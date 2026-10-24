from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.security import create_access_token
from crud.users import get_by_email
from db.session import get_db
from models.domain_models import Role
from schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse
from services.auth import authenticate, register


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    if payload.role is Role.ADMIN_GUDANG:
        raise HTTPException(status_code=403, detail="Admin accounts require controlled provisioning")
    if get_by_email(db, str(payload.email)) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")
    try:
        user = register(db, payload)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered") from exc
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate(db, str(payload.email), payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(user_id=user.id, role=user.role.value))
