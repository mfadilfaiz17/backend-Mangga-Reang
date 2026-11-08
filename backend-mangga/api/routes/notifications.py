from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user
from crud import notifications
from db.session import get_db
from models.domain_models import User
from schemas.notifications import NotificationResponse, NotificationsReadResponse


router = APIRouter()


@router.get("/me", response_model=list[NotificationResponse])
def get_my_notifications(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[NotificationResponse]:
    return notifications.list_for_user(db, user.id, offset=offset, limit=limit)


@router.patch("/me/read-all", response_model=NotificationsReadResponse)
def mark_my_notifications_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationsReadResponse:
    return NotificationsReadResponse(updated_count=notifications.mark_all_read(db, user.id))
