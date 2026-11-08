from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user, require_roles
from crud import logistics, rfq
from db.session import get_db
from models.domain_models import (
    LogisticsMilestone,
    LogisticsTracking,
    Notification,
    RfqStatus,
    Role,
    User,
)
from schemas.logistics import TrackingCreate, TrackingResponse


router = APIRouter()


@router.get("/{rfq_id}", response_model=list[TrackingResponse])
def get_timeline(
    rfq_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TrackingResponse]:
    order = rfq.get(db, rfq_id)
    if order is None:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if user.role is not Role.ADMIN_GUDANG and order.id_buyer != user.id:
        raise HTTPException(status_code=403, detail="Cannot view this tracking timeline")
    return logistics.list_for_rfq(db, rfq_id, offset=offset, limit=limit)


@router.post("/{rfq_id}/update-status", response_model=TrackingResponse, status_code=201)
def update_status(
    rfq_id: int,
    payload: TrackingCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(Role.ADMIN_GUDANG)),
) -> TrackingResponse:
    order = rfq.get(db, rfq_id)
    if order is None:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if order.status_nego is not RfqStatus.APPROVED:
        raise HTTPException(status_code=409, detail="Tracking requires an approved RFQ")
    events = logistics.list_for_rfq(db, rfq_id, offset=0, limit=100)
    expected = (
        LogisticsMilestone.DIPROSES_PETANI
        if not events
        else {
            LogisticsMilestone.DIPROSES_PETANI: LogisticsMilestone.SORTIR_GUDANG,
            LogisticsMilestone.SORTIR_GUDANG: LogisticsMilestone.IN_TRANSIT,
            LogisticsMilestone.IN_TRANSIT: LogisticsMilestone.DELIVERED,
        }.get(events[-1].status_milestone)
    )
    if expected is None or payload.status_milestone is not expected:
        raise HTTPException(status_code=409, detail="Invalid tracking milestone transition")
    event = logistics.create(
        db,
        LogisticsTracking(
            id_rfq=rfq_id,
            status_milestone=payload.status_milestone,
            catatan_qc=payload.catatan_qc,
            updated_by=admin.id,
        ),
    )
    db.add(
        Notification(
            user_id=order.id_buyer,
            notification_type="TRACKING_UPDATED",
            title="Tracking pesanan diperbarui",
            message=f"RFQ #{order.id} masuk milestone {payload.status_milestone.value}.",
        )
    )
    db.commit()
    db.refresh(event)
    return event
