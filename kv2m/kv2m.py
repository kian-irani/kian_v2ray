#!/usr/bin/env python3
"""Kv2m v3.0 — Kian V2Ray Manager. Entry point.

GUI (default, PySide6) or CLI (--cli). All modules live alongside this file;
we add this dir to sys.path so PyInstaller script-mode imports resolve.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for _s in ("stdout", "stderr"):
    _st = getattr(sys, _s, None)
    try:
        if _st: _st.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def main():
    if "--cli" in sys.argv or "-c" in sys.argv:
        import cli; return cli.run()
    try:
        import app; app.run(); return 0
    except ImportError as e:
        print(f"GUI needs PySide6: pip install PySide6  ({e})")
        import cli; return cli.run()

if __name__ == "__main__":
    sys.exit(main() or 0)
