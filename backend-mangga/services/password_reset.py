import hashlib
import secrets
import smtplib
from datetime import timedelta
from email.message import EmailMessage
from urllib.parse import quote

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from core.security import hash_password
from models.domain_models import PasswordResetToken, User, utc_now


GENERIC_RESET_MESSAGE = "Jika email terdaftar, instruksi reset password telah dikirim."


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _smtp_configured() -> bool:
    return all(
        (
            settings.SMTP_HOST,
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM_EMAIL,
        )
    )


def _send_reset_email(email: str, token: str) -> None:
    if not _smtp_configured():
        raise HTTPException(status_code=503, detail="Password reset email is not configured")
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={quote(token)}"
    message = EmailMessage()
    message["Subject"] = "Reset password Juragan Mangga Reang"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message.set_content(
        "Kami menerima permintaan reset password. Buka link berikut dalam "
        f"{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} menit:\n\n{reset_url}\n\n"
        "Jika Anda tidak meminta reset password, abaikan email ini."
    )
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def request_password_reset(db: Session, email: str) -> None:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None:
        return
    if not _smtp_configured():
        raise HTTPException(status_code=503, detail="Password reset email is not configured")
    now = utc_now()
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)
    raw_token = secrets.token_urlsafe(48)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
    )
    try:
        _send_reset_email(user.email, raw_token)
        db.commit()
    except Exception:
        db.rollback()
        raise


def confirm_password_reset(db: Session, token: str, new_password: str) -> None:
    reset_token = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == _hash_token(token),
            PasswordResetToken.used_at.is_(None),
        )
    )
    expires_at = reset_token.expires_at if reset_token is not None else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=utc_now().tzinfo)
    if reset_token is None or expires_at <= utc_now():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    reset_token.user.hashed_password = hash_password(new_password)
    reset_token.used_at = utc_now()
    db.commit()
