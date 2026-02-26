"""Add last_login_at to users

Revision ID: 004_last_login_at
Revises: 003_employee_list_config
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa


revision = "004_last_login_at"
down_revision = "003_employee_list_config"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("users", "last_login_at")
