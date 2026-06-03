#!/usr/bin/env python3
"""kv2m CLI — interactive SSH management menu (no GUI). Uses core."""
import getpass
import core
from core import (SSH, cmd_status, cmd_users, cmd_configs, cmd_add,
                  cmd_renew, cmd_reset, cmd_remove, cmd_sub, cmd_update, APP_VERSION)

def run():
    print(f"Kv2m v{APP_VERSION} — kian_v2ray (CLI)")
    host = input("Server IP: ").strip()
    port = input("SSH port [22]: ").strip() or "22"
    user = input("User [root]: ").strip() or "root"
    pwd = getpass.getpass("Password: ")
    try:
        ssh = SSH().connect(host, port, user, password=pwd or None); print("✔ connected")
    except Exception as e:
        print(f"✘ {e}"); return 1
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
    ]
    try:
        while True:
            print("\n" + "-"*36)
            for i,(l,_) in enumerate(MENU,1): print(f"  {i}) {l}")
            print("  0) exit")
            c = input("choose [0]: ").strip() or "0"
            if c == "0": break
            try: MENU[int(c)-1][1]()
            except Exception as e: print(f"error: {e}")
    finally:
        ssh.close(); print("bye")
    return 0
