"""Add jd_hash columns and caching indexes

Revision ID: 002_add_jd_hash_cache
Revises: 001_fix_source_id
Create Date: 2026-01-25

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_add_jd_hash_cache"
down_revision = "001_fix_source_id"
branch_labels = None
depends_on = None


def upgrade():
    # jd_analysis: add jd_hash (sha256 hex)
    op.add_column("jd_analysis", sa.Column("jd_hash", sa.String(length=64), nullable=True))
    op.create_index("ix_jd_analysis_jd_hash", "jd_analysis", ["jd_hash"], unique=True)

    # match_results: add jd_hash and unique cache index (jd_hash, resume_id)
    op.add_column("match_results", sa.Column("jd_hash", sa.String(length=64), nullable=True))
    op.create_index("ix_match_results_jd_hash", "match_results", ["jd_hash"], unique=False)
    op.create_index("ux_match_results_jd_hash_resume_id", "match_results", ["jd_hash", "resume_id"], unique=True)


def downgrade():
    op.drop_index("ux_match_results_jd_hash_resume_id", table_name="match_results")
    op.drop_index("ix_match_results_jd_hash", table_name="match_results")
    op.drop_column("match_results", "jd_hash")

    op.drop_index("ix_jd_analysis_jd_hash", table_name="jd_analysis")
    op.drop_column("jd_analysis", "jd_hash")


