#!/usr/bin/env python3
# ============================================================================
#  KIAN V2Ray — Gist sync (از طریق Cloudflare Worker)
#   فایل‌های sub محلی ($ETC_DIR/sub/<token>.txt) را به Worker می‌فرستد؛ Worker
#   با توکن خصوصیِ Gist (که فقط سمت خودش است) گیست‌ها را می‌سازد/آپدیت/حذف می‌کند
#   و URLهای HTTPS را برمی‌گرداند. توکن گیت‌هاب هرگز روی سرور کاربر نیست.
#
#  اجرا:
#     gist_sync.py <proxy_url> <install_id_file> <subdir> <map_file> [--delete]
#       proxy_url       : آدرس Worker (مثلاً https://kian-sub.kian-mhrv.workers.dev)
#       install_id_file : فایل حاوی شناسهٔ یکتای این نصب (اگر نبود، ساخته می‌شود)
#       subdir          : دایرکتوری sub محلی
#       map_file        : فایل JSON برای ذخیرهٔ نگاشت token→url
#       --delete        : همهٔ گیست‌های این نصب را پاک کن
# ============================================================================
import json
import os
import secrets
import sys
import time
import urllib.request
import urllib.error


def _post(url, body, retries=3):
    data = json.dumps(body).encode("utf-8")
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "Mozilla/5.0 (kian-v2ray) curl-like")
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=30) as resp:
                txt = resp.read().decode("utf-8", "replace")
                return json.loads(txt) if txt else {}
        except urllib.error.HTTPError as e:
            try:
                last = e.read().decode("utf-8", "replace")
            except Exception:
                last = f"HTTP {e.code}"
            time.sleep(2 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError) as e:
            last = f"net: {e}"
            time.sleep(2 * (attempt + 1))
    print(f"[!] proxy POST failed: {last}", file=sys.stderr)
    return None


def _load_install_id(path):
    if os.path.isfile(path):
        try:
            v = open(path, encoding="utf-8").read().strip()
            if v:
                return v
        except OSError:
            pass
    # ساخت شناسهٔ یکتای جدید (32 hex)
    iid = secrets.token_hex(16)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(iid)
        os.chmod(path, 0o600)
    except OSError:
        pass
    return iid


def main():
    args = sys.argv[1:]
    delete = "--delete" in args
    args = [a for a in args if a != "--delete"]
    if len(args) < 4:
        print("usage: gist_sync.py <proxy_url> <install_id_file> <subdir> <map_file> [--delete]", file=sys.stderr)
        sys.exit(2)
    proxy, iid_file, subdir, map_file = args[0], args[1], args[2], args[3]
    proxy = proxy.rstrip("/")
    install_id = _load_install_id(iid_file)

    if delete:
        r = _post(proxy + "/delete", {"install_id": install_id})
        if r and r.get("ok"):
            print(f"✔ {r.get('deleted', 0)} گیست حذف شد")
            try:
                os.remove(map_file)
            except OSError:
                pass
            sys.exit(0)
        print("[!] حذف گیست‌ها ناموفق", file=sys.stderr)
        sys.exit(1)

    # جمع‌آوری فایل‌های sub
    items = {}
    if os.path.isdir(subdir):
        for name in os.listdir(subdir):
            if not name.endswith(".txt"):
                continue
            tok = name[:-4]
            if not tok or not tok.replace("-", "").replace("_", "").isalnum():
                continue
            try:
                items[tok] = open(os.path.join(subdir, name), encoding="utf-8").read().strip()
            except OSError:
                pass

    if not items:
        print("[i] هیچ فایل sub برای همگام‌سازی نیست")
        sys.exit(0)

    r = _post(proxy + "/sync", {"install_id": install_id, "items": items})
    if not r or not r.get("ok"):
        print(f"[!] همگام‌سازی ناموفق: {r}", file=sys.stderr)
        sys.exit(1)

    urls = r.get("urls", {})
    out = {tok: {"url": u} for tok, u in urls.items()}
    tmp = map_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    os.replace(tmp, map_file)
    try:
        os.chmod(map_file, 0o600)
    except OSError:
        pass
    for tok, u in urls.items():
        print(f"[+] {tok[:8]}...  → {u}")
    print(f"\n✔ {len(urls)} لینک Subscription روی HTTPS گیت‌هاب آماده است.")


if __name__ == "__main__":
    main()
