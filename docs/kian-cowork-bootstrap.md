# Kian Cowork Bootstrap

> این فایل را در ابتدای پروژه‌های بعدی بارگذاری کن (یا محتوایش را در `CLAUDE.md` پروژه بگذار)
> تا Claude خودکار از پلاگین‌ها و skillهای زیر استفاده کند.

## اصل کار: اول Skill، بعد کار

قبل از هر کارِ بیشتر از یک پاسخ مکالمه‌ای، اول بررسی کن کدام Skill می‌خورد و **همان لحظه** صدایش بزن.
Skillهای شخصی بر عمومی اولویت دارند. زبان توضیح فارسی، کد انگلیسی، بدون preamble، قاطع.

## فاز کار روی هر تسک

1. **brainstorming** (`superpowers:brainstorming`) — قبل از هر کار خلاقانه/ساخت، نیت و طراحی را روشن کن.
2. **writing-plans** (`superpowers:writing-plans`) — از spec یک پلن مرحله‌به‌مرحله بساز.
3. **model-route** (`ecc:model-route`) — تیر مدل مناسب را انتخاب کن (haiku/sonnet/opus بر اساس پیچیدگی).
4. پیاده‌سازی با رعایت **karpathy-guidelines** (`andrej-karpathy-skills:karpathy-guidelines`) — تغییر جراحی، بدون پیچیدگی اضافه، فرضیات را شفاف کن، معیار موفقیت تعریف کن.
5. **requesting-code-review** (`superpowers:requesting-code-review`) — قبل از merge بازبینی بخواه.
6. **verification-before-completion** — قبل از ادعای «تمام شد»، با شواهد تأیید کن (تست/build/diff).

## ابزارها و پلاگین‌های جانبی

| نیاز | Skill/Plugin |
|------|--------------|
| کشف پلاگین مناسب | `ruflo-core:discover-plugins` |
| سلامت محیط Ruflo | `ruflo-core:ruflo-doctor` |
| حافظهٔ معنایی (store/search/recall) | `ruflo-rag-memory:ruflo-memory` · `memory-bridge` |
| worker پس‌زمینه (audit/optimize/testgaps/map) | `ruflo-loop-workers:ruflo-loop` |
| اتوماسیون مرورگر (تست UI/اسکرپ) | `ruflo-browser:ruflo-browser` |
| یادداشت‌برداری Obsidian | `obsidian-cli:obsidian-cli` |
| حلقهٔ عامل خودگردان | `ecc:autonomous-agent-harness` |
| ساخت خروجی docx/pptx/xlsx/pdf | skillهای هم‌نام — اول محتوا، بعد فرمت |

## نصب پلاگین‌ها (Cowork / Claude Code)

```
/plugin marketplace add ruvnet/ruflo
/plugin install ruflo-core@ruflo
/plugin install ruflo-rag-memory@ruflo
/plugin install ruflo-loop-workers@ruflo
/plugin install ruflo-browser@ruflo
# superpowers / ecc / andrej-karpathy / obsidian-cli از مارکت‌پلیس‌های مربوطه
```

## توکن‌ها و سرورها

برای جزئیات محرمانه (GitHub/Cloudflare/Telegram/SSH) به `CLAUDE.md` ورک‌اسپیس مراجعه کن — اینجا تکرار نمی‌شود.
