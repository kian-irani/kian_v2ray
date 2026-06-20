"""core.migrate — forward-only schema migration runner.

Keeps a single integer ``user_version`` PRAGMA on the SQLite database and
applies any migrations from :data:`core.db.MIGRATIONS` whose index is greater
than the stored version. Idempotent: running it twice is a no-op.

Usage (CLI):
    python3 -m core.migrate [/path/to/kian.db]
"""

from __future__ import annotations

import sqlite3
import sys

from . import db as _db


def current_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version;").fetchone()[0])


def migrate(conn: sqlite3.Connection) -> int:
    """Apply all pending migrations. Returns the number applied."""
    version = current_version(conn)
    applied = 0
    for idx, statement in enumerate(_db.MIGRATIONS):
        target = idx + 1  # versions are 1-based
        if target <= version:
            continue
        conn.executescript("BEGIN;\n" + statement + "\nCOMMIT;")
        conn.execute(f"PRAGMA user_version = {target};")
        applied += 1
    return applied


def migrate_path(path: str = _db.DEFAULT_DB_PATH) -> int:
    with _db.session(path) as conn:
        return migrate(conn)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = argv[0] if argv else _db.DEFAULT_DB_PATH
    n = migrate_path(path)
    print(f"kian-migrate: applied {n} migration(s); db={path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
