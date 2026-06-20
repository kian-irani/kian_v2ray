"""kian_v2ray web panel (phase 2).

A FastAPI backend for managing users across one or more nodes. It deliberately
reuses :mod:`core.db` (the same SQLite schema the installer uses) instead of a
second ORM, so the panel and the CLI can never drift apart on the data model.

Modules:
    panel.security  — stdlib JWT (HS256) + PBKDF2 password hashing
    panel.repo      — data access over core.db (users / audit / settings)
    panel.schemas   — Pydantic request/response models
    panel.main      — FastAPI app + routers (auth, users, stats, ws)

Run:  uvicorn panel.main:app --host 0.0.0.0 --port 8443
"""

__version__ = "0.1.0"
