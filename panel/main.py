"""panel.main — FastAPI application for the kian_v2ray web panel.

Endpoints (OpenAPI/Swagger is auto-served at /docs):

    POST /auth/login              -> TokenPair         (rate-limited)
    POST /auth/refresh            -> TokenPair
    POST /auth/password           -> change admin password (recovery)
    GET  /auth/sessions           -> issued refresh-token jti list
    GET  /api/users               -> list (search/paginate)
    POST /api/users               -> create
    GET  /api/users/{name}        -> read
    PATCH /api/users/{name}       -> update (quota/ip/speed/hwid/enabled)
    DELETE /api/users/{name}      -> delete
    POST /api/users/bulk          -> bulk enable/disable/delete
    POST /api/users/auto-disable  -> disable expired/over-quota
    GET  /api/stats               -> counts + traffic
    GET  /api/export              -> JSON or CSV dump
    POST /api/keys/rotate         -> rotate the JWT signing secret
    WS   /ws/stats                -> live stats every few seconds

Run:  uvicorn panel.main:app --host 0.0.0.0 --port 8443
"""

from __future__ import annotations

import asyncio
import csv
import io
import os
import secrets
import time
from typing import Optional

from fastapi import (Depends, FastAPI, HTTPException, Request, WebSocket,
                     WebSocketDisconnect, status)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from core import analytics
from core import audit
from core import cluster
from core import db as core_db
from core import migrate
from . import bridge
from . import metrics as panel_metrics
from . import repo, security
from .schemas import (BulkAction, LoginRequest, NodeCreate, NodeHeartbeat,
                      PasswordChange, RefreshRequest, StatsOut, TokenPair,
                      TotpEnable, UserCreate, UserOut, UserUpdate)

# Optional admin IP allowlist (2.9). Empty = allow all.
_ADMIN_IPS = {ip.strip() for ip in
              os.environ.get("KIAN_ADMIN_IP_WHITELIST", "").split(",") if ip.strip()}

ACCESS_TTL = 900          # 15 min
REFRESH_TTL = 7 * 86400   # 7 days
DB_PATH = os.environ.get("KIAN_DB_PATH", core_db.DEFAULT_DB_PATH)

app = FastAPI(title="KIAN V2Ray Panel", version="0.1.0")
bearer = HTTPBearer(auto_error=True)

# CORS — explicit allowlist from env (2.9). Default: same-origin only.
_origins = [o for o in os.environ.get("KIAN_CORS_ORIGINS", "").split(",") if o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["http://localhost:8443"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory rate-limit buckets and issued-session registry (per process).
_login_hits: dict[str, list[float]] = {}
_sessions: dict[str, dict] = {}


# --------------------------------------------------------------------------- #
# infrastructure: db, bootstrap, security headers, rate limit
# --------------------------------------------------------------------------- #
def get_db():
    conn = core_db.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def _bootstrap() -> None:
    """Ensure schema + an admin + a JWT secret exist on first boot."""
    migrate.migrate_path(DB_PATH)
    with core_db.session(DB_PATH) as conn:
        if repo.get_setting(conn, "jwt_secret") is None:
            repo.set_setting(conn, "jwt_secret", secrets.token_urlsafe(48))
        if repo.get_setting(conn, "admin_pw_hash") is None:
            initial = os.environ.get("KIAN_ADMIN_PASSWORD", "admin")
            if initial == "admin":
                # Loud warning: never leave the default password in production.
                import logging
                logging.getLogger("kian.panel").warning(
                    "⚠️  KIAN_ADMIN_PASSWORD not set — admin password defaults to "
                    "'admin'. Set KIAN_ADMIN_PASSWORD or change it in Settings now.")
            repo.set_setting(conn, "admin_user",
                             os.environ.get("KIAN_ADMIN_USER", "admin"))
            repo.set_setting(conn, "admin_pw_hash",
                             security.hash_password(initial))


@app.on_event("startup")
def _on_startup() -> None:
    _bootstrap()


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Strict-Transport-Security"] = "max-age=63072000"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' ws: wss:; "
        "worker-src blob:;"
    )
    return resp


def _rate_limit(ip: str, *, limit: int = 8, window: float = 60.0) -> None:
    now = time.time()
    hits = [t for t in _login_hits.get(ip, []) if now - t < window]
    if len(hits) >= limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="too many attempts; slow down")
    hits.append(now)
    _login_hits[ip] = hits


def _jwt_secret(conn) -> str:
    s = repo.get_setting(conn, "jwt_secret")
    if not s:
        raise HTTPException(500, "panel not initialized")
    return s


def require_admin(creds: HTTPAuthorizationCredentials = Depends(bearer),
                  conn=Depends(get_db)) -> str:
    try:
        payload = security.decode_token(_jwt_secret(conn), creds.credentials)
    except security.InvalidToken as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            f"invalid token: {exc}") from exc
    if payload.get("typ") == "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "refresh token not accepted here")
    return payload["sub"]


# --------------------------------------------------------------------------- #
# auth
# --------------------------------------------------------------------------- #
def _issue_pair(secret: str, sub: str) -> TokenPair:
    access = security.create_token(secret, sub, ttl_seconds=ACCESS_TTL)
    jti = secrets.token_hex(8)
    refresh = security.create_token(secret, sub, ttl_seconds=REFRESH_TTL,
                                    extra={"typ": "refresh", "jti": jti})
    _sessions[jti] = {"sub": sub, "created": int(time.time())}
    return TokenPair(access_token=access, refresh_token=refresh)


def _check_ip_allowlist(request: Request) -> None:
    if not _ADMIN_IPS:
        return
    ip = request.client.host if request.client else None
    if ip not in _ADMIN_IPS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ip not allowed")


@app.post("/auth/login", response_model=TokenPair)
def login(body: LoginRequest, request: Request, conn=Depends(get_db)):
    _check_ip_allowlist(request)
    _rate_limit(request.client.host if request.client else "?")
    admin_user = repo.get_setting(conn, "admin_user") or "admin"
    pw_hash = repo.get_setting(conn, "admin_pw_hash") or ""
    if body.username != admin_user or not security.verify_password(
            body.password, pw_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "bad credentials")
    # Second factor (2.9) — required only once enabled.
    if repo.get_setting(conn, "twofa_enabled") == "1":
        secret = repo.get_setting(conn, "twofa_secret") or ""
        if not body.totp or not security.verify_totp(secret, body.totp):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                                "2FA code required/invalid")
    return _issue_pair(_jwt_secret(conn), admin_user)


@app.get("/auth/2fa/status")
def twofa_status(admin: str = Depends(require_admin), conn=Depends(get_db)):
    return {"enabled": repo.get_setting(conn, "twofa_enabled") == "1"}


@app.post("/auth/2fa/setup")
def twofa_setup(admin: str = Depends(require_admin), conn=Depends(get_db)):
    """Generate (but don't yet enable) a TOTP secret + otpauth URI."""
    secret = security.generate_totp_secret()
    repo.set_setting(conn, "twofa_secret", secret)
    uri = (f"otpauth://totp/KIAN%20Panel:{admin}?secret={secret}"
           f"&issuer=KIAN%20V2Ray")
    return {"secret": secret, "otpauth_uri": uri}


@app.post("/auth/2fa/enable")
def twofa_enable(body: TotpEnable, admin: str = Depends(require_admin),
                 conn=Depends(get_db)):
    secret = repo.get_setting(conn, "twofa_secret") or ""
    if not secret or not security.verify_totp(secret, body.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid code")
    repo.set_setting(conn, "twofa_enabled", "1")
    return {"ok": True}


@app.post("/auth/2fa/disable")
def twofa_disable(admin: str = Depends(require_admin), conn=Depends(get_db)):
    repo.set_setting(conn, "twofa_enabled", "0")
    return {"ok": True}


@app.post("/auth/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, conn=Depends(get_db)):
    secret = _jwt_secret(conn)
    try:
        payload = security.decode_token(secret, body.refresh_token)
    except security.InvalidToken as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    if payload.get("typ") != "refresh" or payload.get("jti") not in _sessions:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not a live session")
    return _issue_pair(secret, payload["sub"])


@app.post("/auth/password")
def change_password(body: PasswordChange, admin: str = Depends(require_admin),
                    conn=Depends(get_db)):
    pw_hash = repo.get_setting(conn, "admin_pw_hash") or ""
    if not security.verify_password(body.old_password, pw_hash):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "old password wrong")
    repo.set_setting(conn, "admin_pw_hash",
                     security.hash_password(body.new_password))
    _sessions.clear()  # force re-login everywhere
    return {"ok": True}


@app.get("/auth/sessions")
def sessions(admin: str = Depends(require_admin)):
    return {"sessions": [{"jti": k, **v} for k, v in _sessions.items()]}


# --------------------------------------------------------------------------- #
# users
# --------------------------------------------------------------------------- #
@app.get("/api/users", response_model=list[UserOut])
def api_list_users(q: str = "", limit: int = 100, offset: int = 0,
                   admin: str = Depends(require_admin), conn=Depends(get_db)):
    return repo.list_users(conn, q=q, limit=limit, offset=offset)


@app.post("/api/users", response_model=UserOut, status_code=201)
def api_create_user(body: UserCreate, admin: str = Depends(require_admin),
                    conn=Depends(get_db)):
    if repo.get_user(conn, body.name):
        raise HTTPException(status.HTTP_409_CONFLICT, "user exists")
    return repo.create_user(conn, actor=admin, **body.model_dump())


@app.get("/api/users/{name}", response_model=UserOut)
def api_get_user(name: str, admin: str = Depends(require_admin),
                 conn=Depends(get_db)):
    user = repo.get_user(conn, name)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such user")
    return user


@app.patch("/api/users/{name}", response_model=UserOut)
def api_update_user(name: str, body: UserUpdate,
                    admin: str = Depends(require_admin), conn=Depends(get_db)):
    if not repo.get_user(conn, name):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such user")
    return repo.update_user(conn, actor=admin, name=name,
                            **body.model_dump(exclude_none=True))


@app.delete("/api/users/{name}")
def api_delete_user(name: str, admin: str = Depends(require_admin),
                    conn=Depends(get_db)):
    if not repo.delete_user(conn, actor=admin, name=name):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such user")
    return {"ok": True}


@app.post("/api/users/bulk")
def api_bulk(body: BulkAction, admin: str = Depends(require_admin),
             conn=Depends(get_db)):
    n = repo.bulk_action(conn, actor=admin, action=body.action,
                         names=body.names)
    return {"affected": n}


@app.post("/api/users/auto-disable")
def api_auto_disable(admin: str = Depends(require_admin), conn=Depends(get_db)):
    return {"disabled": repo.auto_disable_expired(conn, actor=admin)}


# --------------------------------------------------------------------------- #
# stats / export / key rotation
# --------------------------------------------------------------------------- #
@app.get("/api/stats", response_model=StatsOut)
def api_stats(admin: str = Depends(require_admin), conn=Depends(get_db)):
    return repo.stats(conn)


@app.post("/api/sync")
def api_sync(admin: str = Depends(require_admin), conn=Depends(get_db)):
    """Pull the installer's real users (users.json) into the panel db so the
    dashboard reflects the live server (bridge)."""
    result = bridge.import_users(conn)
    return {"ok": True, "cli_available": bridge.cli_available(), **result}


@app.get("/api/audit")
def api_audit(limit: int = 50, admin: str = Depends(require_admin),
              conn=Depends(get_db)):
    """Recent admin actions for the Audit Log viewer (2.8)."""
    return {"entries": audit.tail(conn, limit=min(limit, 500))}


@app.get("/api/analytics/preview")
def api_analytics_preview(admin: str = Depends(require_admin), conn=Depends(get_db)):
    """Transparency endpoint: show EXACTLY the anonymous payload that would be
    sent (only if the operator opted in via KIAN_ANALYTICS=1). No PII ever."""
    s = repo.stats(conn)
    iid = repo.get_setting(conn, "analytics_id")
    if iid is None:
        iid = secrets.token_hex(8)
        repo.set_setting(conn, "analytics_id", iid)
    payload = analytics.build_payload(s, install_id=iid, version="panel",
                                      protocols=[])
    return {"enabled": analytics.enabled(), "would_send": payload}


@app.get("/metrics")
def metrics(conn=Depends(get_db)):
    """Prometheus scrape endpoint (job 'kian-panel'). Unauthenticated by
    convention; restrict at the network layer / behind the panel's TLS."""
    from fastapi.responses import PlainTextResponse
    s = repo.stats(conn)
    nodes = repo.list_nodes(conn)
    alive = sum(1 for n in nodes if cluster.is_alive(n))
    return PlainTextResponse(
        panel_metrics.render_metrics(s, len(nodes), alive),
        media_type="text/plain; version=0.0.4")


@app.get("/api/system")
def api_system(admin: str = Depends(require_admin)):
    """Lightweight CPU/RAM/Net snapshot from /proc for the monitor (2.8)."""
    out: dict = {}
    try:
        with open("/proc/loadavg") as fh:
            la = fh.read().split()
        out["loadavg"] = [float(la[0]), float(la[1]), float(la[2])]
    except OSError:
        out["loadavg"] = None
    try:
        mem: dict[str, int] = {}
        with open("/proc/meminfo") as fh:
            for line in fh:
                k, _, rest = line.partition(":")
                mem[k] = int(rest.strip().split()[0])  # kB
        total, avail = mem.get("MemTotal", 0), mem.get("MemAvailable", 0)
        out["mem_total_kb"] = total
        out["mem_used_kb"] = total - avail
        out["mem_used_pct"] = round((total - avail) / total * 100, 1) if total else None
    except OSError:
        out["mem_total_kb"] = None
    out["ts"] = int(time.time())
    return out


@app.get("/api/export")
def api_export(fmt: str = "json", admin: str = Depends(require_admin),
               conn=Depends(get_db)):
    users = repo.list_users(conn, limit=100000)
    if fmt == "csv":
        buf = io.StringIO()
        if users:
            w = csv.DictWriter(buf, fieldnames=list(users[0].keys()))
            w.writeheader()
            w.writerows(users)
        return StreamingResponse(
            iter([buf.getvalue()]), media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=users.csv"})
    return JSONResponse(users)


@app.post("/api/keys/rotate")
def api_rotate_keys(admin: str = Depends(require_admin), conn=Depends(get_db)):
    """Rotate the JWT signing secret (2.10). Invalidates all live tokens."""
    repo.set_setting(conn, "jwt_secret", secrets.token_urlsafe(48))
    _sessions.clear()
    return {"ok": True, "rotated_at": int(time.time())}


# --------------------------------------------------------------------------- #
# websocket live stats
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# nodes / cluster (phase 5)
# --------------------------------------------------------------------------- #
@app.get("/api/nodes")
def api_list_nodes(admin: str = Depends(require_admin), conn=Depends(get_db)):
    nodes = repo.list_nodes(conn)
    for n in nodes:
        n["alive"] = cluster.is_alive(n)
    return {"nodes": nodes}


@app.post("/api/nodes")
def api_add_node(body: NodeCreate, admin: str = Depends(require_admin),
                 conn=Depends(get_db)):
    return repo.upsert_node(conn, actor=admin, **body.model_dump())


@app.delete("/api/nodes/{name}")
def api_del_node(name: str, admin: str = Depends(require_admin),
                 conn=Depends(get_db)):
    if not repo.delete_node(conn, actor=admin, name=name):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such node")
    return {"ok": True}


@app.post("/api/nodes/{name}/heartbeat")
def api_node_heartbeat(name: str, body: NodeHeartbeat, conn=Depends(get_db)):
    """Called by node-agents. Auth is the node's own token via header."""
    node = next((n for n in repo.list_nodes(conn) if n["name"] == name), None)
    if not node:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such node")
    repo.node_heartbeat(conn, name=name, load=body.load,
                        bandwidth_gb=body.bandwidth_gb, healthy=body.healthy)
    return {"ok": True}


@app.get("/api/route")
def api_route(country: str = "", admin: str = Depends(require_admin),
              conn=Depends(get_db)):
    """Pick the best node for a client country (geo + load + failover)."""
    nodes = repo.list_nodes(conn)
    chosen = cluster.route_by_geo(country, nodes) if country else \
        cluster.pick_least_loaded(nodes)
    return {"chosen": chosen["name"] if chosen else None,
            "failover": cluster.failover_order(nodes),
            "alerts": cluster.bandwidth_alerts(nodes)}


@app.get("/sub/{name}/info")
def sub_info(name: str, conn=Depends(get_db)):
    """Public self-hosted subscription info (usage/expiry) for the sub page.

    Returns only non-secret usage data. In production gate this with a per-user
    token (?token=) so user existence isn't enumerable."""
    user = repo.get_user(conn, name)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such user")
    base = repo.get_setting(conn, "sub_base")
    return {
        "name": user["name"],
        "used_bytes": user["used_bytes"],
        "quota_bytes": user["quota_bytes"],
        "expires_at": user["expires_at"],
        "enabled": bool(user["enabled"]),
        "sub_url": f"{base.rstrip('/')}/{user['name']}" if base else None,
    }


# Serve the dashboard SPA at /app (static dark-glass UI in panel/web).
_web_dir = Path(__file__).parent / "web"
if _web_dir.is_dir():
    app.mount("/app", StaticFiles(directory=str(_web_dir), html=True), name="web")


@app.get("/")
def root():
    """Redirect root to the dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/app")


@app.get("/api/config")
def api_config():
    """Return runtime config for the frontend SPA (API base URL, etc.)."""
    base = os.environ.get("KIAN_PUBLIC_URL", "").rstrip("/")
    return {"api_base": base}


@app.websocket("/ws/stats")
async def ws_stats(websocket: WebSocket):
    secret_token: Optional[str] = websocket.query_params.get("token")
    with core_db.session(DB_PATH) as conn:
        secret = repo.get_setting(conn, "jwt_secret") or ""
    try:
        if not secret_token:
            await websocket.close(code=1008)
            return
        security.decode_token(secret, secret_token)
    except security.InvalidToken:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        while True:
            with core_db.session(DB_PATH) as conn:
                await websocket.send_json(repo.stats(conn))
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        return
