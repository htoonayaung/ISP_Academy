"""create lab instances

Revision ID: 20260601_0003
Revises: 20260601_0002
Create Date: 2026-06-01 00:03:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260601_0003"
down_revision: str | None = "20260601_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lab_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("lab_name", sa.String(length=180), nullable=False),
        sa.Column("lab_directory", sa.String(length=500), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("destroyed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["template_id"], ["lab_templates.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lab_instances_lab_name", "lab_instances", ["lab_name"], unique=True)
    op.create_index("ix_lab_instances_owner_id", "lab_instances", ["owner_id"])
    op.create_index("ix_lab_instances_status", "lab_instances", ["status"])
    op.create_index("ix_lab_instances_template_id", "lab_instances", ["template_id"])

    op.create_table(
        "lab_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lab_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("kind", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=80), nullable=True),
        sa.Column("container_name", sa.String(length=200), nullable=True),
        sa.Column("management_ipv4", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lab_instance_id"], ["lab_instances.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lab_nodes_lab_instance_id", "lab_nodes", ["lab_instance_id"])

    op.create_table(
        "lab_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lab_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lab_instance_id"], ["lab_instances.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lab_events_event_type", "lab_events", ["event_type"])
    op.create_index("ix_lab_events_lab_instance_id", "lab_events", ["lab_instance_id"])


def downgrade() -> None:
    op.drop_index("ix_lab_events_lab_instance_id", table_name="lab_events")
    op.drop_index("ix_lab_events_event_type", table_name="lab_events")
    op.drop_table("lab_events")
    op.drop_index("ix_lab_nodes_lab_instance_id", table_name="lab_nodes")
    op.drop_table("lab_nodes")
    op.drop_index("ix_lab_instances_template_id", table_name="lab_instances")
    op.drop_index("ix_lab_instances_status", table_name="lab_instances")
    op.drop_index("ix_lab_instances_owner_id", table_name="lab_instances")
    op.drop_index("ix_lab_instances_lab_name", table_name="lab_instances")
    op.drop_table("lab_instances")
