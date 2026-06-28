# `/metrics` — Prometheus endpoint & deployment note

**EN** — The panel exposes `GET /metrics` in Prometheus text format (job
`kian-panel`). It is **unauthenticated by convention** so a scraper can read it
without a token. It exposes only aggregate counts (users / nodes / traffic
totals) — no secrets, no per-user credentials — but those counts are still
information you may not want public.

**FA** — پنل مسیرِ `GET /metrics` را به فرمتِ Prometheus ارائه می‌کند
(job: `kian-panel`). این مسیر **طبقِ طراحی بدونِ احراز هویت** است تا
اسکرپر بتواند بدونِ توکن آن را بخواند. فقط شمارشِ کلی (کاربر/نود/ترافیک) را
افشا می‌کند — هیچ رازی یا اعتبارنامهٔ کاربر — ولی همان شمارش‌ها هم ممکن است
چیزی باشد که نمی‌خواهید عمومی شود.

## When the panel is internet-facing / استقرار روی اینترنت

Pick **one** of these (در صورتِ قرارگیری روی اینترنت یکی را انتخاب کنید):

1. **Network layer (recommended).** Keep `/metrics` reachable only from your
   monitoring host — e.g. a firewall rule, a private network, or a reverse
   proxy that only forwards `/metrics` from the Prometheus IP.
   *لایهٔ شبکه (توصیه‌شده): دسترسی را فقط از میزبانِ مانیتورینگ باز بگذارید.*

2. **App-level IP allowlist (opt-in).** Set `KIAN_METRICS_IP_WHITELIST` to a
   comma-separated list of allowed scraper IPs. When set, `/metrics` returns
   `403` for any other client. Empty (default) means no restriction, so
   existing deployments are unchanged.
   *لیستِ سفیدِ IP در سطحِ اپ (اختیاری): متغیرِ محیطیِ
   `KIAN_METRICS_IP_WHITELIST` را تنظیم کنید.*

```bash
# only let the Prometheus host scrape /metrics
KIAN_METRICS_IP_WHITELIST="10.0.0.5,10.0.0.6"
```

> This is independent from `KIAN_ADMIN_IP_WHITELIST` (which gates the admin
> login / API), so your scraper and your admin workstation can be different
> hosts. / این مستقل از `KIAN_ADMIN_IP_WHITELIST` است.

## Troubleshooting / عیب‌یابی

- **Scraper gets `403 ip not allowed`** → its source IP isn't in
  `KIAN_METRICS_IP_WHITELIST`. Check the IP Prometheus actually connects from
  (NAT / proxy can change it) and add it, or unset the variable to disable the
  gate. / IP اسکرپر در لیست نیست؛ همان IP واقعی را اضافه کنید.
