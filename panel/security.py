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

_PBKDF2_ITERATIONS = 200_000
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
