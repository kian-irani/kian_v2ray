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
SB_VERSION="1.12.0"           # pinned, tested (1.12 adds AnyTLS)
HY2_PORT="${KIAN_HY2_PORT:-8443}"      # UDP
TUIC_PORT="${KIAN_TUIC_PORT:-8444}"    # UDP
ANYTLS_PORT="${KIAN_ANYTLS_PORT:-8446}" # TCP — distinct from hy2/tuic & panel(8443/TCP)
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

# Build a per-user credential map from the installer's users.json so each VPN
# user gets their OWN Hysteria2 password + TUIC uuid/password (not one shared
# secret for everyone — the previous behaviour, which broke multi-user installs).
# Falls back to a single "shared" user when users.json is absent.
build_user_creds(){
  local users_json="$ETC_DIR/users.json"
  local map="$SB_DIR/users.json"
  # If a map already exists, keep it stable across re-runs (don't rotate secrets).
  if [ -f "$map" ] && [ "$(jq 'length' "$map" 2>/dev/null || echo 0)" -gt 0 ]; then
    return 0
  fi
  local emails=""
  if [ -f "$users_json" ]; then
    emails="$(jq -r '.users[]?|select(.active!=false)|.email' "$users_json" 2>/dev/null)"
  fi
  [ -z "$emails" ] && emails="shared"
  local arr="[]"
  while IFS= read -r email; do
    [ -z "$email" ] && continue
    local name="${email%@*}"
    local pw uuid apw
    pw="$(openssl rand -hex 16)"; uuid="$(cat /proc/sys/kernel/random/uuid)"
    apw="$(openssl rand -hex 16)"
    arr="$(printf '%s' "$arr" | jq -c --arg n "$name" --arg pw "$pw" --arg u "$uuid" --arg apw "$apw" \
      '. += [{name:$n, hy2_pw:$pw, tuic_uuid:$u, tuic_pw:$pw, anytls_pw:$apw}]')"
  done <<< "$emails"
  printf '%s' "$arr" > "$map"
}

# Render the sing-box config. $1="full" includes the AnyTLS inbound; anything
# else writes only the always-working Hysteria2 + TUIC pair.
_render_config(){
  local with_anytls="$1" sni cert key map
  sni="$(cat "$SB_DIR/sni.txt" 2>/dev/null || echo www.bing.com)"
  cert="$SB_DIR/cert.pem"; key="$SB_DIR/key.pem"; map="$SB_DIR/users.json"
  local hy2_users tuic_users anytls_users
  hy2_users="$(jq -c '[.[]|{password:.hy2_pw}]' "$map")"
  tuic_users="$(jq -c '[.[]|{uuid:.tuic_uuid, password:.tuic_pw}]' "$map")"
  anytls_users="$(jq -c '[.[]|{password:(.anytls_pw // .hy2_pw)}]' "$map")"
  jq -n --argjson hy2u "$hy2_users" --argjson tuicu "$tuic_users" \
        --argjson anytlsu "$anytls_users" --arg anytls_on "$with_anytls" \
        --argjson hy2 "$HY2_PORT" --argjson tuic "$TUIC_PORT" --argjson anytls "$ANYTLS_PORT" \
        --arg cert "$cert" --arg key "$key" '
  {
    log: { level: "warn" },
    inbounds: ([
      { type:"hysteria2", tag:"hy2-in", listen:"::", listen_port:$hy2,
        users:$hy2u,
        tls:{ enabled:true, certificate_path:$cert, key_path:$key } },
      { type:"tuic", tag:"tuic-in", listen:"::", listen_port:$tuic,
        users:$tuicu,
        congestion_control:"bbr",
        tls:{ enabled:true, certificate_path:$cert, key_path:$key } }
    ] + (if $anytls_on=="full" then [
      { type:"anytls", tag:"anytls-in", listen:"::", listen_port:$anytls,
        users:$anytlsu,
        tls:{ enabled:true, certificate_path:$cert, key_path:$key } }
    ] else [] end)),
    outbounds: [ { type:"direct", tag:"direct" } ]
  }' > "$SB_DIR/config.json"
}

# Write the sing-box config. Tries the full set (Hy2 + TUIC + AnyTLS) first;
# if this sing-box build rejects AnyTLS, it falls back to Hy2 + TUIC only so the
# working protocols are NEVER broken (worst case: AnyTLS just isn't offered).
write_singbox_config(){
  _render_config full
  if "$SB_BIN" check -c "$SB_DIR/config.json" 2>/dev/null; then
    echo 1 > "$SB_DIR/anytls_active"
    return 0
  fi
  inf "AnyTLS unsupported by this sing-box build — keeping Hysteria2/TUIC only"
  rm -f "$SB_DIR/anytls_active"
  _render_config minimal
  "$SB_BIN" check -c "$SB_DIR/config.json"
}

gen_config(){
  build_user_creds
  write_singbox_config
  say "sing-box config generated ($(jq 'length' "$SB_DIR/users.json") user(s), hy2:$HY2_PORT tuic:$TUIC_PORT)"
}

# Add one VPN user to the companion (per-user creds) and reload sing-box.
adduser(){
  local name="${1:-}"; [ -n "$name" ] || { err "usage: adduser <name>"; return 1; }
  local map="$SB_DIR/users.json"
  [ -f "$map" ] || { err "companion not initialised — run 'enable' first"; return 1; }
  if [ "$(jq --arg n "$name" '[.[]|select(.name==$n)]|length' "$map")" -gt 0 ]; then
    inf "user $name already in companion — skipped"; return 0
  fi
  local pw uuid apw tmp
  pw="$(openssl rand -hex 16)"; uuid="$(cat /proc/sys/kernel/random/uuid)"; apw="$(openssl rand -hex 16)"
  tmp="$(mktemp)"
  jq --arg n "$name" --arg pw "$pw" --arg u "$uuid" --arg apw "$apw" \
    '. += [{name:$n, hy2_pw:$pw, tuic_uuid:$u, tuic_pw:$pw, anytls_pw:$apw}]' "$map" > "$tmp" && mv "$tmp" "$map"
  write_singbox_config
  systemctl restart "$SVC" 2>/dev/null || true
  say "added $name to Hysteria2/TUIC companion"
}

# Remove one VPN user from the companion and reload sing-box.
deluser(){
  local name="${1:-}"; [ -n "$name" ] || { err "usage: deluser <name>"; return 1; }
  local map="$SB_DIR/users.json"
  [ -f "$map" ] || return 0
  local tmp; tmp="$(mktemp)"
  jq --arg n "$name" 'map(select(.name!=$n))' "$map" > "$tmp" && mv "$tmp" "$map"
  write_singbox_config
  systemctl restart "$SVC" 2>/dev/null || true
  say "removed $name from companion"
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
    # AnyTLS is TCP — only open it if this build actually enabled it.
    [ -f "$SB_DIR/anytls_active" ] && ufw allow "${ANYTLS_PORT}/tcp" >/dev/null 2>&1 || true
    inf "opened ${HY2_PORT}/udp, ${TUIC_PORT}/udp$([ -f "$SB_DIR/anytls_active" ] && echo ", ${ANYTLS_PORT}/tcp") on ufw"
  fi
}

# Per-user share links, labeled #KIAN-<name>-Hysteria2 / -TUIC so the installer's
# per-user subscription builder (grep "#KIAN-<name>-") picks the right one up.
print_links(){
  local ip sni map
  ip="$(curl -fsS4 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')"
  sni="$(cat "$SB_DIR/sni.txt" 2>/dev/null || echo www.bing.com)"
  map="$SB_DIR/users.json"
  [ -f "$map" ] || { err "no user map — run 'enable' first"; return 1; }
  local anytls_on=0; [ -f "$SB_DIR/anytls_active" ] && anytls_on=1
  echo
  jq -r '.[]|[.name,.hy2_pw,.tuic_uuid,.tuic_pw,(.anytls_pw//"")]|@tsv' "$map" \
    | while IFS=$'\t' read -r name hy2pw tuicuuid tuicpw anytlspw; do
        [ -z "$name" ] && continue
        echo "hysteria2://${hy2pw}@${ip}:${HY2_PORT}/?sni=${sni}&insecure=1#KIAN-${name}-Hysteria2"
        echo "tuic://${tuicuuid}:${tuicpw}@${ip}:${TUIC_PORT}/?sni=${sni}&congestion_control=bbr&allow_insecure=1#KIAN-${name}-TUIC"
        # AnyTLS only when this sing-box build accepted it (guarded in write_singbox_config)
        if [ "$anytls_on" = 1 ] && [ -n "$anytlspw" ]; then
          echo "anytls://${anytlspw}@${ip}:${ANYTLS_PORT}/?sni=${sni}&insecure=1#KIAN-${name}-AnyTLS"
        fi
      done
  echo
}

case "${1:-enable}" in
  enable)
    need_root; install_singbox; ensure_cert; gen_config; install_service; open_ports; print_links
    say "Hysteria2 + TUIC enabled. (Reality/SS/TLS untouched.)" ;;
  links)   print_links ;;
  adduser) need_root; shift; adduser "${1:-}" ;;
  deluser) need_root; shift; deluser "${1:-}" ;;
  disable)
    need_root
    systemctl disable --now "$SVC" 2>/dev/null || true
    rm -f "/etc/systemd/system/${SVC}.service"; systemctl daemon-reload
    say "companion disabled (sing-box binary kept)" ;;
  status)  systemctl status "$SVC" --no-pager 2>/dev/null || echo "not installed" ;;
  *) err "usage: kian-protocols.sh {enable|links|adduser <name>|deluser <name>|disable|status}"; exit 2 ;;
esac
