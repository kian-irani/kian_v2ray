#!/usr/bin/env bash
# kian-v2ray port-check
# سرویس‌های موقت روی پورت‌های متداول راه می‌اندازد و از بیرون چک می‌کند کدام‌ها باز هستند.
# هیچ چیز روی سرور نصب نمی‌کند، فقط چند ثانیه از python -m http.server استفاده می‌کند.
# نیاز: bash, curl, python3, ss/netstat

set -u

C_G='\033[1;32m'; C_R='\033[1;31m'; C_Y='\033[1;33m'; C_B='\033[1;36m'; C_N='\033[0m'

# پورت‌هایی که می‌خواهیم چک کنیم — همان‌هایی که kian-v2ray ممکن است استفاده کند
PORTS_TO_CHECK=(443 2083 2087 2096 8080 2052 2086 8443 8444 8445 8446 80 8888 8388)

printf "${C_B}━━━ kian-v2ray port-check ━━━${C_N}\n"
printf "هدف: تشخیص اینکه کدام پورت‌ها از اینترنت قابل دسترس‌اند (آیا پروایدر می‌بندد یا نه)\n\n"

# پیش‌نیازها
if ! command -v python3 >/dev/null 2>&1; then
  printf "${C_R}✘ python3 نصب نیست.${C_N} با: apt install -y python3\n"
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  printf "${C_R}✘ curl نصب نیست.${C_N} با: apt install -y curl\n"
  exit 1
fi

# IP عمومی خودمان را پیدا کنیم (با چند fallback)
MY_IP=""
for url in https://api.ipify.org https://ifconfig.me https://icanhazip.com; do
  MY_IP="$(curl -fsS --max-time 5 "$url" 2>/dev/null | tr -d ' \n\r')"
  [ -n "$MY_IP" ] && break
done
if [ -z "$MY_IP" ]; then
  printf "${C_R}✘ نتوانستم IP عمومی سرور را پیدا کنم.${C_N}\n"
  exit 1
fi
printf "IP عمومی سرور: ${C_G}%s${C_N}\n\n" "$MY_IP"

# پورت‌های اشغال‌شدهٔ فعلی را تشخیص بده تا بهشون دست نزنیم
port_busy(){
  if command -v ss >/dev/null 2>&1; then
    ss -tln 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${1}\$"
  elif command -v netstat >/dev/null 2>&1; then
    netstat -tln 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${1}\$"
  else
    return 1
  fi
}

OPEN_PORTS=()
CLOSED_PORTS=()
BUSY_PORTS=()

for p in "${PORTS_TO_CHECK[@]}"; do
  printf "  بررسی پورت %s ... " "$p"
  if port_busy "$p"; then
    BUSY_PORTS+=("$p")
    printf "${C_Y}پورت در حال استفاده است — رد می‌شویم${C_N}\n"
    continue
  fi
  # سرویس HTTP موقت روی این پورت
  python3 -m http.server "$p" --bind 0.0.0.0 >/dev/null 2>&1 &
  PID=$!
  sleep 1
  # بررسی از بیرون
  CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://${MY_IP}:${p}/" 2>/dev/null)"
  kill "$PID" >/dev/null 2>&1
  wait "$PID" 2>/dev/null
  if [ "$CODE" = "200" ] || [ "$CODE" = "404" ]; then
    OPEN_PORTS+=("$p")
    printf "${C_G}باز ✓${C_N}\n"
  else
    CLOSED_PORTS+=("$p")
    printf "${C_R}بسته/فیلتر (پروایدر اجازه نمی‌دهد) ✘${C_N}\n"
  fi
done

printf "\n${C_B}━━━ خلاصه ━━━${C_N}\n"
if [ "${#OPEN_PORTS[@]}" -gt 0 ]; then
  printf "${C_G}پورت‌های باز از بیرون (می‌توانی این‌ها را برای Reality استفاده کنی):${C_N}\n  "
  printf "%s  " "${OPEN_PORTS[@]}"
  printf "\n\n"
  # پیشنهاد پورت پایه
  for cand in 443 2083 2087 2096 8080 8443; do
    for op in "${OPEN_PORTS[@]}"; do
      if [ "$op" = "$cand" ]; then
        printf "${C_B}پیشنهاد پورت پایه برای استفاده در تنظیمات پیشرفتهٔ صفحه:${C_N} ${C_G}%s${C_N}\n" "$cand"
        printf "  (پورت‌های Reality بعدی از همین به بعد خودکار می‌شوند — اگر کمتر از ۴ تا پورت معروف باز است، در صفحه فیلد را خالی بگذار و سیستم خودش انتخاب می‌کند)\n\n"
        break 2
      fi
    done
  done
else
  printf "${C_R}هیچ پورت باز پیدا نشد!${C_N}\n"
  printf "این یعنی پروایدر فایروال سفت‌گیر دارد. راه‌حل‌ها:\n"
  printf "  • با پشتیبانی پروایدر تماس بگیر و بخواه پورت‌های ۴۴۳/۲۰۸۳/۸۰۸۰ را باز کنند\n"
  printf "  • از پروایدر دیگری استفاده کن (Hetzner، Vultr، DigitalOcean معمولاً همه پورت‌ها را باز می‌گذارند)\n"
  printf "  • اگر دامنه داری، حالت TLS با Caddy روی :443 را فعال کن (تقریباً همه پروایدرها :443 را باز می‌گذارند)\n\n"
fi

if [ "${#CLOSED_PORTS[@]}" -gt 0 ]; then
  printf "${C_R}پورت‌های بسته از بیرون (روی این‌ها کانفیگ بسازی، کار نمی‌کند):${C_N}\n  "
  printf "%s  " "${CLOSED_PORTS[@]}"
  printf "\n\n"
fi

if [ "${#BUSY_PORTS[@]}" -gt 0 ]; then
  printf "${C_Y}پورت‌های در حال استفاده (سرویس دیگری دارد روی این‌ها کار می‌کند — نمی‌توان تست کرد):${C_N}\n  "
  printf "%s  " "${BUSY_PORTS[@]}"
  printf "\n\n"
fi

printf "${C_B}تمام شد.${C_N} حالا برگرد به صفحه و کانفیگ بساز.\n"
