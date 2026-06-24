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
STLS_PORT="${KIAN_STLS_PORT:-8447}"     # TCP — ShadowTLS v3
SVC="kian-singbox"
PORTS_FILE="$SB_DIR/ports.env"
# Reuse ports resolved on a previous run so `links`/`adduser`/`status` (separate
# invocations) agree with the running service.
if [ -f "$PORTS_FILE" ]; then
  while IFS='=' read -r k v; do
    case "$k" in
      KIAN_HY2_PORT)    HY2_PORT="$v" ;;
      KIAN_TUIC_PORT)   TUIC_PORT="$v" ;;
      KIAN_ANYTLS_PORT) ANYTLS_PORT="$v" ;;
      KIAN_STLS_PORT)   STLS_PORT="$v" ;;
    esac
  done < "$PORTS_FILE"
fi

_udp_busy(){ ss -uln 2>/dev/null | awk '{print $5}' | grep -qE "[:.]${1}\$"; }
_tcp_busy(){ ss -tln 2>/dev/null | awk '{print $5}' | grep -qE "[:.]${1}\$"; }
# Pick a free port near a preferred one. $1=udp|tcp $2=preferred.
_pick_free(){
  local proto="$1" pref="$2" i cand
  for i in 0 1 2 3 4 5 6 7 8; do
    cand=$(( pref + i ))
    if [ "$proto" = udp ]; then _udp_busy "$cand" || { echo "$cand"; return; }
    else _tcp_busy "$cand" || { echo "$cand"; return; }; fi
  done
  echo $(( (RANDOM % 20000) + 30000 ))
}
# Move companion ports off anything already listening, then persist the choice
# so the new protocols never collide with Reality/SS/panel or each other.
resolve_ports(){
  mkdir -p "$SB_DIR"
  command -v ss >/dev/null 2>&1 || return 0
  _udp_busy "$HY2_PORT"    && HY2_PORT="$(_pick_free udp "$HY2_PORT")"
  _udp_busy "$TUIC_PORT"   && TUIC_PORT="$(_pick_free udp "$TUIC_PORT")"
  [ "$TUIC_PORT" = "$HY2_PORT" ] && TUIC_PORT="$(_pick_free udp $(( HY2_PORT + 1 )))"
  _tcp_busy "$ANYTLS_PORT"  && ANYTLS_PORT="$(_pick_free tcp "$ANYTLS_PORT")"
  _tcp_busy "$STLS_PORT"    && STLS_PORT="$(_pick_free tcp "$STLS_PORT")"
  [ "$STLS_PORT" = "$ANYTLS_PORT" ] && STLS_PORT="$(_pick_free tcp $(( ANYTLS_PORT + 1 )))"
  cat > "$PORTS_FILE" <<EOF
KIAN_HY2_PORT=$HY2_PORT
KIAN_TUIC_PORT=$TUIC_PORT
KIAN_ANYTLS_PORT=$ANYTLS_PORT
KIAN_STLS_PORT=$STLS_PORT
EOF
  inf "companion ports → hy2:$HY2_PORT/udp tuic:$TUIC_PORT/udp anytls:$ANYTLS_PORT/tcp shadowtls:$STLS_PORT/tcp"
}

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
    local pw uuid apw spw
    pw="$(openssl rand -hex 16)"; uuid="$(cat /proc/sys/kernel/random/uuid)"
    apw="$(openssl rand -hex 16)"; spw="$(openssl rand -hex 16)"
    arr="$(printf '%s' "$arr" | jq -c --arg n "$name" --arg pw "$pw" --arg u "$uuid" --arg apw "$apw" --arg spw "$spw" \
      '. += [{name:$n, hy2_pw:$pw, tuic_uuid:$u, tuic_pw:$pw, anytls_pw:$apw, stls_pw:$spw}]')"
  done <<< "$emails"
  printf '%s' "$arr" > "$map"
  # Server-wide Shadowsocks PSK behind ShadowTLS (16 bytes b64 for aes-128-gcm).
  [ -f "$SB_DIR/ss_psk.txt" ] || openssl rand -base64 16 > "$SB_DIR/ss_psk.txt"
}

# Render the sing-box config. Flags: $1=anytls(1/0) $2=shadowtls(1/0).
# Hysteria2 + TUIC are always present; AnyTLS and ShadowTLS v3 are layered on
# when requested (and only kept if `sing-box check` accepts them — see the guard).
_render_config(){
  local with_anytls="$1" with_stls="$2" sni cert key map psk
  sni="$(cat "$SB_DIR/sni.txt" 2>/dev/null || echo www.bing.com)"
  cert="$SB_DIR/cert.pem"; key="$SB_DIR/key.pem"; map="$SB_DIR/users.json"
  psk="$(cat "$SB_DIR/ss_psk.txt" 2>/dev/null || echo)"
  local hy2_users tuic_users anytls_users stls_users
  hy2_users="$(jq -c '[.[]|{password:.hy2_pw}]' "$map")"
  tuic_users="$(jq -c '[.[]|{uuid:.tuic_uuid, password:.tuic_pw}]' "$map")"
  anytls_users="$(jq -c '[.[]|{password:(.anytls_pw // .hy2_pw)}]' "$map")"
  stls_users="$(jq -c '[.[]|{name:.name, password:(.stls_pw // .hy2_pw)}]' "$map")"
  jq -n --argjson hy2u "$hy2_users" --argjson tuicu "$tuic_users" \
        --argjson anytlsu "$anytls_users" --argjson stlsu "$stls_users" \
        --arg anytls_on "$with_anytls" --arg stls_on "$with_stls" \
        --argjson hy2 "$HY2_PORT" --argjson tuic "$TUIC_PORT" \
        --argjson anytls "$ANYTLS_PORT" --argjson stls "$STLS_PORT" \
        --arg cert "$cert" --arg key "$key" --arg sni "$sni" --arg psk "$psk" '
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
    ]
    + (if $anytls_on=="1" then [
      { type:"anytls", tag:"anytls-in", listen:"::", listen_port:$anytls,
        users:$anytlsu,
        tls:{ enabled:true, certificate_path:$cert, key_path:$key } }
    ] else [] end)
    + (if $stls_on=="1" then [
      { type:"shadowtls", tag:"stls-in", listen:"::", listen_port:$stls,
        version:3, users:$stlsu,
        handshake:{ server:$sni, server_port:443 },
        detour:"stls-ss-in" },
      { type:"shadowsocks", tag:"stls-ss-in",
        method:"2022-blake3-aes-128-gcm", password:$psk }
    ] else [] end)),
    outbounds: [ { type:"direct", tag:"direct" } ]
  }' > "$SB_DIR/config.json"
}

# Write the sing-box config, layering AnyTLS then ShadowTLS on top of the always
# -working Hysteria2 + TUIC pair. If this sing-box build rejects a layer, that
# layer is dropped and we re-check — so the working protocols can NEVER be broken
# by a new one (worst case: the new protocol simply isn't offered).
write_singbox_config(){
  # 1) everything
  _render_config 1 1
  if "$SB_BIN" check -c "$SB_DIR/config.json" 2>/dev/null; then
    echo 1 > "$SB_DIR/anytls_active"; echo 1 > "$SB_DIR/shadowtls_active"; return 0
  fi
  # 2) drop ShadowTLS, keep AnyTLS
  rm -f "$SB_DIR/shadowtls_active"
  _render_config 1 0
  if "$SB_BIN" check -c "$SB_DIR/config.json" 2>/dev/null; then
    echo 1 > "$SB_DIR/anytls_active"
    inf "ShadowTLS unsupported by this sing-box build — kept Hy2/TUIC/AnyTLS"
    return 0
  fi
  # 3) drop AnyTLS too — minimal, always-working pair
  rm -f "$SB_DIR/anytls_active"
  _render_config 0 0
  inf "AnyTLS/ShadowTLS unsupported — keeping Hysteria2/TUIC only"
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
  local pw uuid apw spw tmp
  pw="$(openssl rand -hex 16)"; uuid="$(cat /proc/sys/kernel/random/uuid)"
  apw="$(openssl rand -hex 16)"; spw="$(openssl rand -hex 16)"
  tmp="$(mktemp)"
  jq --arg n "$name" --arg pw "$pw" --arg u "$uuid" --arg apw "$apw" --arg spw "$spw" \
    '. += [{name:$n, hy2_pw:$pw, tuic_uuid:$u, tuic_pw:$pw, anytls_pw:$apw, stls_pw:$spw}]' "$map" > "$tmp" && mv "$tmp" "$map"
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
    # AnyTLS / ShadowTLS are TCP — only open when that layer is actually active.
    [ -f "$SB_DIR/anytls_active" ]    && ufw allow "${ANYTLS_PORT}/tcp" >/dev/null 2>&1 || true
    [ -f "$SB_DIR/shadowtls_active" ] && ufw allow "${STLS_PORT}/tcp"   >/dev/null 2>&1 || true
    inf "opened ${HY2_PORT}/udp, ${TUIC_PORT}/udp$([ -f "$SB_DIR/anytls_active" ] && echo ", ${ANYTLS_PORT}/tcp")$([ -f "$SB_DIR/shadowtls_active" ] && echo ", ${STLS_PORT}/tcp") on ufw"
  fi
}

# Per-user share links, labeled #KIAN-<name>-<Proto> so the installer's per-user
# subscription builder (grep "#KIAN-<name>-") picks each user's links up.
print_links(){
  local ip sni map psk
  ip="$(curl -fsS4 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')"
  sni="$(cat "$SB_DIR/sni.txt" 2>/dev/null || echo www.bing.com)"
  map="$SB_DIR/users.json"; psk="$(cat "$SB_DIR/ss_psk.txt" 2>/dev/null || echo)"
  [ -f "$map" ] || { err "no user map — run 'enable' first"; return 1; }
  local anytls_on=0 stls_on=0
  [ -f "$SB_DIR/anytls_active" ]    && anytls_on=1
  [ -f "$SB_DIR/shadowtls_active" ] && stls_on=1
  # ShadowTLS share URI carries the inner Shadowsocks (method:psk, base64) so a
  # sing-box/Hiddify client can reconstruct the full chain.
  local ss_b64; ss_b64="$(printf '%s' "2022-blake3-aes-128-gcm:${psk}" | base64 -w0 2>/dev/null || printf '')"
  echo
  jq -r '.[]|[.name,.hy2_pw,.tuic_uuid,.tuic_pw,(.anytls_pw//""),(.stls_pw//"")]|@tsv' "$map" \
    | while IFS=$'\t' read -r name hy2pw tuicuuid tuicpw anytlspw stlspw; do
        [ -z "$name" ] && continue
        echo "hysteria2://${hy2pw}@${ip}:${HY2_PORT}/?sni=${sni}&insecure=1#KIAN-${name}-Hysteria2"
        echo "tuic://${tuicuuid}:${tuicpw}@${ip}:${TUIC_PORT}/?sni=${sni}&congestion_control=bbr&allow_insecure=1#KIAN-${name}-TUIC"
        if [ "$anytls_on" = 1 ] && [ -n "$anytlspw" ]; then
          echo "anytls://${anytlspw}@${ip}:${ANYTLS_PORT}/?sni=${sni}&insecure=1#KIAN-${name}-AnyTLS"
        fi
        if [ "$stls_on" = 1 ] && [ -n "$stlspw" ]; then
          # ss:// over shadowtls (sing-box plugin form): shadow-tls v3 + host/pw.
          echo "ss://${ss_b64}@${ip}:${STLS_PORT}?shadow-tls=v3&shadow-tls-password=${stlspw}&shadow-tls-sni=${sni}#KIAN-${name}-ShadowTLS"
        fi
      done
  echo
}

case "${1:-enable}" in
  enable)
    need_root; install_singbox; ensure_cert; resolve_ports; gen_config; install_service; open_ports; print_links
    say "Hysteria2 + TUIC (+AnyTLS if supported) enabled. (Reality/SS/TLS untouched.)" ;;
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
