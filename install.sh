#!/usr/bin/env bash
# ============================================================================
#  KIAN V2Ray — نصب‌کننده‌ی خودکار (فاز ۱: VLESS Reality + WARP)
#  ریپو:  https://github.com/KIAN-IRANI/kian_v2ray
#  صفحه:  https://kian-irani.github.io/kian_v2ray/
#
#  ویژگی‌ها:
#   • مقاوم در برابر قطع شدن SSH (با setsid در پس‌زمینه اجرا می‌شود)
#   • idempotent — اگر وسط کار قطع شد، فقط دوباره همان دستور را اجرا کن
#   • کلیدها در مرورگر ساخته می‌شوند؛ این اسکریپت فقط آن‌ها را روی سرور می‌نشاند
#   • هیچ توکن/رمزی داخل این فایل نیست — کاملاً عمومی و امن
#
#  استفاده (از صفحه تعاملی کپی می‌شود):
#     export KIAN_PAYLOAD='...base64...'
#     curl -fsSL <raw>/install.sh -o /tmp/kian.sh && bash /tmp/kian.sh
#
#  دستورهای دیگر:
#     bash /tmp/kian.sh status     ← وضعیت نصب/سرویس
#     bash /tmp/kian.sh logs       ← لاگ زنده‌ی نصب
# ============================================================================
set -Eeuo pipefail

# ---------------------------------------------------------------------------
RAW_BASE="https://raw.githubusercontent.com/KIAN-IRANI/kian_v2ray/main"
XRAY_IMAGE_PINNED="ghcr.io/xtls/xray-core:26.5.9"   # نسخه‌ی پین‌شده (CalVer)
XRAY_IMAGE_FALLBACK="ghcr.io/xtls/xray-core:latest" # فقط اگر پین‌شده pull نشد
CONTAINER="kian-xray"
WARP_PORT=40000

ETC_DIR="/etc/kian-v2ray"          # users.json + payload + info + config.json
XRAY_DIR="/etc/kian-v2ray"         # config.json (ایزوله — به /etc/xray دست نمی‌زند)
LOG_DIR="/var/log/kian-xray"       # لاگ‌های Xray (ایزوله از پنل‌های دیگر)
WORK_DIR="/opt/kian-v2ray"         # نصب‌کننده + لاگ نصب + state
INSTALL_LOG="$WORK_DIR/install.log"
STATE_FILE="$WORK_DIR/state"
LOCK_FILE="$WORK_DIR/install.lock"

C_G='\033[1;32m'; C_Y='\033[1;33m'; C_R='\033[1;31m'; C_B='\033[1;36m'; C_N='\033[0m'
say(){  printf "${C_G}✔${C_N} %s\n" "$*"; }
inf(){  printf "${C_B}→${C_N} %s\n" "$*"; }
warn(){ printf "${C_Y}⚠${C_N} %s\n" "$*"; }
err(){  printf "${C_R}✘${C_N} %s\n" "$*" >&2; }
trap 'err "خطا در خط $LINENO — جزئیات: tail -n 40 '"$INSTALL_LOG"'"' ERR

mkdir -p "$WORK_DIR"
done_step(){ grep -qxF "$1" "$STATE_FILE" 2>/dev/null; }
mark_step(){ echo "$1" >> "$STATE_FILE"; }

# ===========================================================================
#  زیرفرمان‌ها: status / logs  (بدون نیاز به payload)
# ===========================================================================
cmd_status(){
  printf "\n${C_B}━━━ KIAN V2Ray — وضعیت ━━━${C_N}\n\n"
  if [ -f "$LOCK_FILE" ] && kill -0 "$(cat "$LOCK_FILE" 2>/dev/null)" 2>/dev/null; then
    warn "نصب هنوز در حال اجراست — لاگ زنده:  bash $0 logs"
  fi
  if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
    say "Xray در حال اجراست (container: $CONTAINER)"
    docker ps --filter "name=$CONTAINER" --format '   آپ‌تایم: {{.Status}}' 2>/dev/null || true
  else
    err "Xray اجرا نمی‌شود"
  fi
  if command -v warp-cli >/dev/null 2>&1; then
    local ws; ws=$(warp-cli --accept-tos status 2>/dev/null | head -1 || true)
    if echo "$ws" | grep -qi connected; then say "WARP: متصل"; else warn "WARP: ${ws:-نامشخص}"; fi
  else
    inf "WARP نصب نشده (حالت مستقیم)"
  fi
  if command -v ss >/dev/null 2>&1; then
    printf "\n${C_B}پورت‌های شنونده:${C_N}\n"
    ss -tlnp 2>/dev/null | awk 'NR>1{print "   "$4}' | grep -E ':(8[0-9]{3}|44[0-9]|443)$' | sort -u || true
  fi
  printf "\n${C_B}کانفیگ‌ها:${C_N}  kian-v2ray configs\n\n"
}
cmd_logs(){ [ -f "$INSTALL_LOG" ] || { err "هنوز لاگی نیست."; exit 1; }; tail -n 60 -f "$INSTALL_LOG"; }

case "${1:-}" in
  status) cmd_status; exit 0 ;;
  logs)   cmd_logs;   exit 0 ;;
  ""|install) : ;;
  *) if command -v kian-v2ray >/dev/null 2>&1; then exec kian-v2ray "$@"; fi
     err "زیرفرمان ناشناخته: $1"; exit 1 ;;
esac

[ "$(id -u)" -eq 0 ] || { err "باید با root اجرا شود (sudo)."; exit 1; }

# ===========================================================================
#  payload را بخوان (env یا فایل ذخیره‌شده)
# ===========================================================================
mkdir -p "$ETC_DIR"
[ -n "${KIAN_PAYLOAD:-}" ] && printf '%s' "$KIAN_PAYLOAD" > "$ETC_DIR/payload.b64"
if [ ! -s "$ETC_DIR/payload.b64" ]; then
  err "هیچ payload ای پیدا نشد."
  err "دستور را از صفحه تعاملی کپی کن:  https://kian-irani.github.io/kian_v2ray/"
  exit 1
fi

# ===========================================================================
#  مرحله‌ی ۰ — اجرای مجدد در پس‌زمینه (مقاوم در برابر قطع SSH)
# ===========================================================================
if [ -z "${KIAN_DETACHED:-}" ]; then
  if [ -f "$LOCK_FILE" ] && kill -0 "$(cat "$LOCK_FILE" 2>/dev/null)" 2>/dev/null; then
    warn "نصب از قبل در حال اجراست."
    inf  "وضعیت:  bash $0 status   |   لاگ:  bash $0 logs"
    exit 0
  fi
  cp -f "$0" "$WORK_DIR/install.sh" 2>/dev/null || curl -fsSL "$RAW_BASE/install.sh" -o "$WORK_DIR/install.sh"
  chmod +x "$WORK_DIR/install.sh"
  printf "\n${C_B}🚀 نصب KIAN V2Ray در پس‌زمینه شروع شد${C_N}\n"
  printf "   (می‌توانی SSH را ببندی — نصب ادامه پیدا می‌کند)\n\n"
  setsid env KIAN_DETACHED=1 bash "$WORK_DIR/install.sh" >"$INSTALL_LOG" 2>&1 </dev/null &
  sleep 2
  inf "لاگ زنده:        bash $WORK_DIR/install.sh logs"
  inf "وضعیت سرویس:     kian-v2ray status   (یا: bash $WORK_DIR/install.sh status)"
  inf "گرفتن کانفیگ‌ها:  kian-v2ray configs   (پس از پایان نصب)"
  printf "\n${C_Y}نصب معمولاً ۲ تا ۵ دقیقه طول می‌کشد.${C_N}\n\n"
  exit 0
fi

# ===========================================================================
#  اجرای واقعی نصب (پس‌زمینه)
# ===========================================================================
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT
echo "=== KIAN V2Ray install — $(date -u +%FT%TZ) ==="

PAYLOAD_JSON="$(base64 -d < "$ETC_DIR/payload.b64")"
_grab(){ printf '%s' "$PAYLOAD_JSON" | tr -d '\n' | grep -oE "\"$1\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | head -1 | sed -E "s/.*:[[:space:]]*\"([^\"]*)\"/\1/"; }
_bool(){ printf '%s' "$PAYLOAD_JSON" | tr -d '\n' | grep -oE "\"$1\"[[:space:]]*:[[:space:]]*(true|false)" | head -1 | grep -oE '(true|false)'; }
WARP_NEEDED="$(_bool warp_needed || echo false)"
SERVER_IP="$(_grab server_ip || true)"

# --- مرحله ۱: پیش‌نیازها ---------------------------------------------------
if ! done_step deps; then
  inf "نصب پیش‌نیازها (curl, jq, ufw, ...)"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y -q
  apt-get install -y -q curl jq ca-certificates gnupg lsb-release ufw iproute2 coreutils qrencode
  mark_step deps; say "پیش‌نیازها نصب شد"
else inf "پیش‌نیازها از قبل نصب — رد شد"; fi

# --- مرحله ۲: Docker -------------------------------------------------------
if ! done_step docker; then
  if command -v docker >/dev/null 2>&1; then inf "Docker از قبل نصب است"
  else inf "نصب Docker..."; curl -fsSL https://get.docker.com | sh; fi
  systemctl enable --now docker >/dev/null 2>&1 || true
  mark_step docker; say "Docker آماده است"
else inf "Docker از قبل آماده — رد شد"; fi

# --- مرحله ۳: WARP (فقط در صورت نیاز) --------------------------------------
# fallback خودکار: اگر WARP وصل نشد، قوانینِ routing که به warp می‌روند موقتاً به
# direct تغییر می‌کنند تا کاربرِ کانفیگ‌های warp بی‌نت نماند. هنگام برگشتِ WARP
# دوباره به warp برمی‌گردند. وضعیت در warp_fallback.txt نگه‌داری می‌شود.
warp_fallback(){ # $1 = on|off
  local cfg="$XRAY_DIR/config.json" flag="$ETC_DIR/warp_fallback.txt" tmp
  [ -f "$cfg" ] || return 0
  command -v jq >/dev/null 2>&1 || return 0
  if [ "$1" = "on" ]; then
    # فقط اگر outbound warp اصلاً وجود دارد و قبلاً fallback نشده‌ایم
    jq -e '.outbounds[]?|select(.tag=="warp")' "$cfg" >/dev/null 2>&1 || return 0
    [ "$(cat "$flag" 2>/dev/null)" = "on" ] && return 0
    tmp="$(mktemp)"
    jq '(.routing.rules[]?|select(.outboundTag=="warp")|.outboundTag)="direct"' "$cfg" > "$tmp" \
      && jq -e . "$tmp" >/dev/null 2>&1 && mv "$tmp" "$cfg" || rm -f "$tmp"
    echo on > "$flag"
    docker restart "$CONTAINER" >/dev/null 2>&1 || true
    warn "fallback فعال شد: ترافیک warp موقتاً مستقیم می‌رود (در status اطلاع داده می‌شود)"
  else
    [ "$(cat "$flag" 2>/dev/null)" = "on" ] || { echo off > "$flag"; return 0; }
    # برگرداندن: قوانینِ مربوط به inboundهای reality-warp-* را به warp بازگردان
    tmp="$(mktemp)"
    jq '(.routing.rules[]?|select((.inboundTag//[])|any(test("^reality-warp-")))|.outboundTag)="warp"' "$cfg" > "$tmp" \
      && jq -e . "$tmp" >/dev/null 2>&1 && mv "$tmp" "$cfg" || rm -f "$tmp"
    echo off > "$flag"
    docker restart "$CONTAINER" >/dev/null 2>&1 || true
    say "WARP برگشت: ترافیک warp دوباره از WARP می‌رود"
  fi
}

install_warp(){
  if command -v warp-cli >/dev/null 2>&1; then inf "WARP از قبل نصب است"
  else
    inf "نصب Cloudflare WARP..."
    curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | gpg --yes --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
    local codename; codename="$(lsb_release -cs 2>/dev/null || echo jammy)"
    echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $codename main" > /etc/apt/sources.list.d/cloudflare-client.list
    if ! { apt-get update -y -q && apt-get install -y -q cloudflare-warp; }; then
      warn "codename=$codename ناموفق — تلاش با jammy"
      echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ jammy main" > /etc/apt/sources.list.d/cloudflare-client.list
      apt-get update -y -q && apt-get install -y -q cloudflare-warp
    fi
  fi
  systemctl enable --now warp-svc >/dev/null 2>&1 || true
  sleep 3
  # --- ثبت‌نام مطمئن‌تر: فقط اگر هنوز ثبت نشده، و بدون اتکای صرف به `yes |` ---
  if ! warp-cli --accept-tos registration show >/dev/null 2>&1 \
     && ! warp-cli --accept-tos status 2>/dev/null | grep -qiE 'connected|registration ok|registered'; then
    inf "ثبت‌نام WARP..."
    for r in 1 2 3; do
      warp-cli --accept-tos registration new </dev/null >/dev/null 2>&1 \
        || warp-cli --accept-tos register </dev/null >/dev/null 2>&1 \
        || (yes | warp-cli --accept-tos registration new) >/dev/null 2>&1 || true
      warp-cli --accept-tos registration show >/dev/null 2>&1 && break
      sleep 3
    done
  fi
  warp-cli --accept-tos mode proxy >/dev/null 2>&1 || warp-cli --accept-tos set-mode proxy >/dev/null 2>&1 || true
  warp-cli --accept-tos proxy port "$WARP_PORT" >/dev/null 2>&1 || warp-cli --accept-tos set-proxy-port "$WARP_PORT" >/dev/null 2>&1 || true

  # --- تلاش با هر پروتکل: اول WireGuard (پایدارتر)، بعد MASQUE ---
  _warp_try(){ # $1=protocol
    warp-cli --accept-tos tunnel protocol set "$1" >/dev/null 2>&1 \
      || warp-cli --accept-tos set-tunnel-protocol "$1" >/dev/null 2>&1 || true
    warp-cli --accept-tos disconnect >/dev/null 2>&1 || true
    sleep 1
    warp-cli --accept-tos connect >/dev/null 2>&1 || true
    local k
    for k in 1 2 3 4 5; do
      sleep 4
      if curl -fsS --max-time 8 --socks5 "127.0.0.1:$WARP_PORT" https://1.1.1.1/cdn-cgi/trace 2>/dev/null | grep -q 'warp=on'; then return 0; fi
      warp-cli --accept-tos connect >/dev/null 2>&1 || true
    done
    return 1
  }
  local ok=0 proto=""
  for proto in WireGuard MASQUE; do
    inf "اتصال WARP با پروتکل $proto..."
    if _warp_try "$proto"; then ok=1; echo "$proto" > "$ETC_DIR/warp_proto.txt"; break; fi
    warn "WARP با $proto وصل نشد — تلاش با پروتکل بعدی"
  done
  if [ "$ok" = 1 ]; then
    say "WARP متصل شد (socks5 :$WARP_PORT — پروتکل $(cat "$ETC_DIR/warp_proto.txt" 2>/dev/null))"
    warp_fallback off || true
  else
    warn "WARP وصل نشد — فعال‌سازی fallback موقت به direct تا کاربر بی‌نت نماند"
    warp_fallback on || true
  fi
}
if [ "$WARP_NEEDED" = "true" ]; then
  if ! done_step warp; then install_warp; mark_step warp; fi
else inf "WARP لازم نیست (همه کانفیگ‌ها مستقیم) — رد شد"; fi

# --- مرحله ۴: نوشتن config.json و users.json (ساخته‌شده در مرورگر) ----------
inf "نوشتن config.json و users.json"
mkdir -p "$XRAY_DIR" "$LOG_DIR"
chmod 777 "$LOG_DIR"   # کانتینر Xray با کاربر غیر-root → نیاز به نوشتن لاگ
printf '%s' "$PAYLOAD_JSON" | jq -r '.config_b64' | base64 -d > "$XRAY_DIR/config.json"
jq -e . "$XRAY_DIR/config.json" >/dev/null

# --- مشکل ۰.۱: پورت API (آمار) نباید با 3x-ui/Marzban روی همین سرور تداخل کند ---
# پورت API از config خوانده می‌شود؛ اگر اشغال بود، خودکار اولین پورت آزاد بعدی انتخاب
# و مستقیم در config.json تزریق می‌شود (auto-fix — کاربر کاری نمی‌کند).
API_PORT="$(jq -r '(.inbounds[] | select(.tag=="api") | .port) // 10085' "$XRAY_DIR/config.json")"
_port_busy(){ ss -tln 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${1}\$"; }
if _port_busy "$API_PORT"; then
  warn "پورت API ($API_PORT) اشغال است — احتمالاً پنل دیگری (3x-ui/Marzban) فعال است"
  NEWAPI="$API_PORT"
  for _try in $(seq 1 200); do
    NEWAPI=$(( (RANDOM % 30000) + 20000 ))
    _port_busy "$NEWAPI" && continue
    printf '%s\n' "$PAYLOAD_JSON" | jq -r '.ports[]? // empty' | grep -qx "$NEWAPI" && continue
    break
  done
  inf "پورت API به $NEWAPI تغییر کرد (auto-fix)"
  tmpc="$(mktemp)"
  jq --argjson old "$API_PORT" --argjson new "$NEWAPI" \
     '(.inbounds[] | select(.tag=="api") | .port) |= $new' \
     "$XRAY_DIR/config.json" > "$tmpc" && mv "$tmpc" "$XRAY_DIR/config.json"
  jq -e . "$XRAY_DIR/config.json" >/dev/null
  API_PORT="$NEWAPI"
fi
echo "127.0.0.1:${API_PORT}" > "$ETC_DIR/api.txt"   # منیجر و watchdog از این می‌خوانند
say "پورت API: $API_PORT"
printf '%s' "$PAYLOAD_JSON" | jq -r '.users_b64' | base64 -d > "$ETC_DIR/users.json"
chmod 600 "$ETC_DIR/users.json"; jq -e . "$ETC_DIR/users.json" >/dev/null
printf '%s' "$PAYLOAD_JSON" | jq -r '.links[]? // empty' > "$ETC_DIR/links.txt" || true
{ echo "Server IP : ${SERVER_IP:-?}"; echo "Installed : $(date -u +%FT%TZ)"; echo "WARP      : $WARP_NEEDED"; } > "$ETC_DIR/info.txt"
say "فایل‌های کانفیگ نوشته شد"

# --- مرحله ۵: اجرای کانتینر Xray -------------------------------------------
inf "راه‌اندازی کانتینر Xray"
XRAY_IMAGE="$XRAY_IMAGE_PINNED"
if ! docker pull "$XRAY_IMAGE" >/dev/null 2>&1; then
  warn "نسخه پین‌شده pull نشد — استفاده از :latest"
  XRAY_IMAGE="$XRAY_IMAGE_FALLBACK"; docker pull "$XRAY_IMAGE" >/dev/null 2>&1 || true
fi
echo "$XRAY_IMAGE" > "$ETC_DIR/image.txt"
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
sleep 1
# جلوگیری از تداخل با Xray/پنل دیگری که از قبل روی همین پورت‌ها فعال است
BUSY=""
for p in $(printf '%s' "$PAYLOAD_JSON" | jq -r '.ports[]? // empty'); do
  if ss -tln 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${p}$"; then BUSY="$BUSY $p"; fi
done
if [ -n "$BUSY" ]; then
  err "این پورت‌ها روی سرور از قبل اشغال‌اند:$BUSY"
  err "ظاهراً یک Xray/پنل دیگر روی این سرور فعال است."
  err "در صفحهٔ تعاملی → «تنظیمات پیشرفته» → «پورت پایه» را عوض کن (مثلاً 9443) و دستور نصب جدید را اجرا کن."
  exit 1
fi
docker run -d --name "$CONTAINER" --restart unless-stopped \
  --network host --memory="512m" \
  -v "$XRAY_DIR/config.json:/etc/xray/config.json:ro" \
  -v "$LOG_DIR:/var/log/xray" \
  "$XRAY_IMAGE" run -c /etc/xray/config.json
sleep 3
if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then say "Xray اجرا شد ($XRAY_IMAGE)"
else err "Xray بالا نیامد — لاگ:"; docker logs "$CONTAINER" --tail 30 2>&1 || true; exit 1; fi
mark_step xray

# --- مرحله ۶: نصب مدیر + watchdog ------------------------------------------
inf "نصب ابزار مدیریت و watchdog"
curl -fsSL "$RAW_BASE/scripts/kian-v2ray"  -o /usr/local/bin/kian-v2ray  && chmod +x /usr/local/bin/kian-v2ray
curl -fsSL "$RAW_BASE/scripts/watchdog.sh" -o /usr/local/bin/kian-v2ray-watchdog.sh && chmod +x /usr/local/bin/kian-v2ray-watchdog.sh
cat > /etc/cron.d/kian-v2ray-watchdog <<'CRON'
*/10 * * * * root /usr/local/bin/kian-v2ray-watchdog.sh >> /var/log/kian-xray/watchdog.log 2>&1
CRON
say "مدیر و watchdog نصب شد"
mark_step manager

# --- مرحله ۷: فایروال (ایمن — هرگز ufw را خودکار روشن نمی‌کند) --------------
# اگر کاربر فایروال نداشته باشد، روشن‌کردنش می‌تواند SSH را قطع کند → فقط وقتی
# ufw از قبل «فعال» است پورت‌های ما را باز می‌کنیم (و پورت‌های SSH را هم تضمین می‌کنیم).
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -qi '^Status: active'; then
  inf "ufw فعال است — باز کردن پورت‌های لازم"
  # پورت‌های SSH واقعی را پیدا و باز کن تا کاربر قفل نشود
  SSH_PORTS="$( { sshd -T 2>/dev/null | awk '/^port /{print $2}'; \
                  ss -tlnp 2>/dev/null | grep -i sshd | grep -oE ':[0-9]+' | tr -d ':'; \
                  echo 22; } | sort -u )"
  for sp in $SSH_PORTS; do ufw allow "${sp}/tcp" >/dev/null 2>&1 || true; done
  for p in $(printf '%s' "$PAYLOAD_JSON" | jq -r '.ports[]? // empty'); do
    ufw allow "${p}/tcp" >/dev/null 2>&1 || true
    ufw allow "${p}/udp" >/dev/null 2>&1 || true
  done
  ufw reload >/dev/null 2>&1 || true
  say "پورت‌ها در فایروال باز شد (SSH: $(echo $SSH_PORTS | tr '\n' ' '))"
else
  inf "فایروال ufw فعال نیست — تغییری اعمال نشد (پورت‌ها در دسترس‌اند)"
fi
mark_step firewall

# --- پایان -----------------------------------------------------------------
echo ""
echo "=================================================================="
say "نصب با موفقیت کامل شد! 🎉"
echo "=================================================================="
echo ""
echo "کانفیگ‌ها (در کلاینت import کن):"
echo "------------------------------------------------------------------"
cat "$ETC_DIR/links.txt" 2>/dev/null || echo "(لینکی ذخیره نشده)"
echo "------------------------------------------------------------------"
echo ""
echo "دستورها:  kian-v2ray status | configs | users"
echo ""
