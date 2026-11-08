from sqlalchemy import update, select
from sqlalchemy.orm import Session

from models.domain_models import Notification


def list_for_user(
    db: Session, user_id: int, *, offset: int = 0, limit: int = 50
) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset(offset)
            .limit(limit)
        )
    )


def mark_all_read(db: Session, user_id: int) -> int:
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return result.rowcount


def create(db: Session, notification: Notification) -> Notification:
    db.add(notification)
    db.flush()
    return notification
