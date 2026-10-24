from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.session import Base


class Role(str, Enum):
    ADMIN_GUDANG = "ADMIN_GUDANG"
    PETANI = "PETANI"
    BUYER_B2B = "BUYER_B2B"


class Variety(str, Enum):
    GEDONG_GINCU = "GEDONG_GINCU"
    CENGKIR = "CENGKIR"
    HARUMANIS = "HARUMANIS"


class Grade(str, Enum):
    GRADE_A = "GRADE_A"
    GRADE_B = "GRADE_B"
    GRADE_C = "GRADE_C"


class RfqStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class LogisticsMilestone(str, Enum):
    DIPROSES_PETANI = "DIPROSES_PETANI"
    SORTIR_GUDANG = "SORTIR_GUDANG"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    nama_lengkap: Mapped[str] = mapped_column(String(150))
    role: Mapped[Role] = mapped_column(SqlEnum(Role), index=True)
    nama_perusahaan: Mapped[str | None] = mapped_column(String(200), nullable=True)

    inventories: Mapped[list["Inventory"]] = relationship(back_populates="farmer")
    orders: Mapped[list["RfqTransaction"]] = relationship(back_populates="buyer")


class Inventory(Base):
    __tablename__ = "mangga_inventaris"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    id_petani: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    varietas: Mapped[Variety] = mapped_column(SqlEnum(Variety), index=True)
    grade: Mapped[Grade] = mapped_column(SqlEnum(Grade))
    tonase_tersedia: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("0"))
    harga_per_ton: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    lokasi_kebun: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    farmer: Mapped[User] = relationship(back_populates="inventories")
    rfqs: Mapped[list["RfqTransaction"]] = relationship(back_populates="inventory")


Mangga = Inventory


class RfqTransaction(Base):
    __tablename__ = "rfq_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    id_buyer: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    id_mangga: Mapped[int] = mapped_column(
        ForeignKey("mangga_inventaris.id", ondelete="RESTRICT"), index=True
    )
    tonase_diminta: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    status_nego: Mapped[RfqStatus] = mapped_column(
        SqlEnum(RfqStatus), default=RfqStatus.PENDING, index=True
    )
    total_harga: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    tanggal_pesanan: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    buyer: Mapped[User] = relationship(back_populates="orders")
    inventory: Mapped[Inventory] = relationship(back_populates="rfqs")
    tracking: Mapped[list["LogisticsTracking"]] = relationship(back_populates="rfq")


class LogisticsTracking(Base):
    __tablename__ = "logistik_tracking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    id_rfq: Mapped[int] = mapped_column(
        ForeignKey("rfq_transactions.id", ondelete="RESTRICT"), index=True
    )
    status_milestone: Mapped[LogisticsMilestone] = mapped_column(SqlEnum(LogisticsMilestone))
    catatan_qc: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))

    rfq: Mapped[RfqTransaction] = relationship(back_populates="tracking")
