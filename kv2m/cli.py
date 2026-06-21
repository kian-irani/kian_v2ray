#!/usr/bin/env python3
"""kv2m CLI — interactive multi-server SSH management menu (no GUI).

v3.1: now multi-server. Saved server profiles (servers.py) are listed at start;
pick one, add a new one, or remove. Preferences (settings.py) persist the last
server; the updater (updater.py) checks GitHub for a newer build.
"""
import getpass

import core
from core import (SSH, cmd_status, cmd_users, cmd_configs, cmd_add,
                  cmd_renew, cmd_reset, cmd_remove, cmd_sub, cmd_update,
                  APP_VERSION)
import servers as servers_mod
import settings as settings_mod
import updater as updater_mod


def _choose_server(store: settings_mod.Settings, sstore):
    """Return a connected SSH session, or None. Handles add/remove/pick."""
    while True:
        profiles = sstore.profiles
        print("\n=== Servers ===")
        for i, p in enumerate(profiles, 1):
            mark = "*" if p.name == sstore.active else " "
            print(f" {mark}{i}) {p.name}  ({p.user}@{p.host}:{p.port})")
        print(" a) add new server")
        if profiles:
            print(" d) delete a server")
        print(" 0) quit")
        c = input("choose [1]: ").strip() or ("1" if profiles else "a")

        if c == "0":
            return None
        if c == "a":
            name = input("name: ").strip()
            host = input("host/IP: ").strip()
            port = int(input("ssh port [22]: ").strip() or "22")
            user = input("user [root]: ").strip() or "root"
            try:
                sstore.add(servers_mod.ServerProfile(
                    name=name, host=host, port=port, user=user))
                print(f"✔ saved {name}")
            except ValueError as e:
                print(f"✘ {e}")
            continue
        if c == "d" and profiles:
            idx = input("delete which #: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(profiles):
                sstore.remove(profiles[int(idx) - 1].name)
                print("✔ removed")
            continue
        if c.isdigit() and 1 <= int(c) <= len(profiles):
            prof = sstore.select(profiles[int(c) - 1].name)
            store.set("last_server", prof.name)
            pwd = getpass.getpass(f"Password for {prof.user}@{prof.host}: ")
            try:
                ssh = SSH().connect(prof.host, str(prof.port), prof.user,
                                    password=pwd or None)
                print("✔ connected")
                return ssh
            except Exception as e:  # noqa: BLE001
                print(f"✘ {e}")
                continue


def _deploy_panel(ssh):
    """Deploy the web panel on the connected server over SSH, print URL+creds."""
    import getpass as _gp
    user = input("panel admin username [admin]: ").strip() or "admin"
    pw = _gp.getpass("panel admin password (empty = random): ")
    env = f'KIAN_ADMIN_USER={user} '
    if pw:
        env += f'KIAN_ADMIN_PASSWORD={pw!r} '
    print("→ deploying web panel (this installs deps + a systemd service)…")
    code, out = ssh.run(f'{env}kian-v2ray panel enable')
    print(out)
    if code != 0:
        print("✘ panel deploy failed (Xray is untouched).")


def run():
    print(f"Kv2m v{APP_VERSION} — kian_v2ray (multi-server CLI)")
    cfg = settings_mod.Settings()
    sstore = servers_mod.ServerStore()
    if cfg.get("check_updates"):
        info = updater_mod.check(APP_VERSION)
        if info.get("update"):
            print(f"⬆ update available: {info['latest']} → {info['download_url']}")

    ssh = _choose_server(cfg, sstore)
    if ssh is None:
        print("bye")
        return 0

    MENU = [
        ("status", lambda: print(ssh.run(cmd_status())[1])),
        ("users", lambda: print(ssh.run(cmd_users())[1])),
        ("configs <name>", lambda: print(ssh.run(cmd_configs(input("name: ").strip()))[1])),
        ("add <name>", lambda: print(ssh.run(cmd_add(input("name: ").strip(), int(input("GB [100]: ") or 100), int(input("days [30]: ") or 30)))[1])),
        ("renew <name>", lambda: print(ssh.run(cmd_renew(input("name: ").strip(), int(input("days [30]: ") or 30)))[1])),
        ("reset <name>", lambda: print(ssh.run(cmd_reset(input("name: ").strip(), int(input("GB [0]: ") or 0)))[1])),
        ("remove <name>", lambda: print(ssh.run(cmd_remove(input("name: ").strip()))[1])),
        ("sub <name>", lambda: print(ssh.run(cmd_sub(input("name: ").strip()))[1])),
        ("update", lambda: print(ssh.run(cmd_update())[1])),
        ("deploy web panel", lambda: _deploy_panel(ssh)),
    ]
    try:
        while True:
            print("\n" + "-" * 36)
            for i, (l, _) in enumerate(MENU, 1):
                print(f"  {i}) {l}")
            print("  0) exit")
            c = input("choose [0]: ").strip() or "0"
            if c == "0":
                break
            try:
                MENU[int(c) - 1][1]()
            except Exception as e:  # noqa: BLE001
                print(f"error: {e}")
    finally:
        ssh.close()
        print("bye")
    return 0
