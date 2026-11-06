from datetime import datetime
from decimal import Decimal

from pydantic import Field

from models.domain_models import RfqStatus
from schemas.base import CamelCaseSchema


class RfqCreate(CamelCaseSchema):
    id_mangga: int
    tonase_diminta: Decimal = Field(gt=0, max_digits=12, decimal_places=3)


class RfqResponse(CamelCaseSchema):
    id: int
    id_buyer: int
    id_mangga: int
    tonase_diminta: Decimal
    status_nego: RfqStatus
    total_harga: Decimal
    tanggal_pesanan: datetime
