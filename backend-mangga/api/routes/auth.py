import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.deps import get_current_user
from core.rate_limit import (
    check_login_rate_limit,
    clear_login_failures,
    record_login_failure,
)
from core.security import create_access_token, hash_password, verify_password
from crud.users import get_by_email
from db.session import get_db
from models.domain_models import Role, User
from schemas.auth import (
    LoginRequest,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from services.auth import authenticate, register
from services.password_reset import (
    GENERIC_RESET_MESSAGE,
    confirm_password_reset,
    request_password_reset,
)


router = APIRouter()
security_logger = logging.getLogger("mangga_reang.security")


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
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    rate_limit_key = f"{request.client.host if request.client else 'unknown'}:{payload.email}"
    check_login_rate_limit(rate_limit_key)
    user = authenticate(db, str(payload.email), payload.password)
    if user is None:
        record_login_failure(rate_limit_key)
        security_logger.warning("Login failed for email=%s", str(payload.email).lower())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    clear_login_failures(rate_limit_key)
    return TokenResponse(access_token=create_access_token(user_id=user.id, role=user.role.value))


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return user


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserResponse:
    user.nama_lengkap = payload.nama_lengkap
    user.nama_perusahaan = payload.nama_perusahaan
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=422, detail="New password must be different")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()


@router.post(
    "/password-reset/request",
    response_model=PasswordResetRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def request_password_reset_email(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> PasswordResetRequestResponse:
    request_password_reset(db, str(payload.email))
    return PasswordResetRequestResponse(detail=GENERIC_RESET_MESSAGE)


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),
) -> None:
    confirm_password_reset(db, payload.token, payload.new_password)
