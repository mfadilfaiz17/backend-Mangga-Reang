from decimal import Decimal

from pydantic import Field

from models.domain_models import Grade, Variety
from schemas.base import CamelCaseSchema


class InventoryCreate(CamelCaseSchema):
    id_petani: int | None = None
    varietas: Variety
    grade: Grade
    tonase_tersedia: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    harga_per_ton: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    lokasi_kebun: str = Field(min_length=1, max_length=255)


class InventoryUpdate(CamelCaseSchema):
    tonase_tersedia: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=3)
    harga_per_ton: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    is_active: bool | None = None


class InventoryResponse(CamelCaseSchema):
    id: int
    id_petani: int
    varietas: Variety
    grade: Grade
    tonase_tersedia: Decimal
    harga_per_ton: Decimal
    lokasi_kebun: str
    is_active: bool
