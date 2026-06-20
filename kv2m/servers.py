"""kv2m.servers — multi-server profile management for the Kv2m desktop app.

Phase 3 turns Kv2m from a single-host tool into a multi-server manager. A
profile is a saved SSH target; profiles are persisted as JSON under the user's
config dir so they survive restarts. No third-party deps (passwords are NOT
stored — only connection coordinates; the GUI asks for the secret per session
or uses an ssh key path).
"""

from __future__ import annotations

import dataclasses
import json
import os
from typing import Optional


def config_dir() -> str:
    base = (os.environ.get("XDG_CONFIG_HOME")
            or os.path.join(os.path.expanduser("~"), ".config"))
    path = os.path.join(base, "kv2m")
    os.makedirs(path, exist_ok=True)
    return path


def config_path() -> str:
    return os.environ.get("KV2M_SERVERS", os.path.join(config_dir(), "servers.json"))


@dataclasses.dataclass
class ServerProfile:
    name: str
    host: str
    port: int = 22
    user: str = "root"
    key_path: Optional[str] = None      # path to a private key, optional
    domain: Optional[str] = None        # TLS domain if configured
    note: str = ""

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "ServerProfile":
        known = {f.name for f in dataclasses.fields(ServerProfile)}
        return ServerProfile(**{k: v for k, v in d.items() if k in known})


class ServerStore:
    """Load/save a list of :class:`ServerProfile` and track the active one."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or config_path()
        self.profiles: list[ServerProfile] = []
        self.active: Optional[str] = None
        self.load()

    # ---- persistence ----
    def load(self) -> None:
        if not os.path.exists(self.path):
            self.profiles, self.active = [], None
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.profiles = [ServerProfile.from_dict(d) for d in data.get("servers", [])]
        self.active = data.get("active")

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"servers": [p.to_dict() for p in self.profiles],
                       "active": self.active}, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    # ---- operations ----
    def add(self, profile: ServerProfile) -> ServerProfile:
        if any(p.name == profile.name for p in self.profiles):
            raise ValueError(f"server '{profile.name}' already exists")
        self.profiles.append(profile)
        if self.active is None:
            self.active = profile.name
        self.save()
        return profile

    def remove(self, name: str) -> bool:
        before = len(self.profiles)
        self.profiles = [p for p in self.profiles if p.name != name]
        if self.active == name:
            self.active = self.profiles[0].name if self.profiles else None
        changed = len(self.profiles) != before
        if changed:
            self.save()
        return changed

    def get(self, name: str) -> Optional[ServerProfile]:
        return next((p for p in self.profiles if p.name == name), None)

    def select(self, name: str) -> ServerProfile:
        p = self.get(name)
        if p is None:
            raise KeyError(name)
        self.active = name
        self.save()
        return p

    def active_profile(self) -> Optional[ServerProfile]:
        return self.get(self.active) if self.active else None
