#!/usr/bin/env python3
"""kian-backup — encrypted automated backup for kian_v2ray.

Bundles the important server state (users.json, config.json, the SQLite db and
the /etc/kian-v2ray secrets) into a single tar.gz, encrypts it with
AES-256-CBC via the system ``openssl`` (present on every VPS — no pip install),
and ships it to one or more destinations:

    * Telegram  — uploaded as a document via the Bot API (stdlib urllib only)
    * S3 / R2   — via the system ``aws`` or ``rclone`` CLI if configured

Designed to be run from cron, e.g. nightly:
    0 3 * * *  /usr/bin/python3 /usr/local/bin/kian-backup.py --telegram

Environment:
    KIAN_BACKUP_PASSPHRASE   AES passphrase (required for encryption)
    KIAN_TG_BOT_TOKEN        Telegram bot token        (for --telegram)
    KIAN_TG_CHAT_ID          Telegram chat/channel id  (for --telegram)
    KIAN_S3_URI              s3://bucket/prefix         (for --s3, uses aws cli)
    KIAN_RCLONE_REMOTE       rclone remote:path         (for --rclone)
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

DEFAULT_SOURCES = [
    "/etc/kian-v2ray",
    "/opt/kian-v2ray/users.json",
    "/opt/kian-v2ray/config.json",
]


def _log(msg: str) -> None:
    print(f"[kian-backup] {msg}", file=sys.stderr)


def make_archive(sources: list[str], workdir: str) -> str:
    """tar.gz the existing source paths. Returns the archive path."""
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    archive = os.path.join(workdir, f"kian-backup-{stamp}.tar.gz")
    with tarfile.open(archive, "w:gz") as tar:
        for src in sources:
            if os.path.exists(src):
                tar.add(src, arcname=os.path.basename(src.rstrip("/")))
            else:
                _log(f"skip (missing): {src}")
    return archive


def encrypt(archive: str, passphrase: str) -> str:
    """AES-256-CBC encrypt via openssl. Returns the .enc path."""
    if not shutil.which("openssl"):
        raise RuntimeError("openssl not found; cannot encrypt backup")
    enc = archive + ".enc"
    subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt",
         "-in", archive, "-out", enc, "-pass", "env:KIAN_BACKUP_PASSPHRASE"],
        check=True,
        env={**os.environ, "KIAN_BACKUP_PASSPHRASE": passphrase},
    )
    return enc


def send_telegram(path: str, token: str, chat_id: str) -> None:
    """Upload *path* as a Telegram document (multipart/form-data, stdlib)."""
    boundary = "----kianbackup" + str(int(time.time()))
    with open(path, "rb") as fh:
        file_bytes = fh.read()
    filename = os.path.basename(path)
    pre = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode()
    post = f"\r\n--{boundary}--\r\n".encode()
    body = pre + file_bytes + post
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendDocument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        if resp.status != 200:
            raise RuntimeError(f"telegram upload failed: HTTP {resp.status}")
    _log("telegram: uploaded")


def send_s3(path: str, s3_uri: str) -> None:
    if not shutil.which("aws"):
        raise RuntimeError("aws cli not found; cannot upload to S3")
    dest = s3_uri.rstrip("/") + "/" + os.path.basename(path)
    subprocess.run(["aws", "s3", "cp", path, dest], check=True)
    _log(f"s3: uploaded to {dest}")


def send_rclone(path: str, remote: str) -> None:
    if not shutil.which("rclone"):
        raise RuntimeError("rclone not found; cannot upload")
    subprocess.run(["rclone", "copy", path, remote], check=True)
    _log(f"rclone: copied to {remote}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Encrypted kian_v2ray backup")
    ap.add_argument("--telegram", action="store_true", help="send to Telegram")
    ap.add_argument("--s3", action="store_true", help="upload to S3 (aws cli)")
    ap.add_argument("--rclone", action="store_true", help="upload via rclone")
    ap.add_argument("--out", help="also copy the .enc to this local dir")
    ap.add_argument("--source", action="append", default=None,
                    help="override source path (repeatable)")
    args = ap.parse_args(argv)

    passphrase = os.environ.get("KIAN_BACKUP_PASSPHRASE")
    if not passphrase:
        _log("ERROR: set KIAN_BACKUP_PASSPHRASE")
        return 2

    sources = args.source or DEFAULT_SOURCES
    workdir = tempfile.mkdtemp(prefix="kian-backup-")
    try:
        archive = make_archive(sources, workdir)
        enc = encrypt(archive, passphrase)
        os.remove(archive)  # keep only the encrypted copy
        _log(f"created {os.path.basename(enc)} ({os.path.getsize(enc)} bytes)")

        ok = True
        if args.out:
            os.makedirs(args.out, exist_ok=True)
            shutil.copy2(enc, args.out)
            _log(f"local copy → {args.out}")
        if args.telegram:
            try:
                send_telegram(enc, os.environ["KIAN_TG_BOT_TOKEN"],
                              os.environ["KIAN_TG_CHAT_ID"])
            except (KeyError, urllib.error.URLError, RuntimeError) as exc:
                _log(f"telegram FAILED: {exc}"); ok = False
        if args.s3:
            try:
                send_s3(enc, os.environ["KIAN_S3_URI"])
            except (KeyError, subprocess.CalledProcessError, RuntimeError) as exc:
                _log(f"s3 FAILED: {exc}"); ok = False
        if args.rclone:
            try:
                send_rclone(enc, os.environ["KIAN_RCLONE_REMOTE"])
            except (KeyError, subprocess.CalledProcessError, RuntimeError) as exc:
                _log(f"rclone FAILED: {exc}"); ok = False
        return 0 if ok else 1
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
