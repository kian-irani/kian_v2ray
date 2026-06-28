"""panel.security — authentication primitives, standard-library only.

Hand-rolled so the panel has *zero* crypto dependencies (no PyJWT, no passlib):

* :func:`hash_password` / :func:`verify_password` — PBKDF2-HMAC-SHA256 with a
  per-password random salt, stored as ``pbkdf2_sha256$iter$salt$hash``.
* :func:`create_token` / :func:`decode_token` — compact HS256 JWTs.

These are intentionally small and auditable. They are unit-tested in
tests/test_panel_security.py and run without a server.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Optional

# OWASP 2023 minimum for PBKDF2-HMAC-SHA256. The iteration count is stored in
# each hash, so old 200k hashes still verify — only new hashes use 600k.
_PBKDF2_ITERATIONS = 600_000
_ALGO = "pbkdf2_sha256"


# --------------------------------------------------------------------------- #
# password hashing
# --------------------------------------------------------------------------- #
def hash_password(password: str, *, iterations: int = _PBKDF2_ITERATIONS) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"{_ALGO}${iterations}${_b64(salt)}${_b64(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iter_s, salt_b64, hash_b64 = stored.split("$")
        if algo != _ALGO:
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), _unb64(salt_b64), int(iter_s))
        return hmac.compare_digest(dk, _unb64(hash_b64))
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# JWT (HS256)
# --------------------------------------------------------------------------- #
def create_token(secret: str, sub: str, *, ttl_seconds: int = 900,
                 extra: Optional[dict[str, Any]] = None,
                 now: Optional[int] = None) -> str:
    issued = int(now if now is not None else time.time())
    payload: dict[str, Any] = {"sub": sub, "iat": issued,
                               "exp": issued + ttl_seconds}
    if extra:
        payload.update(extra)
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{_b64url_json(header)}.{_b64url_json(payload)}"
    sig = hmac.new(secret.encode(), signing_input.encode(),
                   hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(sig)}"


def decode_token(secret: str, token: str,
                 now: Optional[int] = None) -> dict[str, Any]:
    """Return the payload if the signature + expiry are valid, else raise."""
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError as exc:
        raise InvalidToken("malformed token") from exc
    signing_input = f"{header_b64}.{payload_b64}"
    expected = hmac.new(secret.encode(), signing_input.encode(),
                        hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _unb64url(sig_b64)):
        raise InvalidToken("bad signature")
    payload = json.loads(_unb64url(payload_b64))
    current = int(now if now is not None else time.time())
    if int(payload.get("exp", 0)) < current:
        raise InvalidToken("expired")
    return payload


class InvalidToken(Exception):
    """Raised by :func:`decode_token` on any verification failure."""


# --------------------------------------------------------------------------- #
# TOTP (RFC 6238) — optional 2FA, stdlib only
# --------------------------------------------------------------------------- #
def generate_totp_secret() -> str:
    """A base32 secret suitable for Google Authenticator / Aegis."""
    return base64.b32encode(os.urandom(20)).decode().rstrip("=")


def totp_at(secret_b32: str, *, for_time: Optional[int] = None,
            step: int = 30, digits: int = 6) -> str:
    counter = int((for_time if for_time is not None else time.time()) // step)
    key = base64.b32decode(_pad_b32(secret_b32.upper()))
    msg = counter.to_bytes(8, "big")
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = ((digest[offset] & 0x7F) << 24 | digest[offset + 1] << 16
            | digest[offset + 2] << 8 | digest[offset + 3]) % (10 ** digits)
    return str(code).zfill(digits)


def verify_totp(secret_b32: str, code: str, *, for_time: Optional[int] = None,
                window: int = 1) -> bool:
    """Accept a code valid within +/- *window* steps (clock skew tolerance)."""
    now = int(for_time if for_time is not None else time.time())
    code = str(code).strip()
    for drift in range(-window, window + 1):
        if hmac.compare_digest(totp_at(secret_b32, for_time=now + drift * 30),
                               code):
            return True
    return False


def parse_ip_allowlist(raw: str) -> frozenset[str]:
    """Parse a comma-separated IP allowlist env value into a set of IPs."""
    return frozenset(ip.strip() for ip in (raw or "").split(",") if ip.strip())


def ip_allowed(ip: Optional[str], allowlist: "frozenset[str] | set[str]") -> bool:
    """Allowlist gate. An empty allowlist means 'no restriction' (allow all);
    otherwise *ip* must be an exact member."""
    if not allowlist:
        return True
    return ip is not None and ip in allowlist


def _pad_b32(s: str) -> str:
    return s + "=" * (-len(s) % 8)


# --------------------------------------------------------------------------- #
# base64 helpers
# --------------------------------------------------------------------------- #
def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def _unb64(s: str) -> bytes:
    return base64.b64decode(s.encode())


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _unb64url(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _b64url_json(obj: dict[str, Any]) -> str:
    return _b64url(json.dumps(obj, separators=(",", ":")).encode())
