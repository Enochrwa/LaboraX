"""create case_assignments table

Revision ID: b7d4e2f918a3
Revises: a1c3f6b2d9e4
Create Date: 2026-07-12 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7d4e2f918a3"
down_revision: str | None = "a1c3f6b2d9e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "case_assignments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("lecturer_id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("assigned_to_group", sa.String(length=128), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["lecturer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_case_assignments_lecturer_id"), "case_assignments", ["lecturer_id"], unique=False
    )
    op.create_index(
        op.f("ix_case_assignments_case_id"), "case_assignments", ["case_id"], unique=False
    )
    op.create_index(
        op.f("ix_case_assignments_assigned_to_group"),
        "case_assignments",
        ["assigned_to_group"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_case_assignments_assigned_to_group"), table_name="case_assignments"
    )
    op.drop_index(op.f("ix_case_assignments_case_id"), table_name="case_assignments")
    op.drop_index(op.f("ix_case_assignments_lecturer_id"), table_name="case_assignments")
    op.drop_table("case_assignments")
