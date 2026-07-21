from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.auth import AppRole


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_work_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("Enter a valid work email address.")
        local, domain = normalized.split("@")
        if not local or "." not in domain or " " in normalized:
            raise ValueError("Enter a valid work email address.")
        return normalized


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: AppRole
    is_active: bool
    profile: None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
