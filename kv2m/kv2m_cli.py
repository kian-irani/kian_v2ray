#!/usr/bin/env python3
"""
Kv2m — رابط خط فرمان (CLI)
روی ویندوز/مک/لینوکس و همچنین اندروید (داخل Termux) کار می‌کند.
اجرا:  python kv2m.py --cli      یا      python kv2m_cli.py
"""
import sys
import kv2m_core as core

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, IntPrompt, Confirm
    RICH = True
    con = Console()
except Exception:
    RICH = False
    con = None


def _say(msg, style=""):
    if RICH:
        con.print(msg, style=style)
    else:
        print(msg)


def _ask(label, default=""):
    if RICH:
        return Prompt.ask(label, default=default)
    v = input(f"{label} [{default}]: ").strip()
    return v or default


def _ask_int(label, default):
    if RICH:
        return IntPrompt.ask(label, default=default)
    try:
        return int(input(f"{label} [{default}]: ").strip() or default)
    except ValueError:
        return default


def banner():
    t = "KV2M — مدیریت سرور Kian V2Ray  (v%s)" % core.APP_VERSION
    if RICH:
        con.print(Panel.fit(t, style="bold cyan"))
    else:
        print("=" * 48 + f"\n{t}\n" + "=" * 48)


def connect_flow() -> core.SSH:
    _say("\n[bold]اتصال به سرور (SSH)[/bold]" if RICH else "\nاتصال به سرور (SSH)")
    host = _ask("آی‌پی یا دامنهٔ سرور")
    port = _ask_int("پورت SSH", 22)
    user = _ask("نام کاربری", "root")
    use_key = _ask("ورود با کلید؟ (y/N)", "n").lower().startswith("y")
    key_path = pwd = None
    if use_key:
        key_path = _ask("مسیر فایل کلید خصوصی")
    else:
        if RICH:
            from rich.prompt import Prompt as P
            pwd = P.ask("رمز", password=True)
        else:
            import getpass
            pwd = getpass.getpass("رمز: ")
    ssh = core.SSH()
    _say("در حال اتصال…")
    ssh.connect(host, port, user, password=pwd, key_path=key_path)
    _say("[green]✔ متصل شد[/green]" if RICH else "✔ متصل شد")
    # چک نصب
    rc, out, _ = ssh.run(core.cmd_installed_check())
    if "KV2M_MISSING" in out:
        _say("[yellow]⚠ روی این سرور هنوز kian-v2ray نصب نشده — از منو «نصب/ساخت کانفیگ تازه» را بزن.[/yellow]"
             if RICH else "⚠ kian-v2ray نصب نیست — از منو «نصب تازه» را بزن.")
    return ssh


def show_users(ssh):
    rc, out, err = ssh.run(core.cmd_users())
    rows = core.parse_users(out)
    if RICH and rows:
        tb = Table(title="کاربرها", show_lines=False)
        for col in ("ایمیل", "فعال", "مصرف", "حجم", "انقضا"):
            tb.add_column(col)
        for r in rows:
            tb.add_row(r["email"], r["active"], r["used"], r["quota"], r["expiry"])
        con.print(tb)
    else:
        print(out or err)


def show_configs(ssh):
    name = _ask("نام کاربر (خالی = همه)", "")
    rc, out, err = ssh.run(core.cmd_configs(name))
    links = core.parse_links(out)
    if links:
        _say(f"\n{len(links)} لینک:")
        for ln in links:
            _say(ln)
    else:
        print(out or err)


def do_add(ssh):
    name = _ask("نام کاربر جدید (انگلیسی)")
    gb = _ask_int("حجم (گیگ، 0=نامحدود)", 100)
    days = _ask_int("مدت (روز، 0=دائمی)", 30)
    rc, out, err = ssh.run(core.cmd_add(name, gb, days))
    _say(out or err)


def do_simple(ssh, builder, *need):
    name = _ask("نام کاربر")
    extra = {}
    if "days" in need:
        extra["days"] = _ask_int("مدت (روز)", 30)
    if "gb" in need:
        extra["gb"] = _ask_int("حجم (گیگ)", 100)
    cmd = builder(name, **extra) if extra else builder(name)
    rc, out, err = ssh.run(cmd)
    _say(out or err or "انجام شد.")


def provision(ssh):
    _say("\n[bold]نصب/ساخت کانفیگ تازه روی این سرور[/bold]" if RICH else "\nنصب تازه روی این سرور")
    ip = _ask("آی‌پی سرور (همان که وصل شدی)", ssh.host or "")
    mode = _ask("حالت: both / direct / warp / nosni", "both")
    opts = {"server_ip": ip, "mode": mode, "sni_mode": "auto",
            "sni_count": _ask_int("تعداد SNI (1-3)", 2) if mode != "nosni" else 1,
            "base_port": _ask_int("پورت پایه (اگه پنل دیگه‌ای داری عوض کن، مثلاً 9443)", 8443),
            "num_users": _ask_int("تعداد کاربر", 1),
            "prefix": _ask("نام پایهٔ کاربر", "user"),
            "quota_gb": _ask_int("حجم هر کاربر (گیگ، 0=نامحدود)", 0),
            "days": _ask_int("مدت اعتبار (روز، 0=دائمی)", 0)}
    g = core.generate(opts)
    _say(f"[green]کلید و کانفیگ ساخته شد. پورت‌ها: {g['ports']}[/green]" if RICH else f"ساخته شد. پورت‌ها: {g['ports']}")
    if not (Confirm.ask("الان روی سرور نصب شود؟") if RICH else _ask("نصب شود؟ (Y/n)", "y").lower().startswith("y")):
        _say("لغو شد. (می‌توانی بعداً دوباره اجرا کنی)")
        return
    cmd = f"export KIAN_PAYLOAD='{g['payload_b64']}'; curl -fsSL {core.RAW_BASE}/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh"
    _say("[dim]در حال نصب… (می‌تونه ۲-۵ دقیقه طول بکشه)[/dim]" if RICH else "در حال نصب…")
    ssh.run_stream(cmd, lambda line: _say(line))
    _say("\n[green]✔ دستور نصب اجرا شد. چند دقیقه بعد منو «وضعیت» را بزن.[/green]"
         if RICH else "✔ نصب اجرا شد. بعداً «وضعیت» را بزن.")
    _say("لینک‌های ساخته‌شده:")
    for u in g["per_user"]:
        for it in u["items"]:
            _say(it["link"])
    if g["ss_link"]:
        _say(g["ss_link"])


MENU = [
    ("وضعیت سرویس", lambda s: _say((s.run(core.cmd_status())[1]) or "")),
    ("لیست کاربرها", show_users),
    ("دیدن کانفیگ کاربر", show_configs),
    ("افزودن کاربر", do_add),
    ("تمدید اعتبار", lambda s: do_simple(s, core.cmd_renew, "days")),
    ("تغییر/صفر حجم", lambda s: do_simple(s, core.cmd_reset, "gb")),
    ("حذف کاربر", lambda s: do_simple(s, core.cmd_remove)),
    ("نصب/ساخت کانفیگ تازه", provision),
]


def main():
    banner()
    try:
        ssh = connect_flow()
    except Exception as e:
        _say(f"[red]✘ اتصال ناموفق: {e}[/red]" if RICH else f"✘ اتصال ناموفق: {e}")
        return 1
    try:
        while True:
            _say("\n" + "─" * 40)
            for i, (label, _) in enumerate(MENU, 1):
                _say(f"  {i}) {label}")
            _say("  0) خروج")
            choice = _ask("انتخاب", "0")
            if choice == "0":
                break
            try:
                idx = int(choice) - 1
                assert 0 <= idx < len(MENU)
            except Exception:
                _say("[red]گزینهٔ نامعتبر[/red]" if RICH else "نامعتبر")
                continue
            try:
                MENU[idx][1](ssh)
            except Exception as e:
                _say(f"[red]خطا: {e}[/red]" if RICH else f"خطا: {e}")
    finally:
        ssh.close()
        _say("خداحافظ 👋")
    return 0


if __name__ == "__main__":
    sys.exit(main())
