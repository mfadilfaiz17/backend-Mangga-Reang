from datetime import datetime

from pydantic import ConfigDict, Field

from models.domain_models import LogisticsMilestone
from schemas.base import CamelCaseSchema


class TrackingCreate(CamelCaseSchema):
    model_config = ConfigDict(extra="forbid")
    status_milestone: LogisticsMilestone
    catatan_qc: str | None = Field(default=None, max_length=1000)


class TrackingResponse(CamelCaseSchema):
    id: int
    id_rfq: int
    status_milestone: LogisticsMilestone
    catatan_qc: str | None
    updated_at: datetime
    updated_by: int
