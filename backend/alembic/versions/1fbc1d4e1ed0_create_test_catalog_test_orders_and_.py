"""create test_catalog, test_orders, and results tables

Revision ID: 1fbc1d4e1ed0
Revises: 4f931cec4aae
Create Date: 2026-07-11 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "1fbc1d4e1ed0"
down_revision: str | None = "4f931cec4aae"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # `disease_category` already exists (created by the diseases/cases
    # migration) — reuse it rather than creating a duplicate Postgres ENUM
    # type, so `create_type=False` here.
    disease_category_enum = postgresql.ENUM(
        "HEMATOLOGY",
        "CHEMISTRY",
        "MICROBIOLOGY",
        "PARASITOLOGY",
        name="disease_category",
        create_type=False,
    )

    op.create_table(
        "test_catalog",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", disease_category_enum, nullable=False),
        sa.Column("cost_weight", sa.Float(), nullable=False),
        sa.Column(
            "relevance_rules",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_test_catalog_category"), "test_catalog", ["category"], unique=False)
    op.create_index(op.f("ix_test_catalog_code"), "test_catalog", ["code"], unique=True)

    op.create_table(
        "test_orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("test_id", sa.UUID(), nullable=False),
        sa.Column("is_appropriate", sa.Boolean(), nullable=False),
        sa.Column("penalty_applied", sa.Float(), nullable=False),
        sa.Column(
            "ordered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_id"], ["test_catalog.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "test_id", name="uq_test_orders_case_test"),
    )
    op.create_index(op.f("ix_test_orders_case_id"), "test_orders", ["case_id"], unique=False)
    op.create_index(
        op.f("ix_test_orders_student_id"), "test_orders", ["student_id"], unique=False
    )
    op.create_index(op.f("ix_test_orders_test_id"), "test_orders", ["test_id"], unique=False)

    op.create_table(
        "results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("test_id", sa.UUID(), nullable=False),
        sa.Column(
            "result_payload",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_id"], ["test_catalog.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "test_id", name="uq_results_case_test"),
    )
    op.create_index(op.f("ix_results_case_id"), "results", ["case_id"], unique=False)
    op.create_index(op.f("ix_results_test_id"), "results", ["test_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_results_test_id"), table_name="results")
    op.drop_index(op.f("ix_results_case_id"), table_name="results")
    op.drop_table("results")

    op.drop_index(op.f("ix_test_orders_test_id"), table_name="test_orders")
    op.drop_index(op.f("ix_test_orders_student_id"), table_name="test_orders")
    op.drop_index(op.f("ix_test_orders_case_id"), table_name="test_orders")
    op.drop_table("test_orders")

    op.drop_index(op.f("ix_test_catalog_code"), table_name="test_catalog")
    op.drop_index(op.f("ix_test_catalog_category"), table_name="test_catalog")
    op.drop_table("test_catalog")

    # `disease_category` itself is owned by the diseases/cases migration and
    # is left in place — only tables introduced here are dropped.
