# Contributing to KIAN V2Ray

Thanks for helping! This project values privacy, simplicity, and never breaking
what already works.

## Ground rules

- **Client-side keys are sacred.** Never add code that sends a private key to a
  server. The browser/app generates keys; the server only ever sees public data.
- **No secrets in the repo.** CI runs a secret scan; keep tokens in env/Settings.
- **Don't break the installer.** `bash -n install.sh` must stay green; the jsdom
  smoke test must keep generating a valid payload.

## Local checks (what CI runs)

```bash
bash -n install.sh scripts/kian-v2ray scripts/watchdog.sh
node --check assets/js/app.js assets/js/i18n.js
python3 -m pytest -q
```

For the panel:

```bash
python3 -m pip install -r panel/requirements.txt
uvicorn panel.main:app --reload --port 8443   # http://localhost:8443/docs
```

## Project layout

- `install.sh`, `scripts/` — the one-command server installer + CLI.
- `core/` — shared, stdlib-only logic (db, logging, audit, protocols, cluster, plugins).
- `panel/` — FastAPI web panel + dark-glass dashboard (`panel/web/`).
- `kv2m/` — desktop manager; `app/` — Kv2m Flutter mobile client.
- `node-agent/` — per-VPS agent for multi-server.
- `monitoring/` — Prometheus/Grafana stack.

## Adding a protocol or feature without touching core

Use the plugin system (`core/plugins.py`):

```python
from core.plugins import register

@register("protocol", "my-proto")
def build_my_proto(**kw):
    return {"type": "my-proto", **kw}
```

Drop modules in a `kian_plugins` package and `core.plugins.discover()` loads them.

## Commits & releases

- Conventional commits (`feat:`, `fix:`, `docs:`…).
- Versioning is SemVer; cut releases with `scripts/release.sh` (see `docs/VERSIONING.md`).
- Open a PR; CI (`validate.yml` + `security.yml`) must be green.

## Code of conduct

Be kind and constructive. Assume good faith. Harassment is not tolerated.
