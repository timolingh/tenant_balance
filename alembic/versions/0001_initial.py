"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('tenants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('additional_resident_names', sa.Text()),
        sa.Column('street_address', sa.String(255), nullable=False),
        sa.Column('unit', sa.String(50)), sa.Column('city', sa.String(120)), sa.Column('state', sa.String(20)), sa.Column('zip', sa.String(20)),
        sa.Column('bedroom_count', sa.Integer()), sa.Column('bathroom_count', sa.Numeric(4,1)), sa.Column('living_area_sqft', sa.Integer()),
        sa.Column('default_rent_amount', sa.Numeric(10,2)), sa.Column('rent_due_day', sa.Integer()), sa.Column('rent_last_changed_date', sa.Date()),
        sa.Column('lease_start_date', sa.Date()), sa.Column('move_out_date', sa.Date()),
        sa.Column('renters_insurance_received_date', sa.Date()), sa.Column('renters_insurance_expiration_date', sa.Date()),
        sa.Column('payment_payable_to', sa.String(255)), sa.Column('payment_contact_name', sa.String(255)), sa.Column('payment_address', sa.String(255)),
        sa.Column('payment_city', sa.String(120)), sa.Column('payment_zip', sa.String(20)), sa.Column('payment_phone', sa.String(50)),
        sa.Column('payment_days', sa.String(120)), sa.Column('payment_hours', sa.String(120)), sa.Column('status', sa.String(20)), sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime()), sa.Column('updated_at', sa.DateTime()),
        sa.UniqueConstraint('full_name','street_address', name='uq_tenant_name_address'))
    op.create_table('ledger_entries',
        sa.Column('id', sa.Integer(), primary_key=True), sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id')),
        sa.Column('entry_type', sa.String(20)), sa.Column('charge_category', sa.String(30)), sa.Column('amount', sa.Numeric(10,2)),
        sa.Column('effective_date', sa.Date()), sa.Column('memo', sa.Text()), sa.Column('payment_method', sa.String(30)),
        sa.Column('reversed_entry_id', sa.Integer(), sa.ForeignKey('ledger_entries.id')), sa.Column('billing_month', sa.Integer()), sa.Column('billing_year', sa.Integer()),
        sa.Column('created_by_operator', sa.String(120)), sa.Column('created_at', sa.DateTime()),
        sa.UniqueConstraint('tenant_id','billing_year','billing_month','charge_category', name='uq_tenant_billing_charge'))
    op.create_table('attachments',
        sa.Column('id', sa.Integer(), primary_key=True), sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id')),
        sa.Column('original_filename', sa.String(255)), sa.Column('stored_filename', sa.String(255)), sa.Column('file_path', sa.String(500)),
        sa.Column('uploaded_by_operator', sa.String(120)), sa.Column('created_at', sa.DateTime()))

def downgrade():
    op.drop_table('attachments')
    op.drop_table('ledger_entries')
    op.drop_table('tenants')
