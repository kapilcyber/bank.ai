"""Add company_employee_list and app_config tables

Revision ID: 003_employee_list_config
Revises: 002_add_jd_hash_cache
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003_employee_list_config"
down_revision = "002_add_jd_hash_cache"
branch_labels = None
depends_on = None


def upgrade():
    # app_config: key-value store for employee list settings
    op.create_table(
        "app_config",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=True),
    )
    op.execute(
        "INSERT INTO app_config (key, value) VALUES "
        "('employee_verification_enabled', 'true'), "
        "('employee_list_source', 'static_file')"
    )

    # company_employee_list: uploaded employee IDs and emails for verification
    op.create_table(
        "company_employee_list",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.String(100), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_company_employee_list_employee_id", "company_employee_list", ["employee_id"], unique=True)
    op.create_index("ix_company_employee_list_email", "company_employee_list", ["email"], unique=False)


def downgrade():
    op.drop_index("ix_company_employee_list_email", table_name="company_employee_list")
    op.drop_index("ix_company_employee_list_employee_id", table_name="company_employee_list")
    op.drop_table("company_employee_list")
    op.drop_table("app_config")
