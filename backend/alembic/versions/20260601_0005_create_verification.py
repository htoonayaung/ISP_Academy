"""create verification

Revision ID: 20260601_0005
Revises: 20260601_0004
Create Date: 2026-06-01 00:05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260601_0005"
down_revision: str | None = "20260601_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "verification_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("target_node", sa.String(length=120), nullable=False),
        sa.Column("command", sa.String(length=500), nullable=False),
        sa.Column("parser_type", sa.String(length=40), nullable=False),
        sa.Column("assertion_type", sa.String(length=60), nullable=False),
        sa.Column("expected_value", sa.Text(), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_rules_is_active", "verification_rules", ["is_active"])
    op.create_index("ix_verification_rules_ticket_id", "verification_rules", ["ticket_id"])

    op.create_table(
        "verification_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_attempt_id"], ["ticket_attempts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_runs_status", "verification_runs", ["status"])
    op.create_index("ix_verification_runs_ticket_attempt_id", "verification_runs", ["ticket_attempt_id"])

    op.create_table(
        "verification_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("actual_output", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["verification_rule_id"], ["verification_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verification_run_id"], ["verification_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_results_status", "verification_results", ["status"])
    op.create_index("ix_verification_results_verification_rule_id", "verification_results", ["verification_rule_id"])
    op.create_index("ix_verification_results_verification_run_id", "verification_results", ["verification_run_id"])


def downgrade() -> None:
    op.drop_index("ix_verification_results_verification_run_id", table_name="verification_results")
    op.drop_index("ix_verification_results_verification_rule_id", table_name="verification_results")
    op.drop_index("ix_verification_results_status", table_name="verification_results")
    op.drop_table("verification_results")
    op.drop_index("ix_verification_runs_ticket_attempt_id", table_name="verification_runs")
    op.drop_index("ix_verification_runs_status", table_name="verification_runs")
    op.drop_table("verification_runs")
    op.drop_index("ix_verification_rules_ticket_id", table_name="verification_rules")
    op.drop_index("ix_verification_rules_is_active", table_name="verification_rules")
    op.drop_table("verification_rules")
