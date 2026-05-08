from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
import shutil
from fastapi import FastAPI, Depends, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models.entities import Tenant, LedgerEntry, Attachment, ChargeCategory, PaymentMethod
from app.services.ledger import tenant_balance, unpaid_charges_total, add_charge, add_payment, reverse_entry, post_monthly_rent
from app.services.importer import import_tenants_csv

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tenant Balance MVP")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
UPLOAD_ROOT = Path("app/uploads")
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}


def get_operator(request: Request) -> str:
    return request.cookies.get("operator_name", "Unknown")


def decorate_tenant(db: Session, tenant: Tenant):
    tenant.current_balance = tenant_balance(db, tenant.id)
    tenant.unpaid_charges = unpaid_charges_total(db, tenant.id)
    return tenant

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    if request.cookies.get("operator_name"):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse("operator.html", {"request": request})

@app.post("/operator")
def set_operator(operator_name: str = Form(...)):
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie("operator_name", operator_name.strip() or "Unknown", httponly=False)
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    tenants = db.query(Tenant).all()
    for t in tenants:
        decorate_tenant(db, t)
    recent = db.query(LedgerEntry).order_by(LedgerEntry.created_at.desc()).limit(10).all()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "operator": get_operator(request),
        "tenants": tenants,
        "active_count": sum(1 for t in tenants if t.status == "active"),
        "inactive_count": sum(1 for t in tenants if t.status == "inactive"),
        "total_balance": sum((t.current_balance for t in tenants), Decimal("0.00")),
        "overdue_count": sum(1 for t in tenants if t.current_balance > 0),
        "recent": recent,
    })

@app.get("/tenants", response_class=HTMLResponse)
def tenants(request: Request, q: str = "", status: str = "", positive_balance: str = "", db: Session = Depends(get_db)):
    query = db.query(Tenant)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Tenant.full_name.ilike(like), Tenant.street_address.ilike(like)))
    if status in {"active", "inactive"}:
        query = query.filter(Tenant.status == status)
    rows = query.order_by(Tenant.full_name).all()
    rows = [decorate_tenant(db, t) for t in rows]
    if positive_balance:
        rows = [t for t in rows if t.current_balance > 0]
    return templates.TemplateResponse("tenants.html", {"request": request, "tenants": rows, "q": q, "status": status, "positive_balance": positive_balance})

@app.get("/tenants/new", response_class=HTMLResponse)
def new_tenant(request: Request):
    return templates.TemplateResponse("tenant_form.html", {"request": request, "tenant": None})

@app.post("/tenants")
def create_tenant(
    full_name: str = Form(...), street_address: str = Form(...), unit: str = Form(""), city: str = Form(""), state: str = Form("CA"), zip: str = Form(""),
    bedroom_count: int = Form(0), bathroom_count: float = Form(0), living_area_sqft: int = Form(0), default_rent_amount: Decimal = Form(...), rent_due_day: int = Form(1),
    status: str = Form("active"), db: Session = Depends(get_db)
):
    tenant = Tenant(full_name=full_name, street_address=street_address, unit=unit, city=city, state=state, zip=zip, bedroom_count=bedroom_count,
                    bathroom_count=bathroom_count, living_area_sqft=living_area_sqft, default_rent_amount=default_rent_amount, rent_due_day=rent_due_day, status=status)
    db.add(tenant)
    db.commit()
    return RedirectResponse(f"/tenants/{tenant.id}", status_code=303)

@app.get("/tenants/{tenant_id}", response_class=HTMLResponse)
def tenant_detail(request: Request, tenant_id: int, db: Session = Depends(get_db)):
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(404)
    decorate_tenant(db, tenant)
    ledger = db.query(LedgerEntry).filter(LedgerEntry.tenant_id == tenant_id).order_by(LedgerEntry.effective_date.desc(), LedgerEntry.id.desc()).all()
    payments = [e for e in ledger if e.entry_type == "payment"]
    return templates.TemplateResponse("tenant_detail.html", {
        "request": request, "tenant": tenant, "ledger": ledger, "payments": payments, "attachments": tenant.attachments,
        "categories": [c.value for c in ChargeCategory], "methods": [m.value for m in PaymentMethod], "operator": get_operator(request)
    })

@app.post("/tenants/{tenant_id}/charges")
def route_add_charge(request: Request, tenant_id: int, category: str = Form(...), amount: Decimal = Form(...), effective_date: date = Form(...), memo: str = Form(""), db: Session = Depends(get_db)):
    add_charge(db, tenant_id, category, amount, effective_date, get_operator(request), memo)
    return RedirectResponse(f"/tenants/{tenant_id}", status_code=303)

@app.post("/tenants/{tenant_id}/payments")
def route_add_payment(request: Request, tenant_id: int, amount: Decimal = Form(...), effective_date: date = Form(...), method: str = Form(...), memo: str = Form(""), db: Session = Depends(get_db)):
    add_payment(db, tenant_id, amount, effective_date, method, get_operator(request), memo)
    return RedirectResponse(f"/tenants/{tenant_id}", status_code=303)

@app.post("/ledger/{entry_id}/reverse")
def route_reverse(request: Request, entry_id: int, db: Session = Depends(get_db)):
    try:
        rev = reverse_entry(db, entry_id, get_operator(request))
        tenant_id = rev.tenant_id
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return RedirectResponse(f"/tenants/{tenant_id}", status_code=303)

@app.get("/import", response_class=HTMLResponse)
def import_page(request: Request):
    return templates.TemplateResponse("import.html", {"request": request})

@app.post("/tenants/import", response_class=HTMLResponse)
async def import_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = (await file.read()).decode("utf-8-sig")
    result = import_tenants_csv(db, content)
    return templates.TemplateResponse("import.html", {"request": request, "result": result})

@app.post("/rent/post-monthly", response_class=HTMLResponse)
def post_rent(request: Request, db: Session = Depends(get_db)):
    result = post_monthly_rent(db, get_operator(request))
    return templates.TemplateResponse("rent_post_result.html", {"request": request, "result": result})

@app.post("/tenants/{tenant_id}/attachments")
async def upload_attachment(request: Request, tenant_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unsupported file type")
    dest_dir = UPLOAD_ROOT / str(tenant_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid4().hex}{ext}"
    dest = dest_dir / stored
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    att = Attachment(tenant_id=tenant_id, original_filename=file.filename or stored, stored_filename=stored, file_path=str(dest), uploaded_by_operator=get_operator(request))
    db.add(att)
    db.commit()
    return RedirectResponse(f"/tenants/{tenant_id}", status_code=303)

@app.get("/attachments/{attachment_id}")
def download_attachment(attachment_id: int, db: Session = Depends(get_db)):
    att = db.get(Attachment, attachment_id)
    if not att:
        raise HTTPException(404)
    return FileResponse(att.file_path, filename=att.original_filename)
