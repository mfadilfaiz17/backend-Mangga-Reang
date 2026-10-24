from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from models.domain_models import RfqStatus


class RfqCreate(BaseModel):
    id_mangga: int
    tonase_diminta: Decimal = Field(gt=0, max_digits=12, decimal_places=3)


class RfqResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_buyer: int
    id_mangga: int
    tonase_diminta: Decimal
    status_nego: RfqStatus
    total_harga: Decimal
    tanggal_pesanan: datetime
