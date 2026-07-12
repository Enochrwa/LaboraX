"""create student_topic_mastery table

Revision ID: a1c3f6b2d9e4
Revises: 739c748e925d
Create Date: 2026-07-12 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1c3f6b2d9e4"
down_revision: str | None = "739c748e925d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "student_topic_mastery",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("topic", sa.String(length=64), nullable=False),
        sa.Column("mastery_score", sa.Float(), nullable=False),
        sa.Column("attempts_count", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id", "topic", name="uq_student_topic_mastery_student_topic"
        ),
    )
    op.create_index(
        op.f("ix_student_topic_mastery_student_id"),
        "student_topic_mastery",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_student_topic_mastery_topic"),
        "student_topic_mastery",
        ["topic"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_student_topic_mastery_topic"), table_name="student_topic_mastery")
    op.drop_index(
        op.f("ix_student_topic_mastery_student_id"), table_name="student_topic_mastery"
    )
    op.drop_table("student_topic_mastery")
