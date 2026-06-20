# KIAN V2Ray — Web Panel (phase 2)

A FastAPI backend for managing users across nodes. It reuses the installer's
SQLite schema (`core/`), so the panel and CLI never drift. Crypto is
hand-rolled in `panel/security.py` (PBKDF2 password hashing + HS256 JWT), so
the only third-party deps are the web framework itself.

## Run

```bash
python3 -m pip install -r panel/requirements.txt
export KIAN_DB_PATH=/etc/kian-v2ray/kian.db
export KIAN_ADMIN_USER=admin
export KIAN_ADMIN_PASSWORD='change-me-strong'   # set on first boot only
export KIAN_CORS_ORIGINS='https://panel.example.com'
uvicorn panel.main:app --host 0.0.0.0 --port 8443
```

Open `http://host:8443/docs` for the auto-generated OpenAPI/Swagger UI.

## Design notes

| Concern | Choice | Why |
|---------|--------|-----|
| ORM | none — raw `core.db` (sqlite3) | one schema shared with the installer; no drift |
| Auth | hand-rolled HS256 JWT + PBKDF2 | zero crypto deps; small + auditable |
| Audit | every mutation calls `core.audit.record` | automatic admin trail |
| Security | nosniff/DENY/HSTS/CSP headers, login rate-limit, explicit CORS | hardening by default (2.9) |
| Key rotation | `POST /api/keys/rotate` swaps the JWT secret | invalidate all tokens on demand (2.10) |

> Deviation from the roadmap's "FastAPI + SQLAlchemy": we reuse `core.db`
> instead of a second ORM. This keeps a single source of truth for the schema
> and avoids migration drift between CLI and panel.

## Endpoints

`/auth/login`, `/auth/refresh`, `/auth/password`, `/auth/sessions`,
`/api/users` (GET/POST), `/api/users/{name}` (GET/PATCH/DELETE),
`/api/users/bulk`, `/api/users/auto-disable`, `/api/stats`, `/api/export`,
`/api/keys/rotate`, and the `/ws/stats` WebSocket.

Per-user controls: quota, expiry, **IP limit**, **speed limit**, **HWID**,
enable/disable, plus **auto-disable** (expired/over-quota) and **bulk actions**.
