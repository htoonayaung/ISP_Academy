"""create tickets

Revision ID: 20260601_0004
Revises: 20260601_0003
Create Date: 2026-06-01 00:04:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260601_0004"
down_revision: str | None = "20260601_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lab_template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("student_instructions", sa.Text(), nullable=False),
        sa.Column("hints", sa.Text(), nullable=True),
        sa.Column("hidden_solution", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["lab_template_id"], ["lab_templates.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tickets_created_by", "tickets", ["created_by"])
    op.create_index("ix_tickets_lab_template_id", "tickets", ["lab_template_id"])
    op.create_index("ix_tickets_slug", "tickets", ["slug"], unique=True)
    op.create_index("ix_tickets_status", "tickets", ["status"])

    op.create_table(
        "ticket_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lab_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lab_instance_id"], ["lab_instances.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_attempts_lab_instance_id", "ticket_attempts", ["lab_instance_id"])
    op.create_index("ix_ticket_attempts_status", "ticket_attempts", ["status"])
    op.create_index("ix_ticket_attempts_student_id", "ticket_attempts", ["student_id"])
    op.create_index("ix_ticket_attempts_ticket_id", "ticket_attempts", ["ticket_id"])


def downgrade() -> None:
    op.drop_index("ix_ticket_attempts_ticket_id", table_name="ticket_attempts")
    op.drop_index("ix_ticket_attempts_student_id", table_name="ticket_attempts")
    op.drop_index("ix_ticket_attempts_status", table_name="ticket_attempts")
    op.drop_index("ix_ticket_attempts_lab_instance_id", table_name="ticket_attempts")
    op.drop_table("ticket_attempts")
    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_index("ix_tickets_slug", table_name="tickets")
    op.drop_index("ix_tickets_lab_template_id", table_name="tickets")
    op.drop_index("ix_tickets_created_by", table_name="tickets")
    op.drop_table("tickets")
