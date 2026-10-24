from sqlalchemy import select
from sqlalchemy.orm import Session

from models.domain_models import User


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    return user
