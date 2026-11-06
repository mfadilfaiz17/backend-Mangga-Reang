"""Add domain invariant constraints.

Revision ID: 20261106_0002
Revises: 20261106_0001
Create Date: 2026-11-06
"""
from typing import Sequence, Union

from alembic import op


revision: str = "20261106_0002"
down_revision: Union[str, Sequence[str], None] = "20261106_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    constraints = (
        (
            "mangga_inventaris",
            "ck_inventory_tonase_non_negative",
            "tonase_tersedia >= 0",
        ),
        (
            "mangga_inventaris",
            "ck_inventory_harga_non_negative",
            "harga_per_ton >= 0",
        ),
        ("rfq_transactions", "ck_rfq_tonase_positive", "tonase_diminta > 0"),
        ("rfq_transactions", "ck_rfq_total_non_negative", "total_harga >= 0"),
    )
    for table_name, constraint_name, expression in constraints:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = '{constraint_name}'
                ) THEN
                    ALTER TABLE {table_name}
                    ADD CONSTRAINT {constraint_name} CHECK ({expression});
                END IF;
            END $$;
            """
        )


def downgrade() -> None:
    for table_name, constraint_name in (
        ("rfq_transactions", "ck_rfq_total_non_negative"),
        ("rfq_transactions", "ck_rfq_tonase_positive"),
        ("mangga_inventaris", "ck_inventory_harga_non_negative"),
        ("mangga_inventaris", "ck_inventory_tonase_non_negative"),
    ):
        op.execute(
            f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}"
        )
