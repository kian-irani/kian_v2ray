"""panel.schemas — Pydantic request/response models for the REST API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=32,
                      pattern=r"^[A-Za-z0-9._-]+$")
    quota_bytes: int = Field(0, ge=0)
    expires_at: Optional[int] = None
    ip_limit: int = Field(0, ge=0)
    speed_kbps: int = Field(0, ge=0)
    hwid: Optional[str] = None


class UserUpdate(BaseModel):
    quota_bytes: Optional[int] = Field(None, ge=0)
    used_bytes: Optional[int] = Field(None, ge=0)
    expires_at: Optional[int] = None
    ip_limit: Optional[int] = Field(None, ge=0)
    speed_kbps: Optional[int] = Field(None, ge=0)
    hwid: Optional[str] = None
    enabled: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    name: str
    uuid: str
    quota_bytes: int
    used_bytes: int
    expires_at: Optional[int]
    ip_limit: int
    speed_kbps: int
    hwid: Optional[str]
    enabled: int
    created_at: int


class BulkAction(BaseModel):
    action: str = Field(..., pattern=r"^(enable|disable|delete)$")
    names: list[str]


class StatsOut(BaseModel):
    total_users: int
    active_users: int
    total_used_bytes: int


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)
