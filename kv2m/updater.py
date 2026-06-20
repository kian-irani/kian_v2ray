"""kv2m.updater — check GitHub Releases for a newer Kv2m build (phase 3).

Compares the running version against the latest GitHub release tag and reports
whether an update is available + the download URL. Pure stdlib (urllib + json),
so it works on a bare desktop with no extra packages.
"""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Optional

LATEST_API = "https://api.github.com/repos/kian-irani/kian_v2ray/releases/latest"


def parse_version(tag: str) -> tuple[int, ...]:
    """'v3.0.2' / 'kv2m-3.0.2' -> (3, 0, 2).

    Prefer a dotted version token so a digit inside the product name
    (the '2' in 'kv2m') is not mistaken for a version component.
    """
    dotted = re.search(r"\d+(?:\.\d+)+", tag or "")
    if dotted:
        return tuple(int(n) for n in dotted.group().split("."))
    tail = re.findall(r"\d+", tag or "")
    return (int(tail[-1]),) if tail else (0,)


def is_newer(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)


def check(current: str, *, timeout: float = 8.0,
          url: str = LATEST_API) -> dict:
    """Return {update, latest, current, download_url, error?}."""
    try:
        req = urllib.request.Request(
            url, headers={"Accept": "application/vnd.github+json",
                          "User-Agent": "kv2m-updater"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:  # network / parse — never crash the app
        return {"update": False, "latest": None, "current": current,
                "download_url": None, "error": str(exc)}
    latest = data.get("tag_name", "")
    asset_url: Optional[str] = None
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.endswith((".exe", ".dmg", ".AppImage", ".zip")):
            asset_url = asset.get("browser_download_url")
            break
    return {"update": is_newer(latest, current), "latest": latest,
            "current": current,
            "download_url": asset_url or data.get("html_url")}
