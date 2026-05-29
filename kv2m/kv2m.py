#!/usr/bin/env python3
"""
Kv2m — نقطهٔ ورود
  python kv2m.py            → رابط گرافیکی (روی PC؛ نیازمند Tkinter که پیش‌فرض پایتون است)
  python kv2m.py --cli      → رابط خط فرمان (PC و اندروید/Termux)
اگر Tkinter نبود، خودکار به CLI سوییچ می‌کند.
"""
import sys


def main():
    if "--cli" in sys.argv or "-c" in sys.argv:
        import kv2m_cli
        return kv2m_cli.main()
    try:
        import tkinter  # noqa: F401
    except Exception:
        print("Tkinter یافت نشد — اجرای حالت خط فرمان (CLI)…")
        import kv2m_cli
        return kv2m_cli.main()
    import kv2m_gui
    return kv2m_gui.main()


if __name__ == "__main__":
    sys.exit(main() or 0)
