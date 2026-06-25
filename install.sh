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

# ── Bilingual output ───────────────────────────────────────────────────────
# Default Persian; the app/page sets KIAN_LANG=en when the user operates in
# English, so the whole install console is English for them. _tr() maps the
# Persian milestone/error strings → English (zero call-site changes), and
# xlt() picks a side for interpolated lines.
KIAN_LANG="${KIAN_LANG:-fa}"
declare -A _EN=(
  ["باید با root اجرا شود (sudo)."]="Must run as root (sudo)."
  ["هیچ payload ای پیدا نشد."]="No payload found."
  ["دستور را از صفحه تعاملی کپی کن:  https://kian-irani.github.io/kian_v2ray/"]="Copy the command from the web page: https://kian-irani.github.io/kian_v2ray/"
  ["نصب از قبل در حال اجراست."]="An install is already running."
  ["نصب پیش‌نیازها (curl, jq, python3, ...)"]="Installing prerequisites (curl, jq, python3, ...)"
  ["پیش‌نیازها نصب شد"]="Prerequisites installed"
  ["پیش‌نیازها از قبل نصب — رد شد"]="Prerequisites already present — skipped"
  ["نصب Docker..."]="Installing Docker..."
  ["docker نصب نیست"]="docker is not installed"
  ["Docker آماده است"]="Docker is ready"
  ["Docker از قبل نصب است"]="Docker already installed"
  ["Docker از قبل آماده — رد شد"]="Docker already ready — skipped"
  ["بهینه‌سازی شبکه فعال شد (BBR + fq)"]="Network tuning enabled (BBR + fq)"
  ["بهینه‌سازی شبکه قبلاً انجام شده — رد شد"]="Network tuning already done — skipped"
  ["نصب Cloudflare WARP..."]="Installing Cloudflare WARP..."
  ["WARP از قبل نصب است"]="WARP already installed"
  ["ثبت‌نام WARP..."]="Registering WARP..."
  ["WARP: متصل"]="WARP: connected"
  ["WARP نصب نشده (حالت مستقیم)"]="WARP not installed (direct mode)"
  ["WARP لازم نیست (همه کانفیگ‌ها مستقیم) — رد شد"]="WARP not needed (all configs direct) — skipped"
  ["WARP وصل نشد — فعال‌سازی fallback موقت به direct تا کاربر بی‌نت نماند"]="WARP didn't connect — enabling temporary direct fallback so you stay online"
  ["WARP افتاده بود → خروجی مستقیم شد (fallback فعال؛ خودکار برمی‌گردد)"]="WARP was down → traffic went direct (fallback active; auto-recovers)"
  ["WARP برگشت: ترافیک warp دوباره از WARP می‌رود"]="WARP recovered: warp traffic routes through WARP again"
  ["fallback فعال شد: ترافیک warp موقتاً مستقیم می‌رود (در status اطلاع داده می‌شود)"]="Fallback enabled: warp traffic goes direct temporarily (shown in status)"
  ["نوشتن config.json و users.json"]="Writing config.json and users.json"
  ["اصلاح‌گرِ REALITY: فیلدِ dest برای inboundها افزوده شد (سازگاری با Xray 26.x)"]="REALITY fixer: added the dest field to inbounds (Xray 26.x compatibility)"
  ["فایل‌های کانفیگ نوشته شد"]="Config files written"
  ["تداخل پورت با سرویس دیگری روی این سرور تشخیص داده شد — انتقال همهٔ پورت‌ها به بازهٔ آزاد"]="Port conflict with another service detected — moving all ports to a free range"
  ["بازهٔ پورت آزاد پیدا نشد."]="No free port range found."
  ["راه‌اندازی کانتینر Xray"]="Starting the Xray container"
  ["نسخه پین‌شده pull نشد — استفاده از :latest"]="Pinned version didn't pull — using :latest"
  ["Xray بالا نیامد — در حال تشخیص علت..."]="Xray didn't start — diagnosing..."
  ["علت: یکی از پورت‌ها هنوز اشغال است. اجرا کن: kian-v2ray fixport"]="Cause: a port is still in use. Run: kian-v2ray fixport"
  ["علت: مشکل در config.json. اجرا کن: kian-v2ray status"]="Cause: config.json problem. Run: kian-v2ray status"
  ["علت: config.json خراب است."]="Cause: config.json is invalid."
  ["علت نامشخص — لاگ بالا را بررسی کن یا: kian-v2ray status"]="Unknown cause — check the log above or: kian-v2ray status"
  ["همگام‌سازی Subscription با گیت‌هاب (از طریق Worker)..."]="Syncing subscription to GitHub (via Worker)..."
  ["لینک‌های Subscription روی HTTPS گیت‌هاب آماده شد ✅"]="Subscription links ready on GitHub HTTPS ✅"
  ["همگام‌سازی Gist موفق نبود — sub محلی روی پورت‌ها همچنان فعال است"]="Gist sync failed — the local sub on ports is still active"
  ["نصب ابزار مدیریت و watchdog"]="Installing the manager tool and watchdog"
  ["مدیر و watchdog نصب شد"]="Manager and watchdog installed"
  ["نصب سرویس Subscription"]="Installing the Subscription service"
  ["Subscription فعال"]="Subscription active"
  ["Subscription پاسخ نداد"]="Subscription didn't respond"
  ["سرویس Subscription هنوز پاسخ نداد — بعداً: systemctl status kian-sub"]="Subscription service not responding yet — later: systemctl status kian-sub"
  ["نصب Caddy..."]="Installing Caddy..."
  ["نصب Caddy ناموفق — کانفیگ‌های TLS کار نخواهند کرد"]="Caddy install failed — TLS configs won't work"
  ["DNS دامنه قابل resolve نیست. مطمئن شو رکورد A تنظیم شده باشد."]="Domain DNS doesn't resolve. Make sure the A record is set."
  ["گواهی TLS احتمالاً گرفته نمی‌شود تا رکورد A را درست کنی. (نصب ادامه پیدا می‌کند)"]="TLS cert likely won't be issued until the A record is fixed. (Install continues)"
  ["پورت ۴۴۳ اشغال است — Caddy نمی‌تواند روی :443 bind کند."]="Port 443 is in use — Caddy can't bind to :443."
  ["پورت ۸۰ اشغال است — Caddy نمی‌تواند گواهی ACME بگیرد. اگر سرویس دیگری روی ۸۰ هست، خاموشش کن."]="Port 80 is in use — Caddy can't get an ACME cert. Stop whatever is on 80."
  ["Caddy فعال شد. گواهی TLS به‌صورت خودکار گرفته می‌شود (ممکن است ۱-۲ دقیقه طول بکشد)."]="Caddy is up. The TLS cert is obtained automatically (may take 1-2 minutes)."
  ["Caddy بالا نیامد — بررسی: systemctl status caddy ; journalctl -u caddy -n 30"]="Caddy didn't start — check: systemctl status caddy ; journalctl -u caddy -n 30"
  ["بارگذاری Caddy ناموفق — بررسی: caddy validate --config /etc/caddy/Caddyfile"]="Caddy reload failed — check: caddy validate --config /etc/caddy/Caddyfile"
  ["ufw فعال است — باز کردن پورت‌های لازم"]="ufw is active — opening the required ports"
  ["فایروال ufw فعال نیست — تغییری اعمال نشد (پورت‌ها در دسترس‌اند)"]="ufw firewall is not active — no changes (ports are reachable)"
  ["راه‌اندازی sing-box ناموفق بود — Xray دست‌نخورده است"]="sing-box setup failed — Xray is untouched"
  ["لینک‌های Hysteria2/TUIC به Subscription اضافه شد ✅"]="Hysteria2/TUIC links added to the subscription ✅"
  ["به‌روزرسانیِ Gist برای پروتکل‌های اضافی ناموفق بود (sub محلی به‌روز است)"]="Gist update for extra protocols failed (local sub is up to date)"
  ["راه‌اندازیِ پنلِ وب"]="Setting up the web panel"
  ["راه‌اندازی پنل ناموفق بود — Xray دست‌نخورده است"]="Panel setup failed — Xray is untouched"
  ["نصب با موفقیت کامل شد! 🎉"]="Installation completed successfully! 🎉"
  ["پورت‌ها تغییر کردند؛ links.txt و Subscription از config بازسازی شد. لینک صفحه ممکن است قدیمی باشد — از «kian-v2ray sub <نام>» لینک به‌روز را بگیر."]="Ports changed; links.txt and the subscription were rebuilt from config. The page link may be stale — get a fresh one with 'kian-v2ray sub <name>'."
)
_tr(){ if [ "$KIAN_LANG" = "en" ]; then printf '%s' "${_EN[$1]:-$1}"; else printf '%s' "$1"; fi; }
xlt(){ if [ "$KIAN_LANG" = "en" ]; then printf '%s' "$2"; else printf '%s' "$1"; fi; }
say(){  printf "${C_G}✔${C_N} %s\n" "$(_tr "$*")"; }
inf(){  printf "${C_B}→${C_N} %s\n" "$(_tr "$*")"; }
warn(){ printf "${C_Y}⚠${C_N} %s\n" "$(_tr "$*")"; }
err(){  printf "${C_R}✘${C_N} %s\n" "$(_tr "$*")" >&2; }
trap 'err "$(xlt "خطا در خط $LINENO" "Error on line $LINENO") — $(xlt "جزئیات" "details"): tail -n 40 '"$INSTALL_LOG"'"' ERR

mkdir -p "$WORK_DIR"
done_step(){ grep -qxF "$1" "$STATE_FILE" 2>/dev/null; }
mark_step(){ echo "$1" >> "$STATE_FILE"; }

# ===========================================================================
#  زیرفرمان‌ها: status / logs  (بدون نیاز به payload)
# ===========================================================================
cmd_status(){
  # مشکل ۰.۳: خودتشخیصی — کرش‌لوپ/WARP/پورت/SS را پیدا می‌کند و برای هر مشکل
  # دستورِ رفع را چاپ می‌کند تا کاربر بدونِ حدس‌زدن، مشکل را حل کند.
  printf "\n${C_B}━━━ KIAN V2Ray — وضعیت ━━━${C_N}\n\n"
  local issues=()   # هر مورد: "متن مشکل|||دستور رفع"
  if [ -f "$LOCK_FILE" ] && kill -0 "$(cat "$LOCK_FILE" 2>/dev/null)" 2>/dev/null; then
    warn "نصب هنوز در حال اجراست — لاگ زنده:  bash $0 logs"
  fi

  # ── Xray: در حال اجرا؟ کرش‌لوپ؟ ──
  local xrunning=0 cstatus crestart
  if command -v docker >/dev/null 2>&1; then
    cstatus="$(docker inspect -f '{{.State.Status}}' "$CONTAINER" 2>/dev/null || echo none)"
    crestart="$(docker inspect -f '{{.RestartCount}}' "$CONTAINER" 2>/dev/null || echo 0)"
    case "$cstatus" in
      running)
        xrunning=1
        say "Xray در حال اجراست (container: $CONTAINER)"
        docker ps --filter "name=$CONTAINER" --format '   آپ‌تایم: {{.Status}}' 2>/dev/null || true
        # کرش‌لوپ: ری‌استارت‌های مکرر در آپ‌تایمِ کوتاه = config/پورت ایراد دارد
        local started now s2 uptime_s
        started="$(docker inspect -f '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || echo '')"
        now=$(date -u +%s); s2=$(date -u -d "${started:-now}" +%s 2>/dev/null || echo "$now")
        uptime_s=$(( now - s2 ))
        if [ "${crestart:-0}" -ge 3 ] && [ "$uptime_s" -lt 120 ]; then
          warn "Xray کرش‌لوپ دارد (restartها: $crestart، آپ‌تایم: ${uptime_s}s)"
          issues+=("Xray کرش‌لوپ — احتمالاً config یا پورت ایراد دارد|||docker logs --tail 60 $CONTAINER ; jq . $XRAY_DIR/config.json")
        fi
        ;;
      restarting)
        err "Xray مدام ری‌استارت می‌شود (کرش‌لوپ)"
        issues+=("Xray بالا نمی‌آید (restarting)|||docker logs --tail 60 $CONTAINER")
        ;;
      none)
        err "کانتینر Xray وجود ندارد — نصب کامل نشده"
        issues+=("Xray نصب نشده|||نصب را از صفحهٔ kian-v2ray دوباره اجرا کن")
        ;;
      *)
        err "Xray اجرا نمی‌شود (وضعیت: $cstatus)"
        issues+=("Xray خاموش است|||docker start $CONTAINER")
        ;;
    esac
  else
    err "docker نصب نیست"
    issues+=("docker نصب نیست|||curl -fsSL https://get.docker.com | sh")
  fi

  # ── WARP ──
  if command -v warp-cli >/dev/null 2>&1; then
    local ws; ws="$(warp-cli --accept-tos status 2>/dev/null | head -1 || true)"
    if echo "$ws" | grep -qi connected; then
      say "WARP: متصل"
    elif [ -f "$ETC_DIR/warp_fallback.txt" ] && grep -qi on "$ETC_DIR/warp_fallback.txt" 2>/dev/null; then
      inf "WARP افتاده بود → خروجی مستقیم شد (fallback فعال؛ خودکار برمی‌گردد)"
    else
      warn "WARP: ${ws:-نامشخص}"
      issues+=("WARP متصل نیست|||warp-cli --accept-tos connect || systemctl restart warp-svc")
    fi
  else
    inf "WARP نصب نشده (حالت مستقیم)"
  fi

  # ── پورت‌ها: reality + ss باید گوش بدهند ──
  local cfg="$XRAY_DIR/config.json" listen
  if [ -f "$cfg" ] && command -v jq >/dev/null 2>&1 && command -v ss >/dev/null 2>&1; then
    listen="$(ss -tln 2>/dev/null | awk '{print $4}' | grep -oE '[0-9]+$' | sort -u)"
    local down=""
    while read -r p tag; do
      [ -z "${p:-}" ] && continue
      printf '%s\n' "$listen" | grep -qx "$p" || down="$down $tag:$p"
    done < <(jq -r '.inbounds[]|select(((.tag//"")|startswith("reality-")) or (.tag=="shadowsocks"))|"\(.port) \(.tag)"' "$cfg" 2>/dev/null)
    if [ -n "$down" ]; then
      err "پورت(هایی) که باید باز باشند گوش نمی‌دهند:$down"
      issues+=("پورت شنونده نیست:$down|||docker restart $CONTAINER ; docker logs --tail 40 $CONTAINER")
    else
      printf "\n${C_B}پورت‌های سرویس (همه شنونده):${C_N}\n"
      jq -r '.inbounds[]|select(((.tag//"")|startswith("reality-")) or (.tag=="shadowsocks"))|"   \(.tag): \(.port)"' "$cfg" 2>/dev/null || true
    fi
    # Shadowsocks (مشکل ۰.۶ — سلامتِ SS)
    local ssport; ssport="$(jq -r '.inbounds[]|select(.tag=="shadowsocks")|.port // empty' "$cfg" 2>/dev/null || true)"
    if [ -n "${ssport:-}" ]; then
      printf '%s\n' "$listen" | grep -qx "$ssport" && say "Shadowsocks فعال (پورت $ssport)" || warn "Shadowsocks خاموش (پورت $ssport)"
    fi
  fi

  # ── سرویس Subscription ──
  if [ -f "$ETC_DIR/sub_port.txt" ]; then
    local subok=0 p
    for p in $(tr ',' ' ' < "$ETC_DIR/sub_port.txt"); do
      curl -fsS --max-time 3 "http://127.0.0.1:${p}/health" 2>/dev/null | grep -q ok && { subok=1; break; }
    done
    if [ "$subok" = 1 ]; then say "Subscription فعال"
    else warn "Subscription پاسخ نداد"; issues+=("Subscription خاموش|||systemctl restart kian-sub ; systemctl status kian-sub --no-pager"); fi
  fi

  # ── جمع‌بندیِ خودتشخیصی ──
  printf "\n${C_B}━━━ خودتشخیصی ━━━${C_N}\n"
  if [ "${#issues[@]}" -eq 0 ]; then
    say "همه‌چیز سالم به‌نظر می‌رسد ✅"
  else
    err "${#issues[@]} مشکل پیدا شد — دستورِ رفع برای هرکدام:"
    local i=1 it
    for it in "${issues[@]}"; do
      printf "  ${C_Y}%d) %s${C_N}\n     ${C_B}رفع:${C_N} %s\n" "$i" "${it%%|||*}" "${it##*|||}"
      i=$(( i + 1 ))
    done
  fi
  printf "\n${C_B}کانفیگ‌ها:${C_N}  kian-v2ray configs\n\n"
}
cmd_logs(){ [ -f "$INSTALL_LOG" ] || { err "هنوز لاگی نیست."; exit 1; }; tail -n 60 -f "$INSTALL_LOG"; }

case "${1:-}" in
  status|health|doctor) cmd_status; exit 0 ;;   # ۰.۳ — همان خودتشخیصی، با نامِ آشناتر
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
chmod 700 "$ETC_DIR"
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
  printf "\n${C_B}🚀 نصب KIAN V2Ray شروع شد${C_N}\n"
  printf "   (مراحل را زنده می‌بینی. اگر SSH قطع شد، نصب در پس‌زمینه ادامه می‌یابد.)\n\n"
  : > "$INSTALL_LOG"
  setsid env KIAN_DETACHED=1 bash "$WORK_DIR/install.sh" >"$INSTALL_LOG" 2>&1 </dev/null &
  INSTALL_PID=$!
  echo "$INSTALL_PID" > "$LOCK_FILE"
  # نمایش زندهٔ لاگ تا وقتی نصب در حال اجراست؛ با پایان نصب، tail خودکار قطع می‌شود
  ( tail -n +1 -f "$INSTALL_LOG" 2>/dev/null & TAIL_PID=$!
    while kill -0 "$INSTALL_PID" 2>/dev/null; do sleep 1; done
    sleep 1; kill "$TAIL_PID" 2>/dev/null ) 
  echo ""
  # نتیجهٔ نهایی را نشان بده
  if grep -q "done" "$STATE_FILE" 2>/dev/null || grep -q "نصب با موفقیت کامل شد" "$INSTALL_LOG" 2>/dev/null; then
    printf "${C_G}✅ نصب کامل شد!${C_N}\n"
    printf "   کانفیگ‌ها:  ${C_B}kian-v2ray configs${C_N}\n"
    printf "   لینک Sub:   ${C_B}kian-v2ray sub <نام>${C_N}\n"
    printf "   وضعیت:      ${C_B}kian-v2ray status${C_N}\n"
  else
    printf "${C_Y}⚠️ نصب تمام شد ولی نتیجهٔ قطعی پیدا نشد. وضعیت را چک کن:${C_N}\n"
    printf "   ${C_B}kian-v2ray status${C_N}  یا لاگ کامل: ${C_B}bash $WORK_DIR/install.sh logs${C_N}\n"
  fi
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
# Language: env KIAN_LANG wins (set by the app/page when the user is in English);
# else fall back to payload.lang; else Persian default.
if [ "${KIAN_LANG:-}" != "en" ] && [ "${KIAN_LANG:-}" != "fa" ]; then
  _PLANG="$(_grab lang || true)"
  [ "$_PLANG" = "en" ] && KIAN_LANG="en"
fi

# --- مرحله ۱: پیش‌نیازها ---------------------------------------------------
if ! done_step deps; then
  inf "نصب پیش‌نیازها (curl, jq, python3, ...)"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y -q
  # ufw را عمداً نصب نمی‌کنیم — اگر کاربر فایروال می‌خواهد، خودش نصب کند.
  # نصب ufw روی سرور خام ممکن است rules پیش‌فرض اضافه کند و دسترسی را محدود کند.
  # python3-venv و python3-pip روی اوبونتو package جداگانه‌اند (بدون آنها panel کار نمی‌کند).
  apt-get install -y -q curl jq ca-certificates gnupg lsb-release iproute2 coreutils qrencode \
    python3 python3-venv python3-pip
  mark_step deps; say "پیش‌نیازها نصب شد"
else inf "پیش‌نیازها از قبل نصب — رد شد"; fi

# --- مرحله ۲: Docker -------------------------------------------------------
if ! done_step docker; then
  if command -v docker >/dev/null 2>&1; then inf "Docker از قبل نصب است"
  else inf "نصب Docker..."; curl -fsSL https://get.docker.com | sh; fi
  systemctl enable --now docker >/dev/null 2>&1 || true
  mark_step docker; say "Docker آماده است"
else inf "Docker از قبل آماده — رد شد"; fi

# --- مرحله ۲.۵: بهینه‌سازی شبکه (BBR + بافرها) — امن، idempotent ------------
# مرحلهٔ tune مرسوم لینوکس برای سرعت بهتر (مخصوص استریم/اینستاگرام). بین مارکرها
# نوشته می‌شود تا قابل‌بازگشت باشد؛ از sysctl موجود کاربر بکاپ گرفته می‌شود.
TUNE_BEGIN="# === KIAN tune (kian-v2ray) ==="
TUNE_END="# === END KIAN tune ==="
apply_tune(){
  local f="/etc/sysctl.d/99-kian-v2ray.conf" bak="$ETC_DIR/sysctl.backup"
  # بکاپ یک‌بارهٔ تنظیمات فعلی (برای rollback)
  [ -f "$bak" ] || sysctl -a 2>/dev/null | grep -E '^(net\.core\.(default_qdisc|rmem_max|wmem_max)|net\.ipv4\.tcp_(congestion_control|fastopen|mtu_probing))' > "$bak" 2>/dev/null || true
  # ماژول BBR
  modprobe tcp_bbr 2>/dev/null || true
  grep -qxF 'tcp_bbr' /etc/modules-load.d/bbr.conf 2>/dev/null || echo 'tcp_bbr' > /etc/modules-load.d/bbr.conf
  # فایل مستقل با مارکر — idempotent (هر بار بازنویسی می‌شود)
  cat > "$f" <<TUNE
$TUNE_BEGIN
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
net.core.rmem_max=67108864
net.core.wmem_max=67108864
net.core.rmem_default=262144
net.core.wmem_default=262144
net.ipv4.tcp_rmem=4096 87380 67108864
net.ipv4.tcp_wmem=4096 65536 67108864
net.core.netdev_max_backlog=16384
net.core.somaxconn=8192
net.ipv4.tcp_fastopen=3
net.ipv4.tcp_mtu_probing=1
net.ipv4.tcp_slow_start_after_idle=0
net.ipv4.tcp_notsent_lowat=16384
net.netfilter.nf_conntrack_max=262144
net.ipv4.tcp_max_syn_backlog=8192
$TUNE_END
TUNE
  sysctl --system >/dev/null 2>&1 || sysctl -p "$f" >/dev/null 2>&1 || true
  local cc; cc="$(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null)"
  if [ "$cc" = "bbr" ]; then say "بهینه‌سازی شبکه فعال شد (BBR + fq)"
  else warn "BBR ممکن است روی این کرنل فعال نشده باشد (cc=$cc) — مشکلی برای کارکرد نیست"; fi
}
if ! done_step tune; then apply_tune; mark_step tune; else inf "بهینه‌سازی شبکه قبلاً انجام شده — رد شد"; fi

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

# --- اصلاح‌گرِ REALITY dest (بحرانی) ----------------------------------------
# Xray-core 26.x اگر inboundِ REALITY فیلدِ dest/target نداشته باشد بالا نمی‌آید
# (خطا: "Failed to build REALITY config"). بعضی تولیدکننده‌های کلاینت (نسخه‌های
# قدیمیِ اپ موبایل/دسکتاپ) این فیلد را جا می‌اندازند → Xray اصلاً start نمی‌شود و
# هیچ پورتی گوش نمی‌دهد. اینجا برای هر inboundِ reality اگر dest خالی بود، از روی
# serverNames[0] آن را می‌سازیم تا Xray همیشه بالا بیاید (idempotent، defensive).
_tmpdest="$(mktemp)"
if jq '
  .inbounds |= map(
    if ((.streamSettings.security? // "") == "reality")
       and (((.streamSettings.realitySettings.dest // .streamSettings.realitySettings.target // "") | tostring) == "")
    then .streamSettings.realitySettings.dest =
           ((.streamSettings.realitySettings.serverNames[0] // "www.microsoft.com") + ":443")
    else . end)
' "$XRAY_DIR/config.json" > "$_tmpdest" 2>/dev/null && jq -e . "$_tmpdest" >/dev/null 2>&1; then
  if ! cmp -s "$XRAY_DIR/config.json" "$_tmpdest"; then
    mv "$_tmpdest" "$XRAY_DIR/config.json"
    inf "اصلاح‌گرِ REALITY: فیلدِ dest برای inboundها افزوده شد (سازگاری با Xray 26.x)"
  else
    rm -f "$_tmpdest"
  fi
else
  rm -f "$_tmpdest"
fi

chmod 640 "$XRAY_DIR/config.json"   # root:docker r+w, Xray container reads via docker gid
chown root:root "$XRAY_DIR/config.json" 2>/dev/null || true

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
# --- مشکل ۰.۵: نصب مجدد امن — بکاپ + ادغام کاربران قبلی ---
# اگر نصب قبلی وجود دارد، اول بکاپ بگیر، سپس کاربرانی که در payload جدید نیستند
# را حفظ کن (هم در users.json و هم به‌عنوان client در همهٔ inboundهای reality جدید)
# تا نصب دوباره کاربران موجود را پاک نکند.
NEW_USERS_JSON="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.users_b64' | base64 -d)"
if [ -f "$ETC_DIR/users.json" ] && jq -e '.users' "$ETC_DIR/users.json" >/dev/null 2>&1; then
  bdir="$ETC_DIR/backups"; mkdir -p "$bdir"; bts="$(date -u +%Y%m%d-%H%M%S)"
  cp "$ETC_DIR/users.json" "$bdir/users_${bts}.json" 2>/dev/null || true
  [ -f "$XRAY_DIR/config.json" ] && cp "$XRAY_DIR/config.json" "$bdir/config_${bts}.json" 2>/dev/null || true
  warn "نصب قبلی پیدا شد — بکاپ در $bdir/*_${bts}.* ساخته شد"
  # کاربران قدیمی که ایمیلشان در payload جدید نیست → حفظ شوند
  OLD_EXTRA="$(jq -c --argjson nu "$NEW_USERS_JSON" \
    '[.users[] as $o | select(($nu.users|map(.email)|index($o.email))|not) | $o]' \
    "$ETC_DIR/users.json" 2>/dev/null || echo '[]')"
  EXTRA_COUNT="$(printf '%s' "$OLD_EXTRA" | jq 'length' 2>/dev/null || echo 0)"
  if [ "${EXTRA_COUNT:-0}" -gt 0 ]; then
    inf "ادغام $EXTRA_COUNT کاربر قبلی که در نصب جدید نبودند"
    # ۱) به users.json جدید اضافه کن
    NEW_USERS_JSON="$(printf '%s' "$NEW_USERS_JSON" | jq -c --argjson ex "$OLD_EXTRA" '.users += $ex')"
    # ۲) به‌عنوان client (id,email,flow) به همهٔ inboundهای reality جدید اضافه کن
    CLIENTS_ADD="$(printf '%s' "$OLD_EXTRA" | jq -c '[.[]|{id:.id,email:.email,flow:"xtls-rprx-vision"}]')"
    tmpc="$(mktemp)"
    jq --argjson add "$CLIENTS_ADD" \
      '(.inbounds[]|select((.tag//"")|startswith("reality-"))|.settings.clients) += $add' \
      "$XRAY_DIR/config.json" > "$tmpc" && jq -e . "$tmpc" >/dev/null 2>&1 && mv "$tmpc" "$XRAY_DIR/config.json" || rm -f "$tmpc"
    warn "برای افزودن کاربر جدید بهتر است از «تب مدیریت» یا «kian-v2ray add» استفاده کنی، نه نصب دوباره."
  fi
fi
printf '%s' "$NEW_USERS_JSON" > "$ETC_DIR/users.json"
chmod 600 "$ETC_DIR/users.json"; jq -e . "$ETC_DIR/users.json" >/dev/null
printf '%s' "$PAYLOAD_JSON" | jq -r '.links[]? // empty' > "$ETC_DIR/links.txt" || true

# --- فایل‌های Subscription (فاز ۲): هر کاربر یک توکن از payload → یک فایل base64 ---
SUB_PORT="$(printf '%s' "$PAYLOAD_JSON" | jq -r '(.sub_port // 80) | if type=="array" then map(tostring)|join(",") else tostring end')"
SUB_TOKENS="$(printf '%s' "$PAYLOAD_JSON" | jq -c '.sub_tokens // {}')"
echo "$SUB_TOKENS" > "$ETC_DIR/sub_tokens.json"; chmod 600 "$ETC_DIR/sub_tokens.json"
echo "$SUB_PORT" > "$ETC_DIR/sub_port.txt"
# پروتکل‌های اضافی که کاربر در صفحه/اپ انتخاب کرده (Hysteria2/TUIC روی sing-box).
# مثال: ["hysteria2","tuic"]. اگر env هم ست باشد، فعال می‌شود (هر دو منبع پذیرفته).
EXTRA_PROTOCOLS="$(printf '%s' "$PAYLOAD_JSON" | jq -r '(.extra_protocols // []) | join(",")')"
mkdir -p "$ETC_DIR/sub"
if [ "$(printf '%s' "$SUB_TOKENS" | jq 'length')" -gt 0 ]; then
  # برای هر ایمیل، لینک‌های همان کاربر (که نام کاربر در label لینک هست) را جمع کن
  printf '%s' "$SUB_TOKENS" | jq -r 'to_entries[]|.key+"\t"+.value' | while IFS=$'\t' read -r email token; do
    local_name="${email%@*}"
    # لینک‌های این کاربر = خطوطی از links.txt که با KIAN-<name>- برچسب خورده‌اند یا SS مشترک
    user_links="$(grep -F "#KIAN-${local_name}-" "$ETC_DIR/links.txt" 2>/dev/null || true)"
    ss_link="$(grep -iE 'KIAN-Shadowsocks|KIAN-SS' "$ETC_DIR/links.txt" 2>/dev/null || true)"
    all_links="$(printf '%s\n%s\n' "$user_links" "$ss_link" | sed '/^$/d')"
    [ -z "$all_links" ] && all_links="$(cat "$ETC_DIR/links.txt")"   # fallback: همه
    printf '%s' "$all_links" | base64 -w0 > "$ETC_DIR/sub/${token}.txt"
  done
  say "فایل‌های Subscription ساخته شد ($(printf '%s' "$SUB_TOKENS" | jq 'length') کاربر)"
fi

{ echo "Server IP : ${SERVER_IP:-?}"; echo "Installed : $(date -u +%FT%TZ)"; echo "WARP      : $WARP_NEEDED"; echo "Sub Port  : $SUB_PORT"; } > "$ETC_DIR/info.txt"
say "فایل‌های کانفیگ نوشته شد"

# --- مرحله ۵: اجرای کانتینر Xray -------------------------------------------
inf "راه‌اندازی کانتینر Xray"
XRAY_IMAGE="$XRAY_IMAGE_PINNED"
if ! docker pull "$XRAY_IMAGE" >/dev/null 2>&1; then
  warn "نسخه پین‌شده pull نشد — استفاده از :latest"
  XRAY_IMAGE="$XRAY_IMAGE_FALLBACK"; docker pull "$XRAY_IMAGE" >/dev/null 2>&1 || true
fi
echo "$XRAY_IMAGE" > "$ETC_DIR/image.txt"
# ثبت نسخهٔ اسکریپت (برای مقایسه در «kian-v2ray update»)
SCRIPT_VER="$(curl -fsSL "$RAW_BASE/VERSION" 2>/dev/null | grep '^SCRIPT_VERSION=' | cut -d= -f2 | tr -d '\r ')"
[ -n "$SCRIPT_VER" ] && echo "$SCRIPT_VER" > "$ETC_DIR/script_version.txt"
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
sleep 1
# ─────────────────────────────────────────────────────────────────────────────
# تخصیص پورت مقاوم و عمومی (مستقل از مشکلاتِ هر سرورِ خاص):
#   • همهٔ پورت‌های در حال استفاده روی سرور را می‌بینیم.
#   • اگر هر کدام از پورت‌های انتخابی (reality + ss) اشغال بود، *همهٔ* پورت‌های
#     reality را یکجا به یک بازهٔ آزادِ پشت‌سرهم منتقل می‌کنیم تا با هیچ نصب/پنل
#     دیگری روی این سرور قاطی نشوند (نه تک‌تک — که نیمه‌قاطی می‌شد).
#   • سپس links.txt و فایل‌های Subscription را *از روی config نهایی* بازمی‌سازیم
#     (نه با جایگزینی رشته‌ایِ لینک‌های از-پیش-ساخته). این کار را قطعی می‌کند.
# ─────────────────────────────────────────────────────────────────────────────
port_busy(){ ss -tln 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${1}\$"; }

PBK="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.reality_pbk // ""')"
SID_FALLBACK="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.reality_sid // ""')"
SS_PASS="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.ss_password // ""')"

# پورت‌های فعلیِ reality (به‌ترتیب tag) و پورت ss
REALITY_PORTS="$(jq -r '.inbounds[]|select((.tag//"")|startswith("reality-"))|.port' "$XRAY_DIR/config.json" 2>/dev/null)"
SS_PORT_CUR="$(jq -r '.inbounds[]|select(.tag=="shadowsocks")|.port' "$XRAY_DIR/config.json" 2>/dev/null)"
N_REALITY="$(printf '%s\n' $REALITY_PORTS | grep -c . || echo 0)"

# آیا تداخلی وجود دارد؟ (هر پورت reality یا ss که اشغال باشد)
COLLISION=0
for p in $REALITY_PORTS; do port_busy "$p" && COLLISION=1; done
[ -n "$SS_PORT_CUR" ] && port_busy "$SS_PORT_CUR" && COLLISION=1

if [ "$COLLISION" = 1 ]; then
  warn "تداخل پورت با سرویس دیگری روی این سرور تشخیص داده شد — انتقال همهٔ پورت‌ها به بازهٔ آزاد"
  # یک بازهٔ پشت‌سرهمِ آزاد به طول N_REALITY پیدا کن (به‌علاوهٔ یک پورت برای ss)
  NEED=$(( N_REALITY + 1 ))
  BASE_NEW=""
  for _try in $(seq 1 400); do
    start=$(( (RANDOM % 20000) + 20000 ))
    ok=1
    i=0
    while [ "$i" -lt "$NEED" ]; do
      port_busy $(( start + i )) && { ok=0; break; }
      i=$(( i + 1 ))
    done
    [ "$ok" = 1 ] && { BASE_NEW="$start"; break; }
  done
  if [ -z "$BASE_NEW" ]; then err "بازهٔ پورت آزاد پیدا نشد."; exit 1; fi

  # نگاشت پورت‌های قدیمی reality → پورت‌های جدیدِ پشت‌سرهم، و اعمال در config
  NEW_REALITY=""
  idx=0
  for oldp in $REALITY_PORTS; do
    newp=$(( BASE_NEW + idx ))
    tmpc="$(mktemp)"
    jq --argjson o "$oldp" --argjson n "$newp" '(.inbounds[]|select(.port==$o)|.port)=$n' "$XRAY_DIR/config.json" > "$tmpc" && jq -e . "$tmpc" >/dev/null 2>&1 && mv "$tmpc" "$XRAY_DIR/config.json" || rm -f "$tmpc"
    NEW_REALITY="$NEW_REALITY $newp"
    idx=$(( idx + 1 ))
  done
  # پورت ss = آخرین پورتِ بازه
  if [ -n "$SS_PORT_CUR" ]; then
    SS_NEW=$(( BASE_NEW + N_REALITY ))
    tmpc="$(mktemp)"
    jq --argjson o "$SS_PORT_CUR" --argjson n "$SS_NEW" '(.inbounds[]|select(.tag=="shadowsocks")|.port)=$n' "$XRAY_DIR/config.json" > "$tmpc" && jq -e . "$tmpc" >/dev/null 2>&1 && mv "$tmpc" "$XRAY_DIR/config.json" || rm -f "$tmpc"
  fi
  inf "پورت‌های جدید reality:$NEW_REALITY${SS_PORT_CUR:+ | ss: $SS_NEW}"
fi

# ── بازسازی links.txt و فایل‌های Subscription از روی config نهایی (قطعی) ──
# (به‌جای جایگزینی رشته‌ای؛ همیشه با پورت‌های واقعیِ در حال اجرا هماهنگ است)
rebuild_links_from_config(){
  [ -z "$PBK" ] && return 1   # اگر pbk نداریم (payload قدیمی)، بازسازی نکن
  : > "$ETC_DIR/links.txt"
  # برای هر کاربر (از روی clientهای اولین inbound reality) × هر inbound reality
  local emails
  emails="$(jq -r '[.inbounds[]|select((.tag//"")|startswith("reality-"))][0].settings.clients[].email' "$XRAY_DIR/config.json" 2>/dev/null)"
  # نگاشت email→uuid از همان inbound
  jq -r '
    ([.inbounds[]|select((.tag//"")|startswith("reality-"))]) as $ri
    | $ri[0].settings.clients[] as $c
    | $ri[] as $ib
    | "\($c.id)|\($c.email)|\($ib.port)|\($ib.streamSettings.realitySettings.serverNames[0])|\($ib.streamSettings.realitySettings.shortIds[0])|\($ib.tag)"
  ' "$XRAY_DIR/config.json" 2>/dev/null | while IFS='|' read -r uuid email port sni sid tag; do
    local label_ch local_name
    case "$tag" in
      *warp*) label_ch="WARP" ;;
      *) label_ch="سریع" ;;
    esac
    local_name="${email%@*}"
    printf 'vless://%s@%s:%s?encryption=none&flow=xtls-rprx-vision&security=reality&sni=%s&fp=chrome&pbk=%s&sid=%s&type=tcp#KIAN-%s-%s-%s\n' \
      "$uuid" "$SERVER_IP" "$port" "$sni" "$PBK" "$sid" "$local_name" "$label_ch" "$sni" >> "$ETC_DIR/links.txt"
  done
  # Shadowsocks (در صورت وجود)
  local ssport
  ssport="$(jq -r '.inbounds[]|select(.tag=="shadowsocks")|.port' "$XRAY_DIR/config.json" 2>/dev/null)"
  if [ -n "$ssport" ] && [ -n "$SS_PASS" ]; then
    local ssb64
    ssb64="$(printf 'chacha20-ietf-poly1305:%s' "$SS_PASS" | base64 -w0)"
    printf 'ss://%s@%s:%s#KIAN-Shadowsocks\n' "$ssb64" "$SERVER_IP" "$ssport" >> "$ETC_DIR/links.txt"
  fi
  return 0
}

# فقط اگر تداخل بود و pbk داریم، links.txt را از config بازبساز؛ وگرنه همان لینک‌های payload می‌مانند
if [ "$COLLISION" = 1 ] && [ -n "$PBK" ]; then
  if rebuild_links_from_config; then
    # فایل‌های Subscription را از links.txt جدید بازبساز (هر کاربر = خطوط KIAN-<name>- + SS)
    if [ -d "$ETC_DIR/sub" ] && [ -f "$ETC_DIR/sub_tokens.json" ]; then
      jq -r 'to_entries[]|.key+"\t"+.value' "$ETC_DIR/sub_tokens.json" | while IFS=$'\t' read -r email token; do
        ln="${email%@*}"
        ul="$( { grep -F "#KIAN-${ln}-" "$ETC_DIR/links.txt"; grep -iE 'KIAN-Shadowsocks' "$ETC_DIR/links.txt"; } 2>/dev/null )"
        [ -z "$ul" ] && ul="$(cat "$ETC_DIR/links.txt")"
        printf '%s' "$ul" | sed '/^$/d' | base64 -w0 > "$ETC_DIR/sub/${token}.txt"
      done
    fi
    warn "پورت‌ها تغییر کردند؛ links.txt و Subscription از config بازسازی شد. لینک صفحه ممکن است قدیمی باشد — از «kian-v2ray sub <نام>» لینک به‌روز را بگیر."
  fi
fi
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
# keep config.json root-only (640) — the container runs as --user 0:0 so root can read it
chmod 640 "$XRAY_DIR/config.json"
docker run -d --name "$CONTAINER" --restart unless-stopped \
  --network host --memory="512m" \
  --user 0:0 \
  --cap-add=NET_BIND_SERVICE \
  -v "$XRAY_DIR/config.json:/etc/xray/config.json:ro" \
  -v "$LOG_DIR:/var/log/xray" \
  "$XRAY_IMAGE" run -c /etc/xray/config.json >/dev/null 2>&1
sleep 3
if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  say "Xray اجرا شد ($XRAY_IMAGE)"
  # ── همگام‌سازی Subscription با Gist از طریق Worker (لینک HTTPS تضمینی) ──
  GIST_PROXY_VAL="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.gist_proxy // ""')"
  INSTALL_ID_VAL="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.install_id // ""')"
  if [ -n "$GIST_PROXY_VAL" ] && [ -d "$ETC_DIR/sub" ]; then
    inf "همگام‌سازی Subscription با گیت‌هاب (از طریق Worker)..."
    curl -fsSL "$RAW_BASE/scripts/gist_sync.py" -o /usr/local/bin/kian-gist-sync.py 2>/dev/null && chmod +x /usr/local/bin/kian-gist-sync.py
    printf '%s' "$GIST_PROXY_VAL" > "$ETC_DIR/gist_proxy"; chmod 600 "$ETC_DIR/gist_proxy"
    # install_id را از payload بنویس تا URL Gist با همانی که صفحه به کاربر داد یکی بماند
    if [ -n "$INSTALL_ID_VAL" ]; then
      printf '%s' "$INSTALL_ID_VAL" > "$ETC_DIR/install_id"; chmod 600 "$ETC_DIR/install_id"
    fi
    if python3 /usr/local/bin/kian-gist-sync.py "$GIST_PROXY_VAL" "$ETC_DIR/install_id" "$ETC_DIR/sub" "$ETC_DIR/gist_map.json" 2>&1; then
      say "لینک‌های Subscription روی HTTPS گیت‌هاب آماده شد ✅"
    else
      warn "همگام‌سازی Gist موفق نبود — sub محلی روی پورت‌ها همچنان فعال است"
    fi
  fi
else
  err "Xray بالا نیامد — در حال تشخیص علت..."
  echo "──────── لاگ Xray ────────"
  docker logs "$CONTAINER" --tail 30 2>&1 || true
  echo "──────────────────────────"
  # تشخیص خودکار علت رایج
  CFG_ERR="$(docker logs "$CONTAINER" 2>&1 | grep -iE 'address already in use|bind|failed to|invalid|panic' | head -3)"
  if printf '%s' "$CFG_ERR" | grep -qi 'address already in use\|bind'; then
    err "علت: یکی از پورت‌ها هنوز اشغال است. اجرا کن: kian-v2ray fixport"
  elif printf '%s' "$CFG_ERR" | grep -qi 'invalid\|panic'; then
    err "علت: مشکل در config.json. اجرا کن: kian-v2ray status"
  elif ! jq -e . "$XRAY_DIR/config.json" >/dev/null 2>&1; then
    err "علت: config.json خراب است."
  else
    err "علت نامشخص — لاگ بالا را بررسی کن یا: kian-v2ray status"
  fi
  exit 1
fi
mark_step xray

# --- مرحله ۶: نصب مدیر + watchdog ------------------------------------------
inf "نصب ابزار مدیریت و watchdog"
curl -fsSL "$RAW_BASE/scripts/kian-v2ray"  -o /usr/local/bin/kian-v2ray  && chmod +x /usr/local/bin/kian-v2ray
curl -fsSL "$RAW_BASE/scripts/watchdog.sh" -o /usr/local/bin/kian-v2ray-watchdog.sh && chmod +x /usr/local/bin/kian-v2ray-watchdog.sh
# پروتکل‌های اضافی (Hysteria2/TUIC روی sing-box) — فقط نصب می‌شود، خودکار اجرا نمی‌شود.
curl -fsSL "$RAW_BASE/scripts/kian-protocols.sh" -o /usr/local/bin/kian-protocols.sh 2>/dev/null && chmod +x /usr/local/bin/kian-protocols.sh || true
# پنلِ وب — فقط نصب می‌شود؛ با KIAN_PANEL=1 یا «kian-v2ray panel» راه می‌افتد.
curl -fsSL "$RAW_BASE/scripts/kian-panel.sh" -o /usr/local/bin/kian-panel.sh 2>/dev/null && chmod +x /usr/local/bin/kian-panel.sh || true
cat > /etc/cron.d/kian-v2ray-watchdog <<'CRON'
*/10 * * * * root /usr/local/bin/kian-v2ray-watchdog.sh >> /var/log/kian-xray/watchdog.log 2>&1
CRON
say "مدیر و watchdog نصب شد"
mark_step manager

# --- مرحله ۶.۲: کانفیگ‌های دامنه‌دار (TLS) — فاز ۳ ---------------------------
# اگر کاربر در صفحه TLS را فعال کرده باشد، Caddy نصب می‌شود و روی :443 با گواهی
# واقعی Let's Encrypt به Xrayِ داخلی reverse proxy می‌کند.
TLS_DOMAIN_VAL="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.tls_domain // ""')"
CADDYFILE_B64="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.caddyfile_b64 // ""')"
if [ -n "$TLS_DOMAIN_VAL" ] && [ -n "$CADDYFILE_B64" ]; then
  inf "راه‌اندازی کانفیگ‌های دامنه‌دار برای: $TLS_DOMAIN_VAL"
  # بررسی DNS: آیا دامنه به IP این سرور اشاره می‌کند؟
  RESOLVED_IP="$(getent hosts "$TLS_DOMAIN_VAL" 2>/dev/null | awk '{print $1}' | head -1)"
  if [ -n "$RESOLVED_IP" ] && [ "$RESOLVED_IP" != "$SERVER_IP" ]; then
    warn "دامنه ($TLS_DOMAIN_VAL → $RESOLVED_IP) به IP این سرور ($SERVER_IP) اشاره نمی‌کند."
    warn "گواهی TLS احتمالاً گرفته نمی‌شود تا رکورد A را درست کنی. (نصب ادامه پیدا می‌کند)"
  elif [ -z "$RESOLVED_IP" ]; then
    warn "DNS دامنه قابل resolve نیست. مطمئن شو رکورد A تنظیم شده باشد."
  fi
  # نصب Caddy (اگر نبود)
  if ! command -v caddy >/dev/null 2>&1; then
    inf "نصب Caddy..."
    apt-get install -y debian-keyring debian-archive-keyring apt-transport-https >/dev/null 2>&1 || true
    curl -fsSL "https://dl.cloudsmith.io/public/caddy/stable/gpg.key" | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg 2>/dev/null
    curl -fsSL "https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt" > /etc/apt/sources.list.d/caddy-stable.list
    apt-get update -qq >/dev/null 2>&1 || true
    apt-get install -y caddy >/dev/null 2>&1 || warn "نصب Caddy ناموفق — کانفیگ‌های TLS کار نخواهند کرد"
  fi
  # نوشتن Caddyfile
  if command -v caddy >/dev/null 2>&1; then
    # بررسی پورت ۸۰ و ۴۴۳ — اگر اشغال بود هشدار
    if ss -tln 2>/dev/null | awk '{print $4}' | grep -qE '[:.]80$'; then
      warn "پورت ۸۰ اشغال است — Caddy نمی‌تواند گواهی ACME بگیرد. اگر سرویس دیگری روی ۸۰ هست، خاموشش کن."
    fi
    if ss -tln 2>/dev/null | awk '{print $4}' | grep -qE '[:.]443$'; then
      warn "پورت ۴۴۳ اشغال است — Caddy نمی‌تواند روی :443 bind کند."
    fi
    mkdir -p /etc/caddy
    printf '%s' "$CADDYFILE_B64" | base64 -d > /etc/caddy/Caddyfile
    chmod 644 /etc/caddy/Caddyfile
    systemctl enable caddy >/dev/null 2>&1 || true
    if systemctl reload caddy >/dev/null 2>&1 || systemctl restart caddy >/dev/null 2>&1; then
      sleep 3
      if systemctl is-active caddy >/dev/null 2>&1; then
        say "Caddy فعال شد. گواهی TLS به‌صورت خودکار گرفته می‌شود (ممکن است ۱-۲ دقیقه طول بکشد)."
        inf "تست HTTPS: curl -I https://$TLS_DOMAIN_VAL"
      else
        err "Caddy بالا نیامد — بررسی: systemctl status caddy ; journalctl -u caddy -n 30"
      fi
    else
      err "بارگذاری Caddy ناموفق — بررسی: caddy validate --config /etc/caddy/Caddyfile"
    fi
    echo "$TLS_DOMAIN_VAL" > "$ETC_DIR/tls_domain.txt"
  fi
  mark_step tls
fi

# --- مرحله ۶.۵: سرویس Subscription (فاز ۲) ---------------------------------
inf "نصب سرویس Subscription"
curl -fsSL "$RAW_BASE/scripts/sub-server.py" -o /usr/local/bin/kian-sub-server.py && chmod +x /usr/local/bin/kian-sub-server.py
# چند پورت کاندید را امتحان می‌کنیم: هر کدام آزاد بود، sub رویش بالا می‌آید.
# هدف: حداقل یکی از بیرون قابل دسترس باشد، بدون اقدام کاربر.
#   • 80  : استاندارد وب (تقریباً همیشه از بیرون باز است)
#   • 8888: پورت رایج HTTP جایگزین
#   • 2086: یکی از پورت‌های HTTP که Cloudflare/پروایدرها معمولاً اجازه می‌دهند
#   • یک پورت تصادفی بالا: آخرین fallback
sub_port_busy(){ ss -tln 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${1}\$"; }
SUB_PORTS=""
for cand in 80 8888 2086; do
  sub_port_busy "$cand" || SUB_PORTS="${SUB_PORTS:+$SUB_PORTS,}$cand"
done
# اگر همهٔ کاندیدها اشغال بودند، حداقل یک پورت تصادفی بالا
if [ -z "$SUB_PORTS" ]; then
  for _ in $(seq 1 200); do
    rp=$(( (RANDOM % 10000) + 20000 ))
    sub_port_busy "$rp" || { SUB_PORTS="$rp"; break; }
  done
fi
[ -z "$SUB_PORTS" ] && SUB_PORTS="80"   # برای ایمنی؛ نباید برسیم اینجا
echo "$SUB_PORTS" > "$ETC_DIR/sub_port.txt"   # ممکن است "80,8888,2086" یا "23456"
cat > /etc/systemd/system/kian-sub.service <<UNIT
[Unit]
Description=KIAN V2Ray Subscription server (multi-port)
After=network.target
[Service]
ExecStart=/usr/bin/python3 /usr/local/bin/kian-sub-server.py $SUB_PORTS $ETC_DIR/sub
Restart=always
RestartSec=3
User=root
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload >/dev/null 2>&1 || true
systemctl enable --now kian-sub >/dev/null 2>&1 || true
# چک سلامت با ۳ تلاش (سرویس ممکن است چند ثانیه طول بکشد بالا بیاید)
SUB_OK=""
for try in 1 2 3; do
  sleep 2
  for p in $(echo "$SUB_PORTS" | tr ',' ' '); do
    if curl -fsS --max-time 3 "http://127.0.0.1:${p}/health" 2>/dev/null | grep -q ok; then
      [[ ",$SUB_OK," == *",$p,"* ]] || SUB_OK="${SUB_OK:+$SUB_OK,}$p"
    fi
  done
  [ -n "$SUB_OK" ] && break
done
if [ -n "$SUB_OK" ]; then
  say "سرویس Subscription فعال شد (پورت‌ها: $SUB_OK)"
else
  warn "سرویس Subscription هنوز پاسخ نداد — بعداً: systemctl status kian-sub"
fi

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
  # پورت‌های نهایی را از خودِ config.json بخوان (شامل پورت‌هایی که auto-fix عوض کرده)
  FW_PORTS="$(jq -r '.inbounds[]|select(((.tag//"")|startswith("reality-")) or (.tag=="shadowsocks"))|.port' "$XRAY_DIR/config.json" 2>/dev/null)"
  [ -z "$FW_PORTS" ] && FW_PORTS="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.ports[]? // empty')"
  for p in $FW_PORTS; do
    ufw allow "${p}/tcp" >/dev/null 2>&1 || true
    ufw allow "${p}/udp" >/dev/null 2>&1 || true
  done
  # پورت‌های سرویس Subscription (می‌تواند چند پورت با ویرگول جدا باشد)
  SUB_PORTS_FW="$(cat "$ETC_DIR/sub_port.txt" 2>/dev/null || echo 80)"
  for sp in $(echo "$SUB_PORTS_FW" | tr ',' ' '); do
    [ -n "$sp" ] && ufw allow "${sp}/tcp" >/dev/null 2>&1 || true
  done
  # پورت‌های TLS (Caddy) — اگر فاز ۳ فعال است
  if [ -f "$ETC_DIR/tls_domain.txt" ]; then
    ufw allow 80/tcp >/dev/null 2>&1 || true
    ufw allow 443/tcp >/dev/null 2>&1 || true
  fi
  ufw reload >/dev/null 2>&1 || true
  say "پورت‌ها در فایروال باز شد (SSH: $(echo $SSH_PORTS | tr '\n' ' '))"
else
  inf "فایروال ufw فعال نیست — تغییری اعمال نشد (پورت‌ها در دسترس‌اند)"
fi
mark_step firewall

# --- پروتکل‌های اضافی (انتخابِ کاربر در صفحه/اپ، یا KIAN_EXTRA_PROTOCOLS=1) ---
# Hysteria2/TUIC روی sing-box، کنارِ Xray. کاملاً additive — مسیرِ کارکنندهٔ
# Reality/SS/TLS دست‌نخورده می‌ماند. حالا با انتخابِ کاربر (payload.extra_protocols)
# هم فعال می‌شود، و لینک‌های تولیدشده به Subscription هر کاربر اضافه + Gist دوباره
# همگام می‌شود تا در کلاینت (اپ/صفحه) مستقیماً دیده شوند.
if { [ -n "$EXTRA_PROTOCOLS" ] || [ "${KIAN_EXTRA_PROTOCOLS:-0}" = "1" ]; } \
   && [ -x /usr/local/bin/kian-protocols.sh ]; then
  inf "فعال‌سازی پروتکل‌های اضافی (Hysteria2/TUIC روی sing-box): ${EXTRA_PROTOCOLS:-env}"
  if bash /usr/local/bin/kian-protocols.sh enable; then
    # لینک‌های per-user (برچسب #KIAN-<name>-Hysteria2/-TUIC/-AnyTLS/-ShadowTLS) را بگیر
    EXTRA_LINKS="$(bash /usr/local/bin/kian-protocols.sh links 2>/dev/null \
      | grep -oE '(hysteria2|tuic|anytls|ss)://[^[:space:]]+#KIAN-[^[:space:]]+' || true)"
    if [ -n "$EXTRA_LINKS" ]; then
      printf '%s\n' "$EXTRA_LINKS" >> "$ETC_DIR/links.txt"
      printf '%s\n' "$EXTRA_LINKS" > "$ETC_DIR/extra_links.txt"
      # به Subscription هرکاربر فقط لینکِ خودش را اضافه کن (per-user، نه اشتراکی).
      # توکن‌ها در sub_tokens.json به ایمیل کاربر نگاشت شده‌اند.
      if [ -d "$ETC_DIR/sub" ] && [ -f "$ETC_DIR/sub_tokens.json" ]; then
        jq -r 'to_entries[]|.key+"\t"+.value' "$ETC_DIR/sub_tokens.json" \
          | while IFS=$'\t' read -r email token; do
              [ -z "$token" ] && continue
              local_name="${email%@*}"
              f="$ETC_DIR/sub/${token}.txt"
              [ -f "$f" ] || continue
              # فقط لینک‌های همان کاربر (#KIAN-<name>-Hysteria2/-TUIC)
              user_extra="$(printf '%s\n' "$EXTRA_LINKS" | grep -F "#KIAN-${local_name}-" || true)"
              [ -z "$user_extra" ] && continue
              { base64 -d "$f" 2>/dev/null; printf '%s\n' "$user_extra"; } \
                | sed '/^$/d' | base64 -w0 > "${f}.new" && mv "${f}.new" "$f"
            done
        # Gist را دوباره همگام کن تا لینکِ HTTPS هم به‌روز شود
        GIST_PROXY_VAL="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.gist_proxy // ""')"
        if [ -n "$GIST_PROXY_VAL" ] && [ -x /usr/local/bin/kian-gist-sync.py ]; then
          python3 /usr/local/bin/kian-gist-sync.py "$GIST_PROXY_VAL" \
            "$ETC_DIR/install_id" "$ETC_DIR/sub" "$ETC_DIR/gist_map.json" >/dev/null 2>&1 \
            && say "لینک‌های Hysteria2/TUIC به Subscription اضافه شد ✅" \
            || warn "به‌روزرسانیِ Gist برای پروتکل‌های اضافی ناموفق بود (sub محلی به‌روز است)"
        fi
      fi
    fi
  else
    warn "راه‌اندازی sing-box ناموفق بود — Xray دست‌نخورده است"
  fi
fi

# پنلِ وب (اختیاری — فقط با KIAN_PANEL=1). additive؛ Xray دست‌نخورده.
if [ "${KIAN_PANEL:-0}" = "1" ] && [ -x /usr/local/bin/kian-panel.sh ]; then
  inf "راه‌اندازیِ پنلِ وب"
  bash /usr/local/bin/kian-panel.sh enable || warn "راه‌اندازی پنل ناموفق بود — Xray دست‌نخورده است"
fi

# پس از اتمام نصب، payload.b64 حذف می‌شود (حاوی کلید خصوصی و رمزها است)
rm -f "$ETC_DIR/payload.b64"

# --- پایان -----------------------------------------------------------------
mark_step done
echo ""
echo "=================================================================="
say "نصب با موفقیت کامل شد! 🎉"
echo "=================================================================="
echo ""
echo "$(xlt "کانفیگ‌ها (در کلاینت import کن):" "Configs (import these in your client):")"
echo "------------------------------------------------------------------"
cat "$ETC_DIR/links.txt" 2>/dev/null || echo "$(xlt "(لینکی ذخیره نشده)" "(no link saved)")"
echo "------------------------------------------------------------------"
echo ""
echo "$(xlt "دستورها" "Commands"):  kian-v2ray status | configs | users"
echo ""
