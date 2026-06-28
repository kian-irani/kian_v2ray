# 🔍 bug-found.md — independent scan (Phase 0)

> Fresh independent pass over panel/core/scripts/app/worker with the §2
> checklist, **in addition to** the six items in `bug.md` (all fixed — see the
> `fix(...)` commits on this branch). Result: **no new critical or high-severity
> bug found.** One low-severity hardening note below.

## Scope verified clean (sampled)

- **SQL injection** — the two f-string SQL sites are safe:
  `core/migrate.py` interpolates an internal `int` version into a `PRAGMA`
  (cannot be parameterized), and `panel/repo.update_user` builds its `SET`
  clause only from a hardcoded `allowed` field-name whitelist, with all values
  bound via `?`. No user-controlled identifier reaches SQL.
- **Command injection** — no `shell=True`, `eval`, or `os.system` in
  panel/core/scripts/node-agent; the CLI bridge uses `subprocess.run([...])`.
- **Token comparison** — panel sub/node/heartbeat tokens use
  `secrets.compare_digest` (re-confirmed).
- **DB durability** — `core/db.py` opens SQLite with `isolation_level=None`
  (autocommit), so writes are not left uncommitted.
- **Error handling** — no bare `except` that silently swallows in
  `panel/main.py` (all log or re-raise).
- **Permissions** — after the BUG-4 fix, no remaining world-writable `chmod`
  in `install.sh` / scripts (guarded by `tests/test_install_hardening.py`).

## 🟡 P3 (low) — minor hardening, not a vulnerability

### NF-1 — non-constant-time token match in `scripts/sub-server.py::_user_info`
**File:** `scripts/sub-server.py` line ~38
**Detail:** `email = next((e for e, t in toks.items() if t == token), "")`
uses `==` to find the email for a presented subscription token while building
the optional `Subscription-Userinfo` header.
**Why it's low, not a bug:** this path is only reached *after* `do_GET` has
already accepted the token by checking that `<token>.txt` exists on disk, and
the response itself already differs for valid (200 + body) vs invalid (404)
tokens. So the `==` adds no enumeration capability beyond what the response
status already reveals, and the header build is fail-soft. No data leak.
**Optional fix (if hardening):** reverse-index the dict
(`email = {t: e for e, t in toks.items()}.get(token, "")`) for an O(1) exact
lookup that also drops the per-entry comparison — clarity + micro-perf, not a
security fix.

---

*Independent scan | 2026-06-28 | 0 new critical/high · 1 low note · all `bug.md`
items (BUG-1…6) fixed with regression tests.*
