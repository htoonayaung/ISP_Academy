"""create ai lab builder previews

Revision ID: 20260601_0006
Revises: 20260601_0005
Create Date: 2026-06-01 00:06:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260601_0006"
down_revision: str | None = "20260601_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_lab_builder_previews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("lab_plan_json", sa.JSON(), nullable=False),
        sa.Column("generated_containerlab_yaml", sa.Text(), nullable=False),
        sa.Column("generated_configs", sa.JSON(), nullable=False),
        sa.Column("generated_verification_rules", sa.JSON(), nullable=False),
        sa.Column("validation_status", sa.String(length=20), nullable=False),
        sa.Column("validation_errors", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_lab_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_lab_template_id"], ["lab_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_lab_builder_previews_requested_by", "ai_lab_builder_previews", ["requested_by"])
    op.create_index("ix_ai_lab_builder_previews_status", "ai_lab_builder_previews", ["status"])
    op.create_index(
        "ix_ai_lab_builder_previews_validation_status",
        "ai_lab_builder_previews",
        ["validation_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_lab_builder_previews_validation_status", table_name="ai_lab_builder_previews")
    op.drop_index("ix_ai_lab_builder_previews_status", table_name="ai_lab_builder_previews")
    op.drop_index("ix_ai_lab_builder_previews_requested_by", table_name="ai_lab_builder_previews")
    op.drop_table("ai_lab_builder_previews")
