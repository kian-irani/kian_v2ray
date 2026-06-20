#!/usr/bin/env bash
# release.sh — Semantic-Versioning helper for kian_v2ray.
#
# Bumps SCRIPT_VERSION in ./VERSION, writes/refreshes a CHANGELOG heading,
# commits, and creates an annotated git tag (vX.Y.Z). CI builds the release
# from the tag. Never pushes on its own — print the push command for the human.
#
# Usage:
#   scripts/release.sh patch        # 2.1.0 -> 2.1.1
#   scripts/release.sh minor        # 2.1.0 -> 2.2.0
#   scripts/release.sh major        # 2.1.0 -> 3.0.0
#   scripts/release.sh 2.3.0        # set explicitly
#
# Honors SemVer: MAJOR breaking, MINOR features, PATCH fixes.
set -euo pipefail

cd "$(dirname "$0")/.."
VERSION_FILE="VERSION"

cur="$(grep -E '^SCRIPT_VERSION=' "$VERSION_FILE" | head -1 | cut -d= -f2)"
[ -n "$cur" ] || { echo "cannot read SCRIPT_VERSION from $VERSION_FILE" >&2; exit 1; }
IFS='.' read -r MA MI PA <<<"$cur"

arg="${1:-patch}"
case "$arg" in
  major) new="$((MA+1)).0.0" ;;
  minor) new="${MA}.$((MI+1)).0" ;;
  patch) new="${MA}.${MI}.$((PA+1))" ;;
  [0-9]*.[0-9]*.[0-9]*) new="$arg" ;;
  *) echo "usage: release.sh {major|minor|patch|X.Y.Z}" >&2; exit 2 ;;
esac

echo "kian release: $cur -> $new"
# Update VERSION in place (portable sed).
tmp="$(mktemp)"
sed "s/^SCRIPT_VERSION=.*/SCRIPT_VERSION=${new}/" "$VERSION_FILE" >"$tmp"
mv "$tmp" "$VERSION_FILE"

# Validate before tagging.
bash -n install.sh
bash -n scripts/kian-v2ray
node --check assets/js/app.js

git add -A
git commit -m "release: v${new}" || echo "(nothing to commit)"
git tag -a "v${new}" -m "kian_v2ray v${new}"

echo
echo "Tagged v${new}. To publish:"
echo "  git push origin main --tags"
