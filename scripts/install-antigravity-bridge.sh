#!/bin/bash
# Antigravity fallback bridge (BT-120): skills.sh installs globally to ~/.gemini/antigravity/skills/,
# but Antigravity discovers skills under ~/.gemini/config/ (vercel-labs/skills#633). Until that is
# fixed upstream, physically copy dist/skills/* into ~/.gemini/config/skills/ (no symlinks).
#
#   bash scripts/install-antigravity-bridge.sh [--target <skills-dir>]
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/dist/skills"
TARGET="$HOME/.gemini/config/skills"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)
            if [ $# -lt 2 ]; then
                echo "Error: --target requires a <skills-dir> value." >&2
                exit 1
            fi
            TARGET="$2"; shift 2 ;;
        --target=?*)
            TARGET="${1#--target=}"; shift ;;
        *)
            echo "Error: unrecognised argument '$1'. Usage: install-antigravity-bridge.sh [--target <skills-dir>]" >&2
            exit 1 ;;
    esac
done

if [ ! -d "$SRC" ] || [ -z "$(find "$SRC" -type f | head -1)" ]; then
    echo "Error: dist/skills is missing or empty. Please run 'python build/build.py' first." >&2
    exit 1
fi

# Replace each shipped skill (drops stale files inside it); leave foreign skills untouched.
mkdir -p "$TARGET"
count=0
for skill in "$SRC"/*/; do
    name="$(basename "$skill")"
    rm -rf "${TARGET:?}/$name"
    cp -r "$skill" "$TARGET/$name"
    count=$((count + 1))
done

echo "Copied $count skills to $TARGET. Restart Google Antigravity (or start a new agent session), then run /stratosphere-setup in your project."
