"""Tests for the core.plugins registry (phase 7.6)."""

from __future__ import annotations

from core import plugins


def setup_function():
    # isolate the registry between tests
    plugins._REGISTRY.clear()


def test_register_and_get_as_decorator():
    @plugins.register("protocol", "demo")
    def build(**kw):
        return {"type": "demo", **kw}

    fn = plugins.get("protocol", "demo")
    assert fn is build
    assert fn(port=443)["port"] == 443


def test_register_direct_call_and_available():
    plugins.register("sub_format", "clash", lambda x: x)
    plugins.register("sub_format", "singbox", lambda x: x)
    plugins.register("notify", "telegram", lambda x: x)
    assert plugins.available("sub_format") == ["clash", "singbox"]
    assert "telegram" in plugins.available()


def test_unregister_and_missing():
    plugins.register("x", "y", lambda: 1)
    assert plugins.get("x", "y") is not None
    assert plugins.unregister("x", "y") is True
    assert plugins.get("x", "y") is None
    assert plugins.unregister("x", "y") is False


def test_discover_missing_package_is_safe():
    assert plugins.discover("definitely_not_a_real_pkg_kian") == 0
