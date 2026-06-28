"""Tests for the panel's dependency-free layers (security + repo).

panel.schemas/panel.main need fastapi+pydantic (not installed in plain CI),
so we only import panel.security and panel.repo here — both stdlib-only.
"""

from __future__ import annotations

import os

from core import db, migrate
from panel import provision, repo, security


def _tmp_db(tmp_path) -> str:
    return os.path.join(str(tmp_path), "panel.db")


# ---------- security: password hashing ----------

def test_password_hash_roundtrip():
    h = security.hash_password("s3cret-pass", iterations=10_000)
    assert h.startswith("pbkdf2_sha256$")
    assert security.verify_password("s3cret-pass", h)
    assert not security.verify_password("wrong", h)


def test_password_hash_is_salted():
    a = security.hash_password("same", iterations=10_000)
    b = security.hash_password("same", iterations=10_000)
    assert a != b  # random salt


# ---------- security: JWT ----------

def test_jwt_roundtrip_and_claims():
    tok = security.create_token("secret", "admin", ttl_seconds=100, now=1000)
    payload = security.decode_token("secret", tok, now=1050)
    assert payload["sub"] == "admin"
    assert payload["exp"] == 1100


def test_jwt_rejects_expired():
    tok = security.create_token("secret", "admin", ttl_seconds=10, now=1000)
    try:
        security.decode_token("secret", tok, now=2000)
        raised = False
    except security.InvalidToken:
        raised = True
    assert raised


def test_jwt_rejects_tampered_signature():
    tok = security.create_token("secret", "admin", ttl_seconds=100, now=1000)
    bad = security.create_token("OTHER", "admin", ttl_seconds=100, now=1000)
    # swap signature from a token signed with a different secret
    forged = ".".join(tok.split(".")[:2] + [bad.split(".")[2]])
    try:
        security.decode_token("secret", forged, now=1050)
        raised = False
    except security.InvalidToken:
        raised = True
    assert raised


# ---------- security: TOTP 2FA ----------

def test_totp_accepts_current_code_and_rejects_wrong():
    secret = security.generate_totp_secret()
    code = security.totp_at(secret, for_time=1_000_000)
    assert security.verify_totp(secret, code, for_time=1_000_000)
    # within the +/- window (30s drift) still accepted
    assert security.verify_totp(secret, code, for_time=1_000_000 + 29)
    # a clearly wrong code is rejected
    assert not security.verify_totp(secret, "000000", for_time=1_000_000) or code == "000000"


# ---------- security: IP allowlist (BUG-6) ----------

def test_ip_allowlist_parse_and_gate():
    empty = security.parse_ip_allowlist("")
    assert empty == frozenset()
    # empty allowlist => no restriction (open), matching current /metrics default
    assert security.ip_allowed("1.2.3.4", empty)
    assert security.ip_allowed(None, empty)

    allow = security.parse_ip_allowlist(" 10.0.0.1, 10.0.0.2 ,, ")
    assert allow == frozenset({"10.0.0.1", "10.0.0.2"})
    assert security.ip_allowed("10.0.0.1", allow)
    assert not security.ip_allowed("10.0.0.9", allow)
    assert not security.ip_allowed(None, allow)  # unknown client is rejected


# ---------- repo ----------

def test_repo_user_lifecycle(tmp_path):
    path = _tmp_db(tmp_path)
    migrate.migrate_path(path)
    with db.session(path) as conn:
        u = repo.create_user(conn, actor="root", name="ali",
                             quota_bytes=100, ip_limit=2,
                             routing="bypass-iran", dns="1.1.1.1")
        assert u["name"] == "ali" and u["uuid"]
        assert repo.get_user(conn, "ali")["ip_limit"] == 2
        # per-user routing/DNS persist (11.2)
        assert u["routing"] == "bypass-iran" and u["dns"] == "1.1.1.1"
        repo.update_user(conn, actor="root", name="ali", speed_kbps=500,
                         routing="global")
        assert repo.get_user(conn, "ali")["speed_kbps"] == 500
        assert repo.get_user(conn, "ali")["routing"] == "global"
        assert repo.stats(conn)["total_users"] == 1
        assert repo.delete_user(conn, actor="root", name="ali")
        assert repo.get_user(conn, "ali") is None


def test_repo_bulk_and_auto_disable(tmp_path):
    path = _tmp_db(tmp_path)
    migrate.migrate_path(path)
    with db.session(path) as conn:
        for n in ("a", "b", "c"):
            repo.create_user(conn, actor="root", name=n)
        # b is over quota, c is expired
        repo.update_user(conn, actor="root", name="b",
                         quota_bytes=10, used_bytes=20)
        repo.update_user(conn, actor="root", name="c", expires_at=1)
        disabled = repo.auto_disable_expired(conn, now=1000)
        assert disabled == 2
        affected = repo.bulk_action(conn, actor="root", action="disable",
                                    names=["a"])
        assert affected == 1
        assert repo.get_user(conn, "a")["enabled"] == 0


# ---------- provision: orphan-safe user creation (BUG-3) ----------

def test_provision_returns_db_result_on_success():
    calls = {"removed": False}
    out = provision.create_user_orphan_safe(
        db_create=lambda: {"name": "ok"},
        server_remove=lambda: calls.__setitem__("removed", True))
    assert out == {"name": "ok"}
    assert calls["removed"] is False  # no rollback on success


def test_provision_rolls_back_server_when_db_insert_fails():
    # BUG-3 regression: server already has the client but the DB write blows up
    # (e.g. UNIQUE race / disk error) -> the orphan must be removed from the
    # server, and the original error must still propagate.
    calls = {"removed": False}

    def boom():
        raise RuntimeError("UNIQUE constraint failed")

    try:
        provision.create_user_orphan_safe(
            db_create=boom,
            server_remove=lambda: calls.__setitem__("removed", True))
        raised = False
    except RuntimeError:
        raised = True
    assert raised
    assert calls["removed"] is True  # compensating removal ran


def test_provision_no_rollback_when_nothing_provisioned():
    # CLI unavailable -> server_remove is None -> nothing to roll back.
    def boom():
        raise RuntimeError("db down")

    try:
        provision.create_user_orphan_safe(db_create=boom, server_remove=None)
        raised = False
    except RuntimeError:
        raised = True
    assert raised


def test_provision_failed_rollback_does_not_mask_original_error():
    # A rollback that itself fails must be swallowed (logged) so the real DB
    # error still surfaces to the caller.
    def boom():
        raise ValueError("real failure")

    def bad_remove():
        raise RuntimeError("server unreachable")

    try:
        provision.create_user_orphan_safe(db_create=boom, server_remove=bad_remove)
        err = None
    except Exception as e:  # noqa: BLE001
        err = e
    assert isinstance(err, ValueError) and str(err) == "real failure"
