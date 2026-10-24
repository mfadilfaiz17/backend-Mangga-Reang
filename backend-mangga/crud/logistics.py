from sqlalchemy import select
from sqlalchemy.orm import Session

from models.domain_models import LogisticsTracking


def list_for_rfq(db: Session, rfq_id: int) -> list[LogisticsTracking]:
    return list(
        db.scalars(
            select(LogisticsTracking)
            .where(LogisticsTracking.id_rfq == rfq_id)
            .order_by(LogisticsTracking.updated_at.asc(), LogisticsTracking.id.asc())
        )
    )


def create(db: Session, event: LogisticsTracking) -> LogisticsTracking:
    db.add(event)
    db.flush()
    return event
