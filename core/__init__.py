"""kian_v2ray core — shared, stdlib-only building blocks.

This package holds the reusable logic that the installer CLI, the web panel
(phase 2) and the node agent (phase 5) all build on:

    core.db       — SQLite connection + schema bootstrap
    core.migrate  — lightweight forward-only migration runner
    core.logging  — structured JSON logging
    core.audit    — admin audit-trail writer (who/what/when/from-where)

Everything here depends only on the Python standard library so it stays
importable on a bare VPS with no pip install, and so CI can `py_compile` and
`pytest` it without extra dependencies.
"""

__all__ = ["db", "migrate", "logging", "audit"]
__version__ = "0.1.0"
