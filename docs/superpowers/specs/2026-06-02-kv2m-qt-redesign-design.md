# Design — kv2m 3.0: Qt Redesign + i18n

**Date:** 2026-06-02
**Status:** Approved (brainstorming) — pending spec review
**Author:** Kian + Claude

## 1. Problem & Goals

The kv2m desktop app works functionally but its UI (built with `customtkinter`) is not visually appealing. The user wants a genuinely graphical, polished desktop app in the style of **Termius** (clean layout, generous spacing, professional SSH-client feel) combined with the **NVIDIA app** green accent. The app must also be bilingual: code/strings in **English** as the base, with a **language picker on first launch** (English | فارسی), changeable later in Settings.

Goals:

- Rewrite the presentation layer in **PySide6/Qt** for real graphical polish (gradients, SVG icons, custom frameless title bar, hover/transition animations).
- Reuse the existing, tested config-generation and SSH logic **unchanged**.
- Add a clean i18n system (`en.json` / `fa.json`) with first-run language selection and RTL handling for Persian.
- Keep the GitHub Actions build/release pipeline working (tag `kv2m-v*`).
- Preserve full feature parity with the current app.

Non-goals: changing the install.sh server side, changing config semantics, or redesigning the web interactive page (separate effort).

## 2. Scope Decomposition

This request contains two independent subsystems:

- **Subsystem A (this spec):** the kv2m Qt redesign + i18n + verification.
- **Subsystem B (separate small deliverable):** a portable "cowork bootstrap" file that wires in the requested plugins/skills (`superpowers:writing-plans`, `superpowers:requesting-code-review`, `ecc:model-route`, `andrej-karpathy-skills:karpathy-guidelines`, `obsidian-cli:obsidian-cli`, `ecc:autonomous-agent-harness`) plus previously used ones, for loading into future projects. Delivered alongside A; it is a config/markdown file, not a software design.

## 3. Architecture

The current single 60KB+ `kv2m/kv2m.py` becomes a small, focused package. **All pure logic is ported verbatim** (it is already headless-tested):

```
kv2m/
  __main__.py          # entry: load settings, first-run language pick, launch app
  core/
    config.py          # build_config, generate, TLS_PROTOS, Caddyfile  (from current kv2m.py)
    links.py           # vless/vmess/trojan/ss + TLS link builders
    ssh.py             # SSH (paramiko) wrapper
    crypto.py          # gen_reality, gen_password
  ui/
    app.py             # QMainWindow, frameless window, sidebar wiring
    titlebar.py        # custom title bar (drag, min, close)
    sidebar.py         # icon nav
    widgets.py         # Card, Toast, LinkRow, QR view, reusable components
    pages/
      connect.py       # SSH connect + dashboard/status
      generate.py      # config generation (basic + advanced + TLS)
      manage.py        # user management commands
      settings.py      # language switch, theme, paths
      about.py
  i18n/
    strings.py         # tr(key) loader, current-language state, RTL flag
    en.json
    fa.json
  assets/
    icons/*.svg
  theme.qss            # global Qt stylesheet (Termius layout + NVIDIA green)
```

Boundaries: `core/` has zero Qt imports (pure, testable). `ui/` depends on `core/` and `i18n/` only. `i18n/` is standalone. This keeps each unit independently understandable and testable.

Settings (chosen language, last server host, theme) persist to a local JSON at the OS user-config path (e.g. `%APPDATA%/kv2m/settings.json`).

## 4. Visual Design System

Palette (Termius structure + NVIDIA accent):

| Token | Hex | Use |
|-------|-----|-----|
| `bg` | `#0B0F14` | window background |
| `panel` | `#12181F` | sidebar, title bar |
| `card` | `#161D26` | cards, inputs |
| `border` | `#222B36` | hairlines |
| `accent` | `#76B900` | NVIDIA green — primary actions |
| `accent-hover` | `#8FD400` | hover |
| `accent2` | `#1F6FEB` | secondary/info |
| `text` | `#E6EDF3` | primary text |
| `muted` | `#8A94A6` | secondary text |
| `error` | `#F85149` / `warn` | `#E3B341` |

Layout & components:

- **Frameless window** with a custom title bar (app icon + title left, min/close right, draggable).
- **Icon sidebar** (~72px) with SVG glyphs and a green active indicator bar; tooltips show page names.
- **Cards** with 12px radius, subtle 1px border, soft shadow; section headers with a faint top gradient.
- **Buttons**: filled green primary (hover lightening + slight scale), ghost secondary.
- **Inputs**: dark filled with green focus ring.
- **Hover/press transitions** via Qt property animations where cheap.
- Font: Inter/Segoe UI for Latin, Vazirmatn (bundled) for Persian; monospace (JetBrains Mono/Cascadia) for links/commands.

Pages mirror current functionality: Connect/Dashboard, Generate (with collapsible Advanced + TLS section), Manage, Settings, About.

## 5. Internationalization

- All user-facing strings live in `i18n/en.json` and `i18n/fa.json`, keyed (e.g. `generate.button`, `connect.ssh`).
- `tr(key)` returns the string for the current language; missing keys fall back to English (and are logged) so the app never shows a raw key.
- **First launch:** a centered modal "Choose language / انتخاب زبان" with two buttons (English | فارسی). Choice saved to settings; not shown again.
- **Settings page** lets the user switch language anytime (live preferred).
- **RTL:** when Persian is active, set layout direction RTL on relevant containers; numbers/links stay LTR.
- Base/source language is English; Persian is a translation layer.

## 6. Build & Release

- `build-kv2m.yml`: replace `customtkinter` dependency with `PySide6`; keep paramiko, cryptography, qrcode, Pillow. PyInstaller bundles PySide6 (`--collect-all PySide6` or the hook); include `i18n/*.json`, `assets/`, `theme.qss` via `--add-data`.
- Entry point becomes `kv2m/__main__.py` (or a thin `kv2m/kv2m.py` shim that calls it, to keep the workflow path stable).
- Output size grows to ~40-55MB (Qt). Acceptable.
- Version bumps to **3.0.0** (major). Tag `kv2m-v3.0.0` triggers the existing release flow (which now has `contents: write`).

## 7. Testing & Verification

- **Pure logic:** reuse the headless harness — `generate()` with Reality/WARP/SS/TLS produces valid config JSON, correct Caddyfile, correct links, no port collisions. Must stay green after the port.
- **Qt smoke test under xvfb:** construct `QApplication`, instantiate the main window and each page, switch language EN<->FA, open the generate flow with mock inputs — assert no exceptions. (Cannot judge final beauty headlessly.)
- **i18n check:** assert every key in `en.json` exists in `fa.json` and vice-versa; assert no page references a missing key.
- **Build check:** confirm the workflow builds and the release produces both exes.
- **Manual:** user runs the Windows exe and confirms look/feel; iterate on palette/spacing from feedback.

## 8. Risks & Honest Caveats

- This is a **large rewrite** of the UI layer (~all GUI code). Time-consuming, but it is the path to the "good software" the user wants. Pure logic reuse limits the risk to presentation.
- Final visual quality **cannot be verified in this environment** (no display); xvfb only proves it constructs without crashing. The user must review on Windows and give feedback for polish iterations.
- PySide6 increases the binary size and adds PyInstaller hook nuances; mitigated by `--collect-all PySide6` and a CI build check before tagging.
- Frameless custom title bar adds window-drag/resize handling; standard Qt patterns cover it.

## 9. Deliverables

1. Rewritten `kv2m/` Qt package with full feature parity + new visual system.
2. i18n system with first-run language picker (EN base, FA translation) + Settings switch.
3. Updated `build-kv2m.yml`, version 3.0.0, working release.
4. **Subsystem B:** `kian-cowork-bootstrap.md` — a loadable file referencing the requested + prior plugins/skills for future projects.
