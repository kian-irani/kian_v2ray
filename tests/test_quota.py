"""Tests for core.quota periodic-reset scheduling + repo.apply_quota_resets (FR-S1)."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from core import db, migrate, quota
from panel import repo


def _ts(y, m, d, hh=0, mm=0):
    return int(datetime(y, m, d, hh, mm, tzinfo=timezone.utc).timestamp())


# ---------- pure scheduling ----------

def test_period_start_none_for_lifetime():
    assert quota.period_start(None) is None
    assert quota.period_start("") is None
    assert quota.period_start("none") is None
    assert quota.period_start("bogus") is None


def test_period_start_daily_weekly_monthly():
    now = _ts(2026, 6, 28, 13, 30)          # Sunday 2026-06-28 13:30 UTC
    assert quota.period_start("daily", now=now) == _ts(2026, 6, 28)
    # ISO week: Monday is the start; 2026-06-28 is a Sunday -> week began 06-22
    assert quota.period_start("weekly", now=now) == _ts(2026, 6, 22)
    assert quota.period_start("monthly", now=now) == _ts(2026, 6, 1)


def test_is_due_transitions():
    now = _ts(2026, 6, 28, 13, 30)
    # never reset -> due
    assert quota.is_due("daily", None, now=now)
    # reset earlier today -> not due
    assert not quota.is_due("daily", _ts(2026, 6, 28, 1, 0), now=now)
    # reset yesterday -> due
    assert quota.is_due("daily", _ts(2026, 6, 27, 23, 0), now=now)
    # monthly: reset last month -> due; reset this month -> not due
    assert quota.is_due("monthly", _ts(2026, 5, 31, 23, 0), now=now)
    assert not quota.is_due("monthly", _ts(2026, 6, 2), now=now)
    # no strategy never due
    assert not quota.is_due("none", None, now=now)


# ---------- repo.apply_quota_resets ----------

def test_apply_quota_resets_zeroes_and_reenables(tmp_path):
    path = os.path.join(str(tmp_path), "kian.db")
    migrate.migrate_path(path)
    now = _ts(2026, 6, 28, 12, 0)
    with db.session(path) as conn:
        # monthly user, over quota, auto-disabled, still valid -> reset+reenable
        repo.create_user(conn, actor="root", name="mon", quota_bytes=100,
                         reset_strategy="monthly")
        repo.update_user(conn, actor="root", name="mon",
                         used_bytes=100, enabled=False)
        # lifetime user (no strategy) -> untouched
        repo.create_user(conn, actor="root", name="life", quota_bytes=100)
        repo.update_user(conn, actor="root", name="life", used_bytes=80)
        # monthly user already reset this month -> untouched
        repo.create_user(conn, actor="root", name="fresh", quota_bytes=100,
                         reset_strategy="monthly")
        repo.update_user(conn, actor="root", name="fresh", used_bytes=40)
        conn.execute("UPDATE users SET last_reset=? WHERE name='fresh'",
                     (_ts(2026, 6, 5),))

        n = repo.apply_quota_resets(conn, actor="root", now=now)
        assert n == 1
        mon = repo.get_user(conn, "mon")
        assert mon["used_bytes"] == 0 and mon["enabled"] == 1
        assert mon["last_reset"] == now
        assert repo.get_user(conn, "life")["used_bytes"] == 80   # untouched
        assert repo.get_user(conn, "fresh")["used_bytes"] == 40  # not due


def test_apply_quota_resets_keeps_expired_disabled(tmp_path):
    path = os.path.join(str(tmp_path), "kian.db")
    migrate.migrate_path(path)
    now = _ts(2026, 6, 28, 12, 0)
    with db.session(path) as conn:
        repo.create_user(conn, actor="root", name="exp", quota_bytes=100,
                         reset_strategy="daily", expires_at=_ts(2026, 6, 1))
        repo.update_user(conn, actor="root", name="exp",
                         used_bytes=100, enabled=False)
        n = repo.apply_quota_resets(conn, actor="root", now=now)
        assert n == 1
        exp = repo.get_user(conn, "exp")
        assert exp["used_bytes"] == 0          # quota still reset
        assert exp["enabled"] == 0             # but stays disabled (expired)


def test_create_user_normalizes_reset_strategy(tmp_path):
    path = os.path.join(str(tmp_path), "kian.db")
    migrate.migrate_path(path)
    with db.session(path) as conn:
        repo.create_user(conn, actor="root", name="a", reset_strategy="weekly")
        assert repo.get_user(conn, "a")["reset_strategy"] == "weekly"
        # invalid / none -> stored as NULL (lifetime cap)
        repo.create_user(conn, actor="root", name="b", reset_strategy="none")
        assert repo.get_user(conn, "b")["reset_strategy"] is None
        repo.create_user(conn, actor="root", name="c", reset_strategy="bogus")
        assert repo.get_user(conn, "c")["reset_strategy"] is None


# ---------- FR-S2 device enforcement ----------

def test_device_enforcement_and_reset(tmp_path):
    path = os.path.join(str(tmp_path), "kian.db")
    migrate.migrate_path(path)
    with db.session(path) as conn:
        repo.create_user(conn, actor="root", name="d", device_limit=2)
        r1 = repo.register_device(conn, name="d", device_id="phoneA")
        r2 = repo.register_device(conn, name="d", device_id="phoneB")
        assert r1["allowed"] and r2["allowed"] and r2["count"] == 2
        # a known device is always allowed and doesn't grow the count
        again = repo.register_device(conn, name="d", device_id="phoneA")
        assert again["allowed"] and again["known"] and again["count"] == 2
        # a third *new* device is over the cap -> denied and not stored
        r3 = repo.register_device(conn, name="d", device_id="tablet")
        assert not r3["allowed"]
        assert len(repo.list_devices(conn, "d")) == 2
        # resetting one frees a slot
        assert repo.reset_devices(conn, actor="root", name="d",
                                  device_id="phoneB") == 1
        assert repo.register_device(conn, name="d", device_id="tablet")["allowed"]
        # reset-all clears the registry
        assert repo.reset_devices(conn, actor="root", name="d") == 2
        assert repo.list_devices(conn, "d") == []


def test_device_unlimited_when_limit_zero(tmp_path):
    path = os.path.join(str(tmp_path), "kian.db")
    migrate.migrate_path(path)
    with db.session(path) as conn:
        repo.create_user(conn, actor="root", name="u")  # device_limit defaults 0
        for i in range(5):
            assert repo.register_device(conn, name="u", device_id=f"dev{i}")["allowed"]
        assert len(repo.list_devices(conn, "u")) == 5
        # unknown user -> denied, no crash
        assert not repo.register_device(conn, name="ghost", device_id="x")["allowed"]
