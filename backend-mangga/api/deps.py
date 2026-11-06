import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.security import decode_access_token
from crud.users import get_by_id
from db.session import get_db
from models.domain_models import Role, User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
security_logger = logging.getLogger("mangga_reang.security")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["user_id"])
    except (KeyError, TypeError, ValueError):
        security_logger.warning("Invalid access token rejected")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_by_id(db, user_id)
    if user is None:
        security_logger.warning("Access token references missing user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*roles: Role):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            security_logger.warning(
                "Authorization denied for user_id=%s role=%s",
                user.id,
                user.role.value,
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return dependency
