#!/usr/bin/env python3
# ============================================================================
#  kian_v2ray — sync با upstream (Xray-core)
#   آخرین نسخهٔ پایدار Xray-core را می‌گیرد و اگر جدیدتر از XRAY_VERSION فعلی بود،
#   فایل VERSION را آپدیت می‌کند و یک entry در CHANGELOG می‌گذارد.
#   این اسکریپت توسط workflow هر ۲ روز اجرا می‌شود و یک PR می‌سازد (نه push مستقیم)
#   تا قبل از pin، نسخه روی سرور تست/تأیید شود.
#   خروجی‌ها برای workflow روی GITHUB_OUTPUT نوشته می‌شوند.
# ============================================================================
import json
import os
import re
import sys
import urllib.request

REPO = "XTLS/Xray-core"
VERSION_FILE = "VERSION"
CHANGELOG = "CHANGELOG.md"


def gh_api(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "kian-v2ray-sync",
    })
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def latest_stable():
    # releases را بگیر و اولین نسخهٔ غیر pre-release را بردار
    rels = gh_api(f"https://api.github.com/repos/{REPO}/releases?per_page=15")
    for rel in rels:
        if rel.get("prerelease") or rel.get("draft"):
            continue
        tag = rel.get("tag_name", "").lstrip("v")
        if re.match(r"^\d+\.\d+\.\d+$", tag):
            return tag
    return None


def read_version():
    with open(VERSION_FILE, encoding="utf-8") as f:
        txt = f.read()
    m = re.search(r"^XRAY_VERSION=(.+)$", txt, re.M)
    return txt, (m.group(1).strip() if m else None)


def set_output(key, val):
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"{key}={val}\n")


def vtuple(v):
    try:
        return tuple(int(x) for x in v.split("."))
    except (ValueError, AttributeError):
        return (0,)


def main():
    force = os.environ.get("FORCE", "false") == "true"
    new = latest_stable()
    if not new:
        print("نتونست نسخهٔ پایدار را بگیرد")
        set_output("has_changes", "false")
        return 0
    txt, cur = read_version()
    print(f"فعلی: {cur} | آخرین پایدار: {new}")
    set_output("old_version", cur or "?")
    set_output("new_version", new)
    # فقط اگر نسخهٔ جدید واقعاً بزرگ‌تر از فعلی بود آپدیت کن (نه عقب‌گرد، نه برابر)
    if not force and (cur is None or vtuple(new) <= vtuple(cur)):
        print("نسخهٔ فعلی به‌روز یا جدیدتر است — تغییری لازم نیست")
        set_output("has_changes", "false")
        return 0
    # آپدیت VERSION
    txt2 = re.sub(r"^XRAY_VERSION=.*$", f"XRAY_VERSION={new}", txt, flags=re.M)
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(txt2)
    # entry در CHANGELOG (زیر [Unreleased] اگر بود، وگرنه بالای فایل بعد از سرتیتر)
    try:
        with open(CHANGELOG, encoding="utf-8") as f:
            cl = f.read()
        entry = f"\n## [unreleased] — sync\n\n### تغییر\n- pin نسخهٔ Xray-core از `{cur}` به `{new}` (auto-sync). **قبل از merge روی سرور تست شود.**\n"
        # بعد از اولین --- می‌گذاریم
        idx = cl.find("\n---\n")
        if idx != -1:
            cl = cl[:idx + 5] + entry + cl[idx + 5:]
        else:
            cl = cl + entry
        with open(CHANGELOG, "w", encoding="utf-8") as f:
            f.write(cl)
    except FileNotFoundError:
        pass
    print(f"VERSION آپدیت شد → XRAY_VERSION={new}")
    set_output("has_changes", "true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
