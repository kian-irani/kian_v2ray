# Versioning & Releases — kian_v2ray

This project follows [Semantic Versioning 2.0.0](https://semver.org/).

## What carries a version

| Component | Source of truth | Tag scheme |
|-----------|-----------------|------------|
| Installer + server scripts | `VERSION` → `SCRIPT_VERSION` | `vX.Y.Z` (git tag) |
| Pinned Xray-core | `VERSION` → `XRAY_VERSION` | upstream version |
| Kv2m desktop app | `kv2m/` (its own header) | `kv2m-X.Y.Z` |
| Landing site | not versioned (rolling) | — |

## When to bump

- **MAJOR** — a breaking change to the install/CLI contract (flags removed,
  config layout changed in a non-migratable way).
- **MINOR** — a new backward-compatible feature (new protocol, new CLI command,
  panel feature).
- **PATCH** — a bug fix or hardening that doesn't change the public contract.

## How to cut a release

```bash
# 1. bump + tag (validates bash/js first)
scripts/release.sh minor          # or major|patch|X.Y.Z

# 2. write the CHANGELOG entry under the new version heading

# 3. publish (CI builds from the tag)
git push origin main --tags
```

Each tag triggers the `validate.yml` checks. A GitHub Release is created from
the tag; the installer reads `VERSION` at runtime so `kian-v2ray update` knows
when a newer version exists.

## Git tagging policy

- Tags are annotated (`git tag -a`) and immutable once pushed.
- The CHANGELOG `[unreleased]` heading is renamed to the version on release.
- Never re-tag a published version; cut a new PATCH instead.
