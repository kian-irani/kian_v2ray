# Adding a language (Translations)

KIAN is fully bilingual (FA/EN) today. Adding a language (ru, zh, ar, …) is
straightforward because every surface uses a single flat key→string map. No
Crowdin/Weblate account is required to contribute — just edit the maps and open
a PR. (A hosted platform can be layered on later; the file format below is what
it would sync.)

## The three string sources

| Surface | File | Format |
|---------|------|--------|
| Web generator | [`assets/js/i18n.js`](../assets/js/i18n.js) | JS object: `key: { fa, en }` |
| Mobile app (Kv2m) | [`app/lib/i18n.dart`](../app/lib/i18n.dart) | `'key': ['fa', 'en']` |
| Desktop (Kv2m) | [`kv2m/i18n.py`](../kv2m/i18n.py) | `STRINGS["en"]` / `STRINGS["fa"]` dicts |

## How to add, e.g. Arabic (`ar`)

### Web (`i18n.js`)
Each entry currently has `fa`/`en`. Add an `ar` field to each key, then add `ar`
to the language toggle list. The toggle reads `data-i18n` attributes — no markup
changes needed beyond the dictionary.

### Desktop (`i18n.py`)
Add a third top-level block `STRINGS["ar"] = { ... }` mirroring the `en` keys,
then add `ar` to the language picker in `app.py` (`_ask_language`).

### Mobile (`i18n.dart`)
The map is `'key': [fa, en]`. To add a third locale, extend the list to
`[fa, en, ar]` and update `Strings.t()` to index by a `lang` switch, plus add
`Locale('ar')` to `supportedLocales` in `main.dart`.

## Rules

- **Keep keys identical** across all three files — same key = same meaning.
- **Don't translate** code identifiers, URLs, protocol names (VLESS, Reality,
  Hysteria2), or CLI commands.
- RTL languages (fa, ar) must keep `dir="rtl"` handling — the apps already switch
  direction by language.
- Run the validators before a PR:
  - `node --check assets/js/i18n.js`
  - `python3 -m py_compile kv2m/i18n.py`
  - confirm every key referenced in code exists (no missing-key fallbacks).

## Why no Crowdin yet

A hosted TMS adds value only once there are several active translators. Until
then, PRs against these files are simpler and reviewable. The flat format is
TMS-ready, so migrating later is a mechanical export.
