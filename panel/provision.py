"""panel.provision — orphan-safe user provisioning (stdlib only).

Creating a user touches two systems: the real server (Xray client + configs)
and the panel DB. If the DB write fails *after* the server already has the
client, the user becomes an orphan — connectable but invisible to the panel.
This helper performs the DB write and, on failure, runs a compensating
server-side removal so the two stay consistent.

Kept dependency-free (callables injected) so it is unit-testable without
fastapi/pydantic, which the rest of panel.main pulls in.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

_log = logging.getLogger("kian.panel")


def create_user_orphan_safe(
    *,
    db_create: Callable[[], dict],
    server_remove: Optional[Callable[[], object]] = None,
) -> dict:
    """Run *db_create*; if it raises and the server already provisioned the
    client (*server_remove* given), call *server_remove* to roll it back.

    *server_remove* is ``None`` when nothing was created on the server (e.g.
    the CLI was unavailable), so there is nothing to compensate. The original
    exception always propagates — the rollback is best-effort and never masks
    the real failure (a failed rollback is logged, not raised).
    """
    try:
        return db_create()
    except Exception:
        if server_remove is not None:
            try:
                server_remove()
            except Exception:
                _log.exception("rollback: failed to remove orphan user from "
                               "server after DB insert failed")
        raise
