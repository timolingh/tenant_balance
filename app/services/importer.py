import csv
from datetime import datetime
from decimal import Decimal
from io import StringIO
from sqlalchemy.orm import Session
from app.models.entities import Tenant

REQUIRED_FIELDS = {"full_name", "street_address", "city", "state", "zip", "default_rent_amount"}

def parse_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None

def import_tenants_csv(db: Session, csv_text: str) -> dict:
    reader = csv.DictReader(StringIO(csv_text))
    headers = set(reader.fieldnames or [])
    missing = REQUIRED_FIELDS - headers
    if missing:
        return {"created": 0, "updated": 0, "errors": [f"Missing required columns: {', '.join(sorted(missing))}"]}

    created = updated = 0
    errors: list[str] = []
    for row_num, row in enumerate(reader, start=2):
        try:
            full_name = (row.get("full_name") or "").strip()
            street_address = (row.get("street_address") or "").strip()
            if not full_name or not street_address:
                raise ValueError("full_name and street_address are required")
            tenant = db.query(Tenant).filter(Tenant.full_name == full_name, Tenant.street_address == street_address).first()
            is_new = tenant is None
            tenant = tenant or Tenant(full_name=full_name, street_address=street_address)
            tenant.additional_resident_names = row.get("additional_resident_names") or tenant.additional_resident_names
            tenant.unit = row.get("unit") or tenant.unit
            tenant.city = row.get("city") or tenant.city or ""
            tenant.state = row.get("state") or tenant.state or "CA"
            tenant.zip = row.get("zip") or tenant.zip or ""
            tenant.bedroom_count = int(row["bedroom_count"]) if row.get("bedroom_count") else tenant.bedroom_count
            tenant.bathroom_count = Decimal(row["bathroom_count"]) if row.get("bathroom_count") else tenant.bathroom_count
            tenant.living_area_sqft = int(row["living_area_sqft"]) if row.get("living_area_sqft") else tenant.living_area_sqft
            tenant.default_rent_amount = Decimal(row.get("default_rent_amount") or tenant.default_rent_amount or 0)
            tenant.rent_due_day = int(row.get("rent_due_day") or tenant.rent_due_day or 1)
            tenant.rent_last_changed_date = parse_date(row.get("rent_last_changed_date")) or tenant.rent_last_changed_date
            tenant.lease_start_date = parse_date(row.get("lease_start_date")) or tenant.lease_start_date
            tenant.move_out_date = parse_date(row.get("move_out_date")) or tenant.move_out_date
            tenant.renters_insurance_received_date = parse_date(row.get("renters_insurance_received_date")) or tenant.renters_insurance_received_date
            tenant.renters_insurance_expiration_date = parse_date(row.get("renters_insurance_expiration_date")) or tenant.renters_insurance_expiration_date
            tenant.status = row.get("status") or tenant.status or "active"
            tenant.payment_payable_to = row.get("payment_payable_to") or tenant.payment_payable_to
            tenant.payment_contact_name = row.get("payment_contact_name") or tenant.payment_contact_name
            tenant.payment_address = row.get("payment_address") or tenant.payment_address
            tenant.payment_city = row.get("payment_city") or tenant.payment_city
            tenant.payment_zip = row.get("payment_zip") or tenant.payment_zip
            tenant.payment_phone = row.get("payment_phone") or tenant.payment_phone
            tenant.payment_days = row.get("payment_days") or tenant.payment_days
            tenant.payment_hours = row.get("payment_hours") or tenant.payment_hours
            db.add(tenant)
            if is_new:
                created += 1
            else:
                updated += 1
        except Exception as exc:
            errors.append(f"Row {row_num}: {exc}")
    db.commit()
    return {"created": created, "updated": updated, "errors": errors}
