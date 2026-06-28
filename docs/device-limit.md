# Device limit (HWID) / سقفِ دستگاه (FR-S2)

**EN** — Each user can have a **device limit**: the maximum number of distinct
devices that may use their account. `0` (default) means unlimited. The panel
keeps a per-user **device registry** so you can see and reset paired devices.

- A **known** device is always allowed (its `last_seen` is refreshed).
- A **new** device is allowed only while the user is under their limit.
- Over the limit, a new device is **denied and not stored**.
- **Resetting** a device (one or all) frees a slot so the user can re-pair —
  e.g. after switching phones.

**FA** — هر کاربر می‌تواند **سقفِ دستگاه** داشته باشد: بیشترین تعدادِ دستگاهِ
مجزا. مقدارِ `0` یعنی نامحدود. پنل فهرستِ دستگاه‌های هر کاربر را نگه می‌دارد تا
بتوانید ببینید و ریست کنید. دستگاهِ شناخته‌شده همیشه مجاز است؛ دستگاهِ جدید فقط
تا وقتی زیرِ سقف است مجاز است؛ ریستِ دستگاه یک جا آزاد می‌کند (مثلاً تعویضِ گوشی).

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/users/{name}/devices` | list devices + the user's limit |
| `DELETE` | `/api/users/{name}/devices` | forget all devices |
| `DELETE` | `/api/users/{name}/devices?device_id=…` | forget one device |

The panel user form has a **«سقفِ دستگاه» / “Device limit”** field next to the
IP limit.

## Enforcement wiring / اتصالِ enforcement

`repo.register_device(...)` is the **decision** function (allow/deny + bump
`last_seen`) and the single source of truth for the registry. The point that
*observes* a real connection and calls it — the node/Xray side reporting a
device id — is the integration hook and is **⏳ field-test** (the panel
management, limit and registry are tested and ready).
