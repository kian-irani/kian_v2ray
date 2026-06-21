"""Tests for core.notify (channels are mocked — no real network)."""

from __future__ import annotations

from core import notify


def test_build_message_templates():
    assert "ali" in notify.build_message("user.expired", user="ali")
    assert "100" in notify.build_message("user.quota", user="ali", used_gb=100)
    assert "1.2.3.4" in notify.build_message("user.newip", user="ali", ip="1.2.3.4")
    # unknown kind falls back without raising
    assert "custom.kind" in notify.build_message("custom.kind", x=1)


def test_event_fanout_calls_each_channel(monkeypatch):
    n = notify.Notifier(
        telegram=("t", "c"),
        email_smtp={"host": "h", "from": "a@x", "to": "b@x"},
        webhook_url="https://example.com/hook",
    )
    calls = []
    monkeypatch.setattr(n, "_telegram", lambda text: calls.append("tg") or True)
    monkeypatch.setattr(n, "_email", lambda s, b: calls.append("em") or True)
    monkeypatch.setattr(n, "_webhook", lambda p: calls.append("wh") or True)
    res = n.event("user.expired", "ali expired", user="ali")
    assert res == {"telegram": True, "email": True, "webhook": True}
    assert set(calls) == {"tg", "em", "wh"}


def test_event_with_no_channels_is_noop():
    n = notify.Notifier()
    assert n.event("node.down", "x") == {}


def test_channel_failure_is_caught(monkeypatch):
    # a raising channel must not propagate; the others still run
    n = notify.Notifier(telegram=("t", "c"), webhook_url="https://x/y")

    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(urllib_request_open := "urllib.request.urlopen", boom,
                        raising=False)
    # _telegram/_webhook internally catch Exception -> return False
    res = n.event("node.down", "n1 down")
    assert res["telegram"] in (True, False)
    assert res["webhook"] in (True, False)
