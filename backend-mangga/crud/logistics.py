from sqlalchemy import select
from sqlalchemy.orm import Session
from models.domain_models import LogisticsTracking


def list_for_rfq(
    db: Session, rfq_id: int, *, offset: int = 0, limit: int = 50
) -> list[LogisticsTracking]:
    return list(
        db.scalars(
            select(LogisticsTracking)
            .where(LogisticsTracking.id_rfq == rfq_id)
            .order_by(LogisticsTracking.updated_at.asc(), LogisticsTracking.id.asc())
            .offset(offset)
            .limit(limit)
        )
    )


def create(db: Session, event: LogisticsTracking) -> LogisticsTracking:
    db.add(event)
    db.flush()
    return event
