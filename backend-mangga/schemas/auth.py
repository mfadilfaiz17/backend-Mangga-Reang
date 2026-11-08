from pydantic import EmailStr, Field

from models.domain_models import Role
from schemas.base import CamelCaseSchema


class UserCreate(CamelCaseSchema):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    nama_lengkap: str = Field(min_length=1, max_length=150)
    role: Role
    nama_perusahaan: str | None = Field(default=None, max_length=200)


class UserResponse(CamelCaseSchema):
    id: int
    email: EmailStr
    nama_lengkap: str
    role: Role
    nama_perusahaan: str | None


class UserUpdate(CamelCaseSchema):
    nama_lengkap: str = Field(min_length=1, max_length=150)
    nama_perusahaan: str | None = Field(default=None, max_length=200)


class PasswordChange(CamelCaseSchema):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)


class LoginRequest(CamelCaseSchema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(CamelCaseSchema):
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(CamelCaseSchema):
    email: EmailStr


class PasswordResetConfirm(CamelCaseSchema):
    token: str = Field(min_length=32, max_length=256)
    new_password: str = Field(min_length=8, max_length=72)


class PasswordResetRequestResponse(CamelCaseSchema):
    detail: str
