from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=200)


class AuthUserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=120)
    is_active: bool = True
    is_admin: bool = False


class AuthUserResponse(BaseModel):
    username: str
    display_name: str | None = None
    is_active: bool
    is_admin: bool
    last_login_at: datetime | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: AuthUserResponse
