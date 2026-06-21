#!/usr/bin/env bash
# kian-protocols.sh — add Hysteria2 / TUIC (and optional WireGuard) alongside
# the existing Xray install, via a self-contained sing-box companion service.
#
# Xray-core does NOT speak Hysteria2/TUIC, so these run on sing-box. This script
# is OPT-IN and ADDITIVE: it never touches the Xray config or the working
# Reality/SS/TLS path. Run it after a normal install:
#
#   bash kian-protocols.sh enable          # install sing-box + hy2 + tuic
#   bash kian-protocols.sh links           # print client share links
#   bash kian-protocols.sh disable         # stop + remove the companion
#
# It reuses the install's TLS domain/cert when present (TLS mode); otherwise it
# generates a self-signed cert (clients connect with insecure/pinned SHA256).
set -euo pipefail

ETC_DIR="/etc/kian-v2ray"
SB_DIR="$ETC_DIR/singbox"
SB_BIN="/usr/local/bin/sing-box"
SB_VERSION="1.10.1"            # pinned, tested
HY2_PORT="${KIAN_HY2_PORT:-8443}"
TUIC_PORT="${KIAN_TUIC_PORT:-8444}"
SVC="kian-singbox"

say(){ printf '\033[32m✔\033[0m %s\n' "$*"; }
inf(){ printf '\033[34m→\033[0m %s\n' "$*"; }
err(){ printf '\033[31m✘\033[0m %s\n' "$*" >&2; }

need_root(){ [ "$(id -u)" = 0 ] || { err "run as root"; exit 1; }; }

detect_arch(){
  case "$(uname -m)" in
    x86_64|amd64) echo "amd64" ;;
    aarch64|arm64) echo "arm64" ;;
    armv7l) echo "armv7" ;;
    *) err "unsupported arch: $(uname -m)"; exit 1 ;;
  esac
}

install_singbox(){
  if [ -x "$SB_BIN" ] && "$SB_BIN" version 2>/dev/null | grep -q "$SB_VERSION"; then
    inf "sing-box $SB_VERSION already installed"; return 0
  fi
  local arch tar url
  arch="$(detect_arch)"
  tar="sing-box-${SB_VERSION}-linux-${arch}.tar.gz"
  url="https://github.com/SagerNet/sing-box/releases/download/v${SB_VERSION}/${tar}"
  inf "downloading sing-box $SB_VERSION ($arch)"
  local tmp; tmp="$(mktemp -d)"
  curl -fsSL "$url" -o "$tmp/sb.tar.gz"
  tar -xzf "$tmp/sb.tar.gz" -C "$tmp"
  install -m 0755 "$tmp"/sing-box-*/sing-box "$SB_BIN"
  rm -rf "$tmp"
  say "sing-box installed: $("$SB_BIN" version | head -1)"
}

ensure_cert(){
  mkdir -p "$SB_DIR"
  local domain="" cert="$SB_DIR/cert.pem" key="$SB_DIR/key.pem"
  [ -f "$ETC_DIR/tls_domain.txt" ] && domain="$(cat "$ETC_DIR/tls_domain.txt")"
  # Reuse Caddy's cert if the TLS mode obtained one for this domain.
  local caddy_base="/var/lib/caddy/.local/share/caddy/certificates"
  if [ -n "$domain" ] && [ -d "$caddy_base" ]; then
    local found
    found="$(find "$caddy_base" -name "${domain}.crt" 2>/dev/null | head -1 || true)"
    if [ -n "$found" ]; then
      cp "$found" "$cert"; cp "${found%.crt}.key" "$key"
      echo "$domain" > "$SB_DIR/sni.txt"; say "reusing Caddy cert for $domain"; return 0
    fi
  fi
  # Self-signed fallback (clients use insecure=1 / pinned SHA256).
  if [ ! -f "$cert" ]; then
    local sni="${domain:-www.bing.com}"
    openssl req -x509 -newkey rsa:2048 -keyout "$key" -out "$cert" \
      -days 3650 -nodes -subj "/CN=${sni}" >/dev/null 2>&1
    echo "$sni" > "$SB_DIR/sni.txt"
    inf "generated self-signed cert (CN=$sni) — clients use insecure/pinned"
  fi
}

gen_config(){
  local pw uuid sni
  pw="$(openssl rand -hex 16)"; uuid="$(cat /proc/sys/kernel/random/uuid)"
  sni="$(cat "$SB_DIR/sni.txt" 2>/dev/null || echo www.bing.com)"
  echo "$pw"   > "$SB_DIR/hy2_pw.txt"
  echo "$uuid" > "$SB_DIR/tuic_uuid.txt"
  echo "$pw"   > "$SB_DIR/tuic_pw.txt"
  jq -n --arg pw "$pw" --arg uuid "$uuid" \
        --argjson hy2 "$HY2_PORT" --argjson tuic "$TUIC_PORT" \
        --arg cert "$SB_DIR/cert.pem" --arg key "$SB_DIR/key.pem" '
  {
    log: { level: "warn" },
    inbounds: [
      { type:"hysteria2", tag:"hy2-in", listen:"::", listen_port:$hy2,
        users:[{password:$pw}],
        tls:{ enabled:true, certificate_path:$cert, key_path:$key } },
      { type:"tuic", tag:"tuic-in", listen:"::", listen_port:$tuic,
        users:[{uuid:$uuid, password:$pw}],
        congestion_control:"bbr",
        tls:{ enabled:true, certificate_path:$cert, key_path:$key } }
    ],
    outbounds: [ { type:"direct", tag:"direct" } ]
  }' > "$SB_DIR/config.json"
  "$SB_BIN" check -c "$SB_DIR/config.json"
  say "sing-box config generated (hy2:$HY2_PORT tuic:$TUIC_PORT)"
}

install_service(){
  cat > "/etc/systemd/system/${SVC}.service" <<EOF
[Unit]
Description=KIAN sing-box (Hysteria2/TUIC companion)
After=network.target

[Service]
ExecStart=${SB_BIN} run -c ${SB_DIR}/config.json
Restart=on-failure
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable --now "$SVC"
  say "service ${SVC} started"
}

open_ports(){
  if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q active; then
    ufw allow "${HY2_PORT}/udp"  >/dev/null 2>&1 || true
    ufw allow "${TUIC_PORT}/udp" >/dev/null 2>&1 || true
    inf "opened ${HY2_PORT}/udp, ${TUIC_PORT}/udp on ufw"
  fi
}

print_links(){
  local ip sni pw uuid
  ip="$(curl -fsS4 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')"
  sni="$(cat "$SB_DIR/sni.txt" 2>/dev/null || echo www.bing.com)"
  pw="$(cat "$SB_DIR/hy2_pw.txt")"; uuid="$(cat "$SB_DIR/tuic_uuid.txt")"
  echo
  echo "Hysteria2:  hysteria2://${pw}@${ip}:${HY2_PORT}/?sni=${sni}&insecure=1#KIAN-Hysteria2"
  echo "TUIC v5:    tuic://${uuid}:${pw}@${ip}:${TUIC_PORT}/?sni=${sni}&congestion_control=bbr&allow_insecure=1#KIAN-TUIC"
  echo
}

case "${1:-enable}" in
  enable)
    need_root; install_singbox; ensure_cert; gen_config; install_service; open_ports; print_links
    say "Hysteria2 + TUIC enabled. (Reality/SS/TLS untouched.)" ;;
  links)   print_links ;;
  disable)
    need_root
    systemctl disable --now "$SVC" 2>/dev/null || true
    rm -f "/etc/systemd/system/${SVC}.service"; systemctl daemon-reload
    say "companion disabled (sing-box binary kept)" ;;
  status)  systemctl status "$SVC" --no-pager 2>/dev/null || echo "not installed" ;;
  *) err "usage: kian-protocols.sh {enable|links|disable|status}"; exit 2 ;;
esac
