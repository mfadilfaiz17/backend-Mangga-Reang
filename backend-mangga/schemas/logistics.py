from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.domain_models import LogisticsMilestone


class TrackingCreate(BaseModel):
    status_milestone: LogisticsMilestone
    catatan_qc: str | None = Field(default=None, max_length=1000)


class TrackingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_rfq: int
    status_milestone: LogisticsMilestone
    catatan_qc: str | None
    updated_at: datetime
    updated_by: int
