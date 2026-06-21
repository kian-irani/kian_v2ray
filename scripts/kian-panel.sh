#!/usr/bin/env bash
# kian-panel.sh — one-command deploy of the KIAN web panel on the server.
#
# Makes the panel EASY: installs deps, drops in panel/ + core/, asks for the
# admin username/password, creates a systemd service, syncs the real installed
# users, opens the port, and prints the URL + credentials. Additive/opt-in —
# never touches the running Xray.
#
#   kian-panel.sh enable          # install + start + print URL
#   kian-panel.sh url             # print the panel URL + admin user
#   kian-panel.sh disable         # stop + remove the panel service
set -euo pipefail

APP_DIR="/opt/kian-panel"
PORT="${KIAN_PANEL_PORT:-8443}"
SVC="kian-panel"
RAW_TARBALL="https://github.com/kian-irani/kian_v2ray/archive/refs/heads/main.tar.gz"
DB_PATH="/etc/kian-v2ray/kian.db"

say(){ printf '\033[32m✔\033[0m %s\n' "$*"; }
inf(){ printf '\033[34m→\033[0m %s\n' "$*"; }
err(){ printf '\033[31m✘\033[0m %s\n' "$*" >&2; }
need_root(){ [ "$(id -u)" = 0 ] || { err "run as root"; exit 1; }; }

server_ip(){ curl -fsS4 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}'; }

fetch_code(){
  inf "fetching panel + core code"
  local tmp; tmp="$(mktemp -d)"
  curl -fsSL "$RAW_TARBALL" -o "$tmp/src.tgz"
  tar -xzf "$tmp/src.tgz" -C "$tmp"
  local root; root="$(find "$tmp" -maxdepth 1 -type d -name 'kian_v2ray-*' | head -1)"
  mkdir -p "$APP_DIR"
  cp -r "$root/panel" "$root/core" "$APP_DIR/"
  rm -rf "$tmp"
}

setup_venv(){
  inf "installing python venv + dependencies"
  command -v python3 >/dev/null || { apt-get update -y && apt-get install -y python3 python3-venv python3-pip; }
  python3 -m venv "$APP_DIR/venv"
  "$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
  "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/panel/requirements.txt"
}

ask_admin(){
  ADMIN_USER="${KIAN_ADMIN_USER:-}"
  ADMIN_PASS="${KIAN_ADMIN_PASSWORD:-}"
  if [ -z "$ADMIN_USER" ]; then
    read -r -p "Panel admin username [admin]: " ADMIN_USER || true
    ADMIN_USER="${ADMIN_USER:-admin}"
  fi
  if [ -z "$ADMIN_PASS" ]; then
    read -r -s -p "Panel admin password (leave empty = random): " ADMIN_PASS || true
    echo
    [ -n "$ADMIN_PASS" ] || ADMIN_PASS="$(openssl rand -base64 12 | tr -d '/+=' | cut -c1-14)"
  fi
}

install_service(){
  cat > "/etc/systemd/system/${SVC}.service" <<EOF
[Unit]
Description=KIAN Web Panel
After=network.target

[Service]
Environment=KIAN_DB_PATH=${DB_PATH}
Environment=KIAN_ADMIN_USER=${ADMIN_USER}
Environment=KIAN_ADMIN_PASSWORD=${ADMIN_PASS}
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/venv/bin/uvicorn panel.main:app --host 0.0.0.0 --port ${PORT}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable --now "$SVC"
}

sync_users(){
  # pull the real installed users into the panel db so it manages the live server
  "$APP_DIR/venv/bin/python" - <<PY 2>/dev/null || true
import os, sys
sys.path.insert(0, "${APP_DIR}")
os.environ.setdefault("KIAN_DB_PATH", "${DB_PATH}")
from core import db, migrate
from panel import bridge
migrate.migrate_path("${DB_PATH}")
with db.session("${DB_PATH}") as c:
    print(bridge.import_users(c))
PY
}

open_port(){
  if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q active; then
    ufw allow "${PORT}/tcp" >/dev/null 2>&1 || true
  fi
}

print_url(){
  local ip; ip="$(server_ip)"
  echo
  echo "==================================================================="
  say  "پنلِ وب آماده است — Web panel is ready"
  echo "  URL:       http://${ip}:${PORT}/app"
  echo "  Swagger:   http://${ip}:${PORT}/docs"
  echo "  Username:  ${ADMIN_USER:-$(grep -oP 'KIAN_ADMIN_USER=\K.*' /etc/systemd/system/${SVC}.service 2>/dev/null)}"
  [ -n "${ADMIN_PASS:-}" ] && echo "  Password:  ${ADMIN_PASS}"
  echo "==================================================================="
  echo "  ⚠️ پشتِ TLS بگذار (Caddy) و 2FA را در تبِ تنظیمات فعال کن."
}

case "${1:-enable}" in
  enable)
    need_root; fetch_code; setup_venv; ask_admin; install_service; sync_users; open_port; print_url ;;
  url)     ADMIN_PASS=""; print_url ;;
  disable)
    need_root; systemctl disable --now "$SVC" 2>/dev/null || true
    rm -f "/etc/systemd/system/${SVC}.service"; systemctl daemon-reload
    say "panel service removed (code kept in ${APP_DIR})" ;;
  status)  systemctl status "$SVC" --no-pager 2>/dev/null || echo "not installed" ;;
  *) err "usage: kian-panel.sh {enable|url|disable|status}"; exit 2 ;;
esac
