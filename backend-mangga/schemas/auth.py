from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.domain_models import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    nama_lengkap: str = Field(min_length=1, max_length=150)
    role: Role
    nama_perusahaan: str | None = Field(default=None, max_length=200)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nama_lengkap: str
    role: Role
    nama_perusahaan: str | None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
