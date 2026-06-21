"""core.plugins — a tiny plugin system so protocols/features can be added
without touching core (phase 7.6).

A plugin registers a builder under a kind ("protocol", "sub_format", "notify",
...) and a name. Other code looks plugins up by (kind, name). Plugins can be
registered in-process via the decorator, or discovered from a package whose
modules each call :func:`register` at import time.

    from core.plugins import register, get, available

    @register("protocol", "hysteria2")
    def build_hysteria2(**kw): ...

    builder = get("protocol", "hysteria2")
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Callable, Optional

_REGISTRY: dict[tuple[str, str], Callable] = {}


def register(kind: str, name: str, fn: Optional[Callable] = None):
    """Register a plugin. Usable as a decorator or a direct call."""
    def _add(func: Callable) -> Callable:
        _REGISTRY[(kind, name)] = func
        return func
    return _add(fn) if fn is not None else _add


def get(kind: str, name: str) -> Optional[Callable]:
    return _REGISTRY.get((kind, name))


def available(kind: Optional[str] = None) -> list[str]:
    """List registered plugin names, optionally filtered by kind."""
    return sorted(n for (k, n) in _REGISTRY if kind is None or k == kind)


def unregister(kind: str, name: str) -> bool:
    return _REGISTRY.pop((kind, name), None) is not None


def discover(package_name: str = "kian_plugins") -> int:
    """Import every module under *package_name* so they self-register.

    Returns the number of modules imported. Missing package -> 0 (no error).
    """
    try:
        pkg = importlib.import_module(package_name)
    except ModuleNotFoundError:
        return 0
    count = 0
    for mod in pkgutil.iter_modules(pkg.__path__):
        importlib.import_module(f"{package_name}.{mod.name}")
        count += 1
    return count
