# Periodic traffic reset / ریستِ دوره‌ای حجم (FR-S1)

**EN** — Each user can have a **reset strategy** so their used traffic is
zeroed automatically on a schedule, instead of the quota being a one-time
lifetime cap:

| Strategy | Resets at (UTC) |
|----------|-----------------|
| `none` (default) | never — quota is a lifetime cap |
| `daily`   | 00:00 every day |
| `weekly`  | 00:00 every Monday |
| `monthly` | 00:00 on the 1st of each month |

When a reset fires, the user's `used_bytes` is set to 0. A user who was
auto-disabled **only** because they hit their quota is re-enabled — unless
their validity (`expires_at`) has also passed, in which case they stay off.

**FA** — هر کاربر می‌تواند یک **استراتژیِ ریست** داشته باشد تا مصرفش به‌صورت
خودکار و دوره‌ای صفر شود (روزانه/هفتگی/ماهانه) به‌جای سقفِ یک‌بارهٔ کل. هنگام
ریست، `used_bytes` صفر می‌شود و اگر کاربر فقط به‌خاطرِ پر شدنِ حجم غیرفعال شده
بود دوباره فعال می‌شود (مگر اعتبارش هم تمام شده باشد).

## How it runs / نحوهٔ اجرا

The panel runs a background maintenance pass every
`KIAN_MAINTENANCE_INTERVAL` seconds (default `3600`) that applies due resets
and then disables expired/over-quota users. Set `KIAN_DISABLE_MAINTENANCE=1`
to opt out (e.g. multi-worker deploys that schedule it externally via the
`POST /api/users/apply-resets` and `POST /api/users/auto-disable` endpoints).

> Resets always run **before** the over-quota check, so a user whose
> allowance just rolled over is restored rather than disabled.

## In the panel / در پنل

The user form has a **«ریستِ دوره‌ای حجم» / “Periodic traffic reset”** drop-down
(none / daily / weekly / monthly) next to the config-type selector.
