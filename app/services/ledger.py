from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.entities import LedgerEntry, Tenant, EntryType, ChargeCategory


def tenant_balance(db: Session, tenant_id: int) -> Decimal:
    entries = db.query(LedgerEntry).filter(LedgerEntry.tenant_id == tenant_id).all()
    total = Decimal("0.00")
    for e in entries:
        total += Decimal(str(e.amount))
    return total


def unpaid_charges_total(db: Session, tenant_id: int) -> Decimal:
    # MVP approximation: unpaid charges = max(balance, 0)
    bal = tenant_balance(db, tenant_id)
    return bal if bal > 0 else Decimal("0.00")


def add_charge(db: Session, tenant_id: int, category: str, amount: Decimal, effective_date: date, operator: str, memo: str | None = None, billing_month: int | None = None, billing_year: int | None = None) -> LedgerEntry:
    entry = LedgerEntry(
        tenant_id=tenant_id,
        entry_type=EntryType.charge.value,
        charge_category=category,
        amount=amount,
        effective_date=effective_date,
        memo=memo,
        billing_month=billing_month,
        billing_year=billing_year,
        created_by_operator=operator or "Unknown",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def add_payment(db: Session, tenant_id: int, amount: Decimal, effective_date: date, method: str, operator: str, memo: str | None = None) -> LedgerEntry:
    entry = LedgerEntry(
        tenant_id=tenant_id,
        entry_type=EntryType.payment.value,
        amount=-abs(amount),
        effective_date=effective_date,
        payment_method=method,
        memo=memo,
        created_by_operator=operator or "Unknown",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def reverse_entry(db: Session, entry_id: int, operator: str, memo: str | None = None) -> LedgerEntry:
    original = db.get(LedgerEntry, entry_id)
    if not original:
        raise ValueError("Ledger entry not found")
    existing = db.query(LedgerEntry).filter(LedgerEntry.reversed_entry_id == entry_id).first()
    if existing:
        raise ValueError("Ledger entry has already been reversed")
    reversal = LedgerEntry(
        tenant_id=original.tenant_id,
        entry_type=EntryType.reversal.value,
        charge_category=original.charge_category,
        amount=-Decimal(str(original.amount)),
        effective_date=date.today(),
        memo=memo or f"Reversal of ledger entry #{entry_id}",
        payment_method=original.payment_method,
        reversed_entry_id=entry_id,
        created_by_operator=operator or "Unknown",
    )
    db.add(reversal)
    db.commit()
    db.refresh(reversal)
    return reversal


def post_monthly_rent(db: Session, operator: str, today: date | None = None) -> dict:
    today = today or date.today()
    created = []
    skipped = []
    active_tenants = db.query(Tenant).filter(Tenant.status == "active").all()
    for tenant in active_tenants:
        exists = db.query(LedgerEntry).filter(
            LedgerEntry.tenant_id == tenant.id,
            LedgerEntry.billing_month == today.month,
            LedgerEntry.billing_year == today.year,
            LedgerEntry.charge_category == ChargeCategory.rent.value,
        ).first()
        if exists:
            skipped.append(tenant)
            continue
        entry = add_charge(
            db=db,
            tenant_id=tenant.id,
            category=ChargeCategory.rent.value,
            amount=Decimal(str(tenant.default_rent_amount or 0)),
            effective_date=date(today.year, today.month, min(tenant.rent_due_day or 1, 28)),
            operator=operator,
            memo=f"Monthly rent for {today.year}-{today.month:02d}",
            billing_month=today.month,
            billing_year=today.year,
        )
        created.append(entry)
    return {"created_count": len(created), "skipped_count": len(skipped), "created": created, "skipped": skipped}
