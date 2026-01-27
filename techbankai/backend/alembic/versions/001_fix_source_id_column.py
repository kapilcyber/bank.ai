"""Fix source_id column size

Revision ID: 001_fix_source_id
Revises: 
Create Date: 2026-01-22 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_fix_source_id'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Alter source_id column from VARCHAR(100) to VARCHAR(500)
    # This allows longer source IDs (like Outlook message IDs up to 172 chars) to be stored
    op.alter_column('resumes', 'source_id',
                    existing_type=sa.VARCHAR(length=100),
                    type_=sa.String(length=500),
                    existing_nullable=True)


def downgrade():
    # Revert source_id column back to VARCHAR(100)
    # Note: This may fail if there are existing values longer than 100 characters
    op.alter_column('resumes', 'source_id',
                    existing_type=sa.String(length=500),
                    type_=sa.VARCHAR(length=100),
                    existing_nullable=True)

