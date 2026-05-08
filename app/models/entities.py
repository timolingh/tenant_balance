from datetime import datetime, date
from enum import Enum
from sqlalchemy import String, Text, DateTime, Date, Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class TenantStatus(str, Enum):
    active = "active"
    inactive = "inactive"

class EntryType(str, Enum):
    charge = "charge"
    payment = "payment"
    reversal = "reversal"

class ChargeCategory(str, Enum):
    rent = "rent"
    late_fee = "late_fee"
    nsf_fee = "nsf_fee"
    other = "other"

class PaymentMethod(str, Enum):
    check = "check"
    cash = "cash"
    zelle = "zelle"
    ach = "ach"
    venmo = "venmo"
    money_order = "money_order"
    credit_card = "credit_card"
    other = "other"

class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (UniqueConstraint("full_name", "street_address", name="uq_tenant_name_address"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    additional_resident_names: Mapped[str | None] = mapped_column(Text, nullable=True)
    street_address: Mapped[str] = mapped_column(String(255), index=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str] = mapped_column(String(120), default="")
    state: Mapped[str] = mapped_column(String(20), default="CA")
    zip: Mapped[str] = mapped_column(String(20), default="")
    bedroom_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathroom_count: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    living_area_sqft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_rent_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    rent_due_day: Mapped[int] = mapped_column(Integer, default=1)
    rent_last_changed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    lease_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    move_out_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    renters_insurance_received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    renters_insurance_expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_payable_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payment_zip: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payment_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_days: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payment_hours: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=TenantStatus.active.value)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (UniqueConstraint("tenant_id", "billing_year", "billing_month", "charge_category", name="uq_tenant_billing_charge"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    entry_type: Mapped[str] = mapped_column(String(20), index=True)
    charge_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    effective_date: Mapped[date] = mapped_column(Date)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reversed_entry_id: Mapped[int | None] = mapped_column(ForeignKey("ledger_entries.id"), nullable=True)
    billing_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    billing_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by_operator: Mapped[str] = mapped_column(String(120), default="Unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tenant: Mapped[Tenant] = relationship(back_populates="ledger_entries")
    reversed_entry: Mapped["LedgerEntry"] = relationship(remote_side=[id])

class Attachment(Base):
    __tablename__ = "attachments"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    uploaded_by_operator: Mapped[str] = mapped_column(String(120), default="Unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tenant: Mapped[Tenant] = relationship(back_populates="attachments")
