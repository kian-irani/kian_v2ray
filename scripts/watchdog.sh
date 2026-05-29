#!/usr/bin/env bash
# ============================================================================
#  KIAN V2Ray — watchdog  (هر ۱۰ دقیقه از طریق cron)
#   • اطمینان از اجرای کانتینر Xray
#   • اطمینان از اتصال WARP (در صورت نصب)
#   • محاسبه‌ی مصرف هر کاربر و اعمال محدودیت حجم/انقضا
#  بدون آرگومان اجرا می‌شود؛ خروجی به /var/log/kian-xray/watchdog.log می‌رود.
# ============================================================================
set -uo pipefail

CONTAINER="kian-xray"
WARP_PORT=40000
ETC_DIR="/etc/kian-v2ray"
XRAY_DIR="/etc/kian-v2ray"
USERS_FILE="$ETC_DIR/users.json"
CONFIG="$XRAY_DIR/config.json"
API_FILE="$ETC_DIR/api.txt"
if [ -f "$API_FILE" ]; then API="$(cat "$API_FILE" 2>/dev/null)"; fi
[ -z "${API:-}" ] && API="127.0.0.1:$(jq -r '(.inbounds[]|select(.tag=="api")|.port)//10085' "$CONFIG" 2>/dev/null || echo 10085)"
ts(){ date -u +%FT%TZ; }
log(){ echo "[$(ts)] $*"; }

command -v jq >/dev/null 2>&1 || { log "jq نیست — خروج"; exit 0; }
[ -f "$USERS_FILE" ] || { log "users.json نیست — خروج"; exit 0; }

# --- ۱) کانتینر Xray باید بالا باشد ---------------------------------------
if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
  log "Xray پایین است — restart"
  docker start "$CONTAINER" >/dev/null 2>&1 || docker restart "$CONTAINER" >/dev/null 2>&1 || true
fi

# --- ۲) سلامت WARP (اگر نصب باشد) -----------------------------------------
if command -v warp-cli >/dev/null 2>&1; then
  if ! curl -fsS --max-time 8 --socks5 "127.0.0.1:$WARP_PORT" https://1.1.1.1/cdn-cgi/trace 2>/dev/null | grep -q 'warp=on'; then
    log "WARP قطع است — تلاش برای اتصال مجدد"
    warp-cli --accept-tos connect >/dev/null 2>&1 || { systemctl restart warp-svc >/dev/null 2>&1; sleep 3; warp-cli --accept-tos connect >/dev/null 2>&1; }
  fi
fi

# --- ۳) خواندن آمار مصرف از Xray stats API --------------------------------
query_stats(){
  local img out
  img="$(cat "$ETC_DIR/image.txt" 2>/dev/null || echo ghcr.io/xtls/xray-core:latest)"
  out="$(docker exec "$CONTAINER" xray api statsquery --server="$API" -reset 2>/dev/null)" && [ -n "$out" ] && { echo "$out"; return; }
  out="$(docker run --rm --network host --entrypoint xray "$img" api statsquery --server="$API" -reset 2>/dev/null)" && [ -n "$out" ] && { echo "$out"; return; }
  echo '{}'
}
STATS="$(query_stats)"
echo "$STATS" | jq -e . >/dev/null 2>&1 || STATS='{}'

NOW=$(date -u +%s)
BEFORE="$(jq -c '[.users[]|{email:.email,active:.active}]' "$USERS_FILE" 2>/dev/null || echo '[]')"
TMP="$(mktemp)"

# همه‌ی محاسبات در یک برنامه‌ی jq: افزودن delta به used_bytes و اعمال حجم/انقضا
jq --argjson stats "$STATS" --argjson now "$NOW" '
  def delta($email):
    [ ($stats.stat // [])[]
      | select(.name | startswith("user>>>" + $email + ">>>"))
      | (.value // 0 | tonumber) ] | add // 0;
  .users |= map(
      (.used_bytes + delta(.email)) as $used
    | .used_bytes = $used
    | (if (.quota_bytes > 0 and $used >= .quota_bytes) then .active = false else . end)
    | (if (.expires_at != null and .expires_at != ""
           and ((.expires_at | sub("\\.[0-9]+Z$";"Z") | fromdateiso8601) <= $now))
        then .active = false else . end)
  )
' "$USERS_FILE" > "$TMP" 2>/dev/null

if jq -e . "$TMP" >/dev/null 2>&1; then
  mv "$TMP" "$USERS_FILE"; chmod 600 "$USERS_FILE"
else
  rm -f "$TMP"; log "به‌روزرسانی users.json ناموفق — رد شد"; exit 0
fi

AFTER="$(jq -c '[.users[]|{email:.email,active:.active}]' "$USERS_FILE")"

# --- ۴) اگر وضعیت فعال‌بودن کسی تغییر کرد → بازسازی clients و restart -------
if [ "$BEFORE" != "$AFTER" ]; then
  log "تغییر وضعیت کاربر(ان) — بازسازی config و restart"
  ACTIVE="$(jq -c '[.users[] | select(.active==true) | {id:.id, email:.email, flow:"xtls-rprx-vision"}]' "$USERS_FILE")"
  CFGTMP="$(mktemp)"
  jq --argjson cl "$ACTIVE" '
    .inbounds |= map(
      if ((.tag // "") | startswith("reality-")) then .settings.clients = $cl else . end
    )' "$XRAY_DIR/config.json" > "$CFGTMP" 2>/dev/null
  if jq -e . "$CFGTMP" >/dev/null 2>&1; then
    mv "$CFGTMP" "$XRAY_DIR/config.json"
    docker restart "$CONTAINER" >/dev/null 2>&1 || true
    log "config بازسازی و Xray restart شد"
  else
    rm -f "$CFGTMP"; log "بازسازی config ناموفق"
  fi
fi
exit 0
