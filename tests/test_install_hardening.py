"""Static hardening checks on install.sh (BUG-4 regression).

These don't run the installer (it needs root + docker); they assert that
known-bad permission patterns don't reappear in the shipped script.
"""

from __future__ import annotations

import os
import re

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _install_sh() -> str:
    with open(os.path.join(_HERE, "install.sh"), encoding="utf-8") as fh:
        return fh.read()


def test_no_world_writable_chmod():
    # BUG-4: the log dir was chmod 777 (world read/write/exec). No 777 / o+w
    # permission grants should remain in the installer.
    src = _install_sh()
    assert "chmod 777" not in src
    assert not re.search(r"chmod\s+[0-7]{0,2}[2367]\b", src), \
        "found a chmod granting world-write permission"


def test_log_dir_is_locked_down():
    # The log dir is created and explicitly restricted to root.
    src = _install_sh()
    assert 'chmod 750 "$LOG_DIR"' in src
    assert 'chown root:root "$LOG_DIR"' in src
