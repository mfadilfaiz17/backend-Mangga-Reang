from sqlalchemy.orm import Session

from core.security import hash_password, verify_password
from crud import users
from models.domain_models import User
from schemas.auth import UserCreate


def register(db: Session, payload: UserCreate) -> User:
    user = User(
        email=str(payload.email).lower(),
        hashed_password=hash_password(payload.password),
        nama_lengkap=payload.nama_lengkap,
        role=payload.role,
        nama_perusahaan=payload.nama_perusahaan,
    )
    return users.create(db, user)


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = users.get_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
