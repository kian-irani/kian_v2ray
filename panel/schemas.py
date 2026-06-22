"""panel.schemas — Pydantic request/response models for the REST API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str
    totp: Optional[str] = None   # required only if 2FA is enabled


class TotpEnable(BaseModel):
    code: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


_ROUTING = r"^(global|bypass-lan|bypass-iran|bypass-both)$"


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=32,
                      pattern=r"^[A-Za-z0-9._-]+$")
    quota_bytes: int = Field(0, ge=0)
    expires_at: Optional[int] = None
    ip_limit: int = Field(0, ge=0)
    speed_kbps: int = Field(0, ge=0)
    hwid: Optional[str] = None
    routing: Optional[str] = Field(None, pattern=_ROUTING)  # per-user routing (11.2)
    dns: Optional[str] = None                               # per-user DNS (11.2)


class UserUpdate(BaseModel):
    quota_bytes: Optional[int] = Field(None, ge=0)
    used_bytes: Optional[int] = Field(None, ge=0)
    expires_at: Optional[int] = None
    ip_limit: Optional[int] = Field(None, ge=0)
    speed_kbps: Optional[int] = Field(None, ge=0)
    hwid: Optional[str] = None
    enabled: Optional[bool] = None
    routing: Optional[str] = Field(None, pattern=_ROUTING)
    dns: Optional[str] = None


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
    routing: Optional[str] = None
    dns: Optional[str] = None


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


class NodeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)
    address: str
    token: str
    api_port: int = Field(8443, ge=1, le=65535)
    geo: Optional[str] = None


class NodeHeartbeat(BaseModel):
    load: float = 0.0
    bandwidth_gb: float = 0.0
    healthy: bool = True
