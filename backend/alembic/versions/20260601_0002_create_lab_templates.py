"""create lab templates

Revision ID: 20260601_0002
Revises: 20260601_0001
Create Date: 2026-06-01 00:02:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260601_0002"
down_revision: str | None = "20260601_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lab_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("containerlab_yaml", sa.Text(), nullable=False),
        sa.Column("default_startup_config", sa.Text(), nullable=True),
        sa.Column("estimated_cpu", sa.Integer(), nullable=False),
        sa.Column("estimated_memory_mb", sa.Integer(), nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lab_templates_slug", "lab_templates", ["slug"], unique=True)
    op.create_index("ix_lab_templates_category", "lab_templates", ["category"])
    op.create_index("ix_lab_templates_difficulty", "lab_templates", ["difficulty"])
    op.create_index("ix_lab_templates_created_by", "lab_templates", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_lab_templates_created_by", table_name="lab_templates")
    op.drop_index("ix_lab_templates_difficulty", table_name="lab_templates")
    op.drop_index("ix_lab_templates_category", table_name="lab_templates")
    op.drop_index("ix_lab_templates_slug", table_name="lab_templates")
    op.drop_table("lab_templates")

