"""Create initial Mangga Reang schema.

Revision ID: 20261106_0001
Revises:
Create Date: 2026-11-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261106_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    role = sa.Enum("ADMIN_GUDANG", "PETANI", "BUYER_B2B", name="role")
    variety = sa.Enum("GEDONG_GINCU", "CENGKIR", "HARUMANIS", name="variety")
    grade = sa.Enum("GRADE_A", "GRADE_B", "GRADE_C", name="grade")
    rfq_status = sa.Enum(
        "PENDING", "APPROVED", "REJECTED", "COMPLETED", name="rfqstatus"
    )
    milestone = sa.Enum(
        "DIPROSES_PETANI", "SORTIR_GUDANG", "IN_TRANSIT", "DELIVERED",
        name="logisticsmilestone",
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("nama_lengkap", sa.String(length=150), nullable=False),
        sa.Column("role", role, nullable=False),
        sa.Column("nama_perusahaan", sa.String(length=200), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "mangga_inventaris",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("id_petani", sa.Integer(), nullable=False),
        sa.Column("varietas", variety, nullable=False),
        sa.Column("grade", grade, nullable=False),
        sa.Column("tonase_tersedia", sa.Numeric(12, 3), nullable=False),
        sa.Column("harga_per_ton", sa.Numeric(14, 2), nullable=False),
        sa.Column("lokasi_kebun", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("tonase_tersedia >= 0", name="ck_inventory_tonase_non_negative"),
        sa.CheckConstraint("harga_per_ton >= 0", name="ck_inventory_harga_non_negative"),
        sa.ForeignKeyConstraint(["id_petani"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_mangga_inventaris_id_petani", "mangga_inventaris", ["id_petani"])
    op.create_index("ix_mangga_inventaris_varietas", "mangga_inventaris", ["varietas"])
    op.create_index("ix_mangga_inventaris_is_active", "mangga_inventaris", ["is_active"])

    op.create_table(
        "rfq_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("id_buyer", sa.Integer(), nullable=False),
        sa.Column("id_mangga", sa.Integer(), nullable=False),
        sa.Column("tonase_diminta", sa.Numeric(12, 3), nullable=False),
        sa.Column("status_nego", rfq_status, nullable=False),
        sa.Column("total_harga", sa.Numeric(14, 2), nullable=False),
        sa.Column("tanggal_pesanan", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("tonase_diminta > 0", name="ck_rfq_tonase_positive"),
        sa.CheckConstraint("total_harga >= 0", name="ck_rfq_total_non_negative"),
        sa.ForeignKeyConstraint(["id_buyer"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["id_mangga"], ["mangga_inventaris.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_rfq_transactions_id_buyer", "rfq_transactions", ["id_buyer"])
    op.create_index("ix_rfq_transactions_id_mangga", "rfq_transactions", ["id_mangga"])
    op.create_index("ix_rfq_transactions_status_nego", "rfq_transactions", ["status_nego"])

    op.create_table(
        "logistik_tracking",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("id_rfq", sa.Integer(), nullable=False),
        sa.Column("status_milestone", milestone, nullable=False),
        sa.Column("catatan_qc", sa.String(length=1000), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["id_rfq"], ["rfq_transactions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_logistik_tracking_id_rfq", "logistik_tracking", ["id_rfq"])


def downgrade() -> None:
    op.drop_index("ix_logistik_tracking_id_rfq", table_name="logistik_tracking")
    op.drop_table("logistik_tracking")
    op.drop_index("ix_rfq_transactions_status_nego", table_name="rfq_transactions")
    op.drop_index("ix_rfq_transactions_id_mangga", table_name="rfq_transactions")
    op.drop_index("ix_rfq_transactions_id_buyer", table_name="rfq_transactions")
    op.drop_table("rfq_transactions")
    op.drop_index("ix_mangga_inventaris_is_active", table_name="mangga_inventaris")
    op.drop_index("ix_mangga_inventaris_varietas", table_name="mangga_inventaris")
    op.drop_index("ix_mangga_inventaris_id_petani", table_name="mangga_inventaris")
    op.drop_table("mangga_inventaris")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    for enum_name in (
        "logisticsmilestone",
        "rfqstatus",
        "grade",
        "variety",
        "role",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
