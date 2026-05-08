# PRD — Tenant Balance Tracking MVP

## Overview

Build a lightweight multi-user tenant balance tracking web application for small property management operations.

The application tracks:
- tenants
- recurring rent charges
- late fees and other manual charges
- payments
- balances owed
- tenant attachments
- historical ledger activity

The application is intentionally scoped as an MVP:
- no authentication
- no external payment processing
- no accounting integrations
- no email/SMS notifications
- no property/building hierarchy
- desktop-first UI

The system must maintain a fully auditable ledger where balances are derived from ledger entries rather than stored directly.

---

# Goals

## Primary Goals

1. Track tenant balances accurately
2. Support recurring monthly rent posting
3. Support manual charges and payments
4. Maintain a historical audit trail
5. Support CSV import of tenants
6. Support attachment uploads
7. Provide a simple operator workflow for office staff

---

# Non-Goals

The following are explicitly out of scope for MVP:

- authentication/login
- payment gateway integration
- automated late fee calculation
- online tenant portal
- mobile-first UI
- property/building hierarchy
- accounting software integration
- email/SMS reminders
- PDF/statement generation
- advanced reporting
- scheduled background workers
- cloud deployment requirements

---

# Tech Stack

## Backend
- Python 3.12+
- FastAPI
- SQLAlchemy ORM
- Alembic migrations
- Pydantic

## Frontend
- Jinja2 templates
- HTMX
- Bootstrap 5
- Vanilla JavaScript (minimal)

## Database
- SQLite

## File Storage
- Local filesystem
- `/uploads/`

## Testing
- Pytest

## Packaging
- Docker + docker-compose

---

# Core Product Concepts

## Ledger-Based Accounting

Balances are NEVER directly edited.

Balance is always derived from:

```text
SUM(charges) - SUM(payments)
```

Every financial action creates immutable ledger entries.

Corrections are handled through reversal entries.

---

# Data Model

# Tenant

Represents a tenant household.

## Fields

| Field | Type |
|---|---|
| id | integer |
| full_name | string |
| additional_resident_names | text |
| street_address | string |
| unit | string nullable |
| city | string |
| state | string |
| zip | string |
| bedroom_count | integer |
| bathroom_count | float nullable |
| living_area_sqft | integer nullable |
| default_rent_amount | decimal |
| rent_due_day | integer |
| rent_last_changed_date | date |
| lease_start_date | date |
| move_out_date | date nullable |
| renters_insurance_received_date | date nullable |
| renters_insurance_expiration_date | date nullable |
| payment_payable_to | string nullable |
| payment_contact_name | string nullable |
| payment_address | string nullable |
| payment_city | string nullable |
| payment_zip | string nullable |
| payment_phone | string nullable |
| payment_days | string nullable |
| payment_hours | string nullable |
| status | enum(active, inactive) |
| notes | text nullable |
| created_at | datetime |
| updated_at | datetime |

---

# LedgerEntry

Single source of truth for balances.

## Entry Types

```text
charge
payment
reversal
```

## Charge Categories

```text
rent
late_fee
nsf_fee
other
```

## Fields

| Field | Type |
|---|---|
| id | integer |
| tenant_id | FK |
| entry_type | enum |
| charge_category | enum nullable |
| amount | decimal |
| effective_date | date |
| memo | text nullable |
| payment_method | enum nullable |
| reversed_entry_id | FK nullable |
| created_by_operator | string |
| created_at | datetime |

---

# Attachment

## Fields

| Field | Type |
|---|---|
| id | integer |
| tenant_id | FK |
| original_filename | string |
| stored_filename | string |
| file_path | string |
| uploaded_by_operator | string |
| created_at | datetime |

---

# Supported Payment Methods

```text
check
cash
zelle
ach
venmo
money_order
credit_card
other
```

Display order should prioritize:
1. check
2. cash
3. zelle

---

# Operator Model

There is no authentication.

On first app load:
- user enters/selects operator name
- stored in browser session
- used for audit trail fields

---

# Rent Posting Workflow

## Manual Workflow

System provides:

```text
"Run Monthly Rent Posting"
```

button.

---

# CSV Import

## Supported

Tenant import ONLY.

---

# UI Requirements

# Main Navigation

```text
Dashboard
Tenants
Import CSV
Run Rent Posting
```

---

# Dashboard

## Summary Metrics

| Metric |
|---|
| Total tenants |
| Active tenants |
| Inactive tenants |
| Total outstanding balance |
| Overdue tenant count |

---

# Acceptance Criteria

# Tenant Management

- create tenant
- edit tenant
- archive tenant
- search/filter tenants

---

# Financial Workflows

- add charges
- add payments
- reverse entries
- accurate balance calculation

---

# Suggested Future Enhancements (Post-MVP)

- authentication
- role permissions
- automated late fees
- recurring scheduled jobs
- tenant portal
- accounting integrations
- online payments
