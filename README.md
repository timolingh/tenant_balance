# Tenant Balance Tracking MVP

A desktop-first FastAPI + Jinja + HTMX application for tracking tenant balances using an immutable ledger model.

## Features

- Multi-operator workflow without authentication
- Tenant creation and listing
- Tenant CSV import with upsert by `full_name + street_address`
- Ledger-based charges, payments, and reversals
- Manual monthly rent posting button
- Duplicate monthly rent charge prevention
- Manual late fee, NSF fee, rent, and other charges
- Partial payments, overpayments, and negative balances
- Tenant attachment uploads stored locally under `app/uploads/`
- Dashboard and tenant detail pages
- SQLite database
- Seed data
- Pytest tests
- Docker support
- Alembic migration scaffold

## API Endpoints

- `GET /` - Root page, redirects to dashboard if operator is set, otherwise shows operator selection
- `POST /operator` - Set the operator name via form
- `GET /dashboard` - Dashboard page with tenant overview and recent ledger entries
- `GET /tenants` - List tenants with optional query parameters for search, status, and balance filters
- `GET /tenants/new` - Form to create a new tenant
- `POST /tenants` - Create a new tenant
- `GET /tenants/{tenant_id}` - View tenant details, ledger, and attachments
- `GET /tenants/{tenant_id}/edit` - Form to edit tenant details
- `POST /tenants/{tenant_id}` - Update tenant details
- `POST /tenants/{tenant_id}/charges` - Add a charge to a tenant's ledger
- `POST /tenants/{tenant_id}/payments` - Add a payment to a tenant's ledger
- `POST /ledger/{entry_id}/reverse` - Reverse a ledger entry
- `GET /import` - Import page for tenant CSV
- `POST /tenants/import` - Import tenants from CSV file
- `POST /rent/post-monthly` - Post monthly rent charges for all active tenants
- `POST /tenants/{tenant_id}/attachments` - Upload an attachment for a tenant
- `GET /attachments/{attachment_id}` - Download an attachment file

## Example Payloads (Add / Update Tenant)

Tenant create and update endpoints expect `application/x-www-form-urlencoded` form data.

Create tenant (`POST /tenants`):

```bash
curl -X POST http://localhost:8000/tenants \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "full_name=Jane Doe" \
  --data-urlencode "street_address=123 Main St" \
  --data-urlencode "unit=4B" \
  --data-urlencode "city=Los Angeles" \
  --data-urlencode "state=CA" \
  --data-urlencode "zip=90001" \
  --data-urlencode "bedroom_count=2" \
  --data-urlencode "bathroom_count=1.5" \
  --data-urlencode "living_area_sqft=950" \
  --data-urlencode "default_rent_amount=2450.00" \
  --data-urlencode "rent_due_day=1" \
  --data-urlencode "status=active"
```

Update tenant (`POST /tenants/{tenant_id}`):

```bash
curl -X POST http://localhost:8000/tenants/1 \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "full_name=Jane Doe" \
  --data-urlencode "additional_resident_names=John Doe" \
  --data-urlencode "street_address=123 Main St" \
  --data-urlencode "unit=4B" \
  --data-urlencode "city=Los Angeles" \
  --data-urlencode "state=CA" \
  --data-urlencode "zip=90001" \
  --data-urlencode "bedroom_count=2" \
  --data-urlencode "bathroom_count=1.5" \
  --data-urlencode "living_area_sqft=950" \
  --data-urlencode "default_rent_amount=2550.00" \
  --data-urlencode "rent_due_day=5" \
  --data-urlencode "payment_payable_to=Acme Properties" \
  --data-urlencode "payment_contact_name=Leasing Office" \
  --data-urlencode "payment_address=500 Property Ln" \
  --data-urlencode "payment_city=Los Angeles" \
  --data-urlencode "payment_zip=90002" \
  --data-urlencode "payment_phone=555-111-2222" \
  --data-urlencode "payment_days=Mon-Fri" \
  --data-urlencode "payment_hours=9am-5pm" \
  --data-urlencode "notes=Updated lease terms" \
  --data-urlencode "status=active"
```

Required fields:

```text
Create: full_name, street_address, default_rent_amount
Update: full_name, street_address, default_rent_amount
```

## Extract Into a Git-Managed Directory

From the directory where you downloaded the tarball:

```bash
tar -xzf tenant_balance_mvp.tar.gz
cd tenant_balance_mvp
git init
git add .
git commit -m "Initial tenant balance MVP"
```

## Local Python Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000
```

## Docker Setup

Use the provided Makefile for easy container management:

```bash
# Build and start the containers
make up

# Stop the containers
make down

# View logs
make logs

# Clean up (stop and remove volumes)
make clean
```

Open:

```text
http://localhost:8000
```

To seed data in Docker:

```bash
docker compose exec web python seed.py
```

## Run Tests

```bash
pytest
```

## CSV Import Columns

Required:

```text
full_name,street_address,city,state,zip,default_rent_amount
```

Optional supported columns include:

```text
additional_resident_names,unit,bedroom_count,bathroom_count,living_area_sqft,rent_due_day,rent_last_changed_date,lease_start_date,move_out_date,renters_insurance_received_date,renters_insurance_expiration_date,status,payment_payable_to,payment_contact_name,payment_address,payment_city,payment_zip,payment_phone,payment_days,payment_hours
```

## Notes

- Balances are derived from ledger entries and are not directly editable.
- Ledger entries are immutable. Corrections are made by reversal entries.
- Authentication is intentionally deferred.
- The UI is desktop-first.
