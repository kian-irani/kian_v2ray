"""kv2m.settings — persisted user preferences for the desktop app (phase 3.4).

Stores the chosen theme (dark/light), language (fa/en) and last-used server in
a small JSON file under the user's config dir, so the GUI restores them at
launch. Stdlib only, testable.
"""

from __future__ import annotations

import json
import os
from typing import Any

try:  # kv2m modules are used flat (sys.path), but support package import too.
    from .servers import config_dir
except ImportError:
    from servers import config_dir

_DEFAULTS: dict[str, Any] = {
    "theme": "dark",     # dark | light | system
    "lang": "fa",        # fa | en
    "last_server": None,
    "minimize_to_tray": True,
    "check_updates": True,
}


def settings_path() -> str:
    return os.environ.get("KV2M_SETTINGS",
                          os.path.join(config_dir(), "settings.json"))


class Settings:
    def __init__(self, path: str | None = None):
        self.path = path or settings_path()
        self.data: dict[str, Any] = dict(_DEFAULTS)
        self.load()

    def load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                if isinstance(stored, dict):
                    self.data.update({k: v for k, v in stored.items()
                                      if k in _DEFAULTS})
            except (json.JSONDecodeError, OSError):
                pass  # corrupt file -> fall back to defaults

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def get(self, key: str) -> Any:
        return self.data.get(key, _DEFAULTS.get(key))

    def set(self, key: str, value: Any) -> None:
        if key not in _DEFAULTS:
            raise KeyError(f"unknown setting: {key}")
        self.data[key] = value
        self.save()

    def toggle_theme(self) -> str:
        new = "light" if self.data.get("theme") == "dark" else "dark"
        self.set("theme", new)
        return new
