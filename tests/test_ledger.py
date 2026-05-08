from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.entities import Tenant
from app.services.ledger import add_charge, add_payment, tenant_balance, reverse_entry, post_monthly_rent


def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_balance_partial_and_overpayment():
    db = make_db()
    t = Tenant(full_name="Test", street_address="1 Main", city="Compton", state="CA", zip="90220", default_rent_amount=Decimal("1000"), rent_due_day=1, status="active")
    db.add(t); db.commit()
    add_charge(db, t.id, "rent", Decimal("1000"), date(2026,5,1), "Tester")
    add_payment(db, t.id, Decimal("1200"), date(2026,5,2), "check", "Tester")
    assert tenant_balance(db, t.id) == Decimal("-200.00")


def test_reversal():
    db = make_db()
    t = Tenant(full_name="Test", street_address="1 Main", city="Compton", state="CA", zip="90220", default_rent_amount=Decimal("1000"), rent_due_day=1, status="active")
    db.add(t); db.commit()
    e = add_charge(db, t.id, "late_fee", Decimal("50"), date(2026,5,1), "Tester")
    reverse_entry(db, e.id, "Tester")
    assert tenant_balance(db, t.id) == Decimal("0.00")


def test_post_monthly_rent_prevents_duplicates():
    db = make_db()
    t = Tenant(full_name="Test", street_address="1 Main", city="Compton", state="CA", zip="90220", default_rent_amount=Decimal("1000"), rent_due_day=1, status="active")
    db.add(t); db.commit()
    result1 = post_monthly_rent(db, "Tester", date(2026,5,8))
    result2 = post_monthly_rent(db, "Tester", date(2026,5,9))
    assert result1["created_count"] == 1
    assert result2["skipped_count"] == 1
    assert tenant_balance(db, t.id) == Decimal("1000.00")
