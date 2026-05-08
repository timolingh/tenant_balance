from datetime import date
from decimal import Decimal
from app.database import Base, engine, SessionLocal
from app.models.entities import Tenant
from app.services.ledger import add_charge, add_payment

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    if db.query(Tenant).count() == 0:
        t1 = Tenant(full_name="Kevin Lyons", additional_resident_names="Sahara Lyons", street_address="258 E. Myrrh St.", city="Compton", state="CA", zip="90220", bedroom_count=4, default_rent_amount=Decimal("2675.00"), rent_due_day=1, status="active")
        t2 = Tenant(full_name="Alicia Chen", street_address="100 Demo Ave", city="Compton", state="CA", zip="90220", bedroom_count=2, default_rent_amount=Decimal("2100.00"), rent_due_day=5, status="active")
        t3 = Tenant(full_name="Moved Out Example", street_address="55 Old St", city="Compton", state="CA", zip="90220", bedroom_count=1, default_rent_amount=Decimal("1500.00"), rent_due_day=1, status="inactive", move_out_date=date(2026,1,31))
        db.add_all([t1, t2, t3]); db.commit()
        add_charge(db, t1.id, "rent", Decimal("2675.00"), date(2026,5,1), "Seed", "May rent", 5, 2026)
        add_payment(db, t1.id, Decimal("1000.00"), date(2026,5,3), "zelle", "Seed", "Partial payment")
        add_charge(db, t2.id, "rent", Decimal("2100.00"), date(2026,5,5), "Seed", "May rent", 5, 2026)
        add_payment(db, t2.id, Decimal("2500.00"), date(2026,5,4), "check", "Seed", "Overpayment example")
        add_charge(db, t3.id, "late_fee", Decimal("75.00"), date(2026,2,1), "Seed", "Manual late fee")
        print("Seeded demo data")
    else:
        print("Database already has tenants; skipping seed")
finally:
    db.close()
