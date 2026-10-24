from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_current_user, require_roles
from crud import logistics, rfq
from db.session import get_db
from models.domain_models import LogisticsTracking, Role, User
from schemas.logistics import TrackingCreate, TrackingResponse


router = APIRouter()


@router.get("/{rfq_id}", response_model=list[TrackingResponse])
def get_timeline(
    rfq_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TrackingResponse]:
    order = rfq.get(db, rfq_id)
    if order is None:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if user.role is not Role.ADMIN_GUDANG and order.id_buyer != user.id:
        raise HTTPException(status_code=403, detail="Cannot view this tracking timeline")
    return logistics.list_for_rfq(db, rfq_id)


@router.post("/{rfq_id}/update-status", response_model=TrackingResponse, status_code=201)
def update_status(
    rfq_id: int,
    payload: TrackingCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(Role.ADMIN_GUDANG)),
) -> TrackingResponse:
    if rfq.get(db, rfq_id) is None:
        raise HTTPException(status_code=404, detail="RFQ not found")
    event = logistics.create(
        db,
        LogisticsTracking(
            id_rfq=rfq_id,
            status_milestone=payload.status_milestone,
            catatan_qc=payload.catatan_qc,
            updated_by=admin.id,
        ),
    )
    db.commit()
    db.refresh(event)
    return event
