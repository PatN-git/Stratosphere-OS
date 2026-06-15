#!/bin/bash
set -e

# Resolve repo root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Verify build output exists
BUILD_DIR="$REPO_ROOT/dist/antigravity"
if [ ! -d "$BUILD_DIR" ] || [ -z "$(find "$BUILD_DIR" -type f | head -1)" ]; then
    echo "Error: dist/antigravity is missing or empty. Please run 'python build/build.py' first." >&2
    exit 1
fi

SCOPE=""
TARGET=""
# Parse command line args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --global)
            SCOPE="global"
            shift
            ;;
        --local)
            SCOPE="local"
            shift
            ;;
        --target)
            TARGET="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Prompt if not specified
if [ -z "$SCOPE" ]; then
    if [ -t 0 ]; then
        read -p "Install StratosphereOS globally or locally for the current project? [global/local]: " choice
        choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]')
        if [ "$choice" = "local" ]; then
            SCOPE="local"
        else
            SCOPE="global"
        fi
    else
        # default to global if non-interactive
        SCOPE="global"
    fi
fi

RESOLVED_TARGET="${TARGET:-$(pwd)}"

if [ "$SCOPE" = "global" ]; then
    # Confirmed against installed Antigravity plugins (android-cli, chrome-devtools, ...).
    PLUGIN_DIR="$HOME/.gemini/config/plugins/stratosphere-os"
    echo "Installing globally under ~/.gemini/config/plugins/stratosphere-os/..."
else
    PLUGIN_DIR="$RESOLVED_TARGET/.agents/plugins/stratosphere-os"
    echo "Installing locally under $PLUGIN_DIR..."
fi

# Overlay the bundle: replace every item we ship (dropping stale orphans such as
# renamed workflow files within those folders), but PRESERVE foreign entries.
# In particular, external skills fetched into skills/ by `sync_skills.py --global`
# on Antigravity must survive a plugin update, so skills/ is merged per-skill.
mkdir -p "$PLUGIN_DIR"
SRC="$REPO_ROOT/dist/antigravity"
for item in "$SRC"/*; do
    name="$(basename "$item")"
    if [ "$name" = "skills" ] && [ -d "$item" ]; then
        mkdir -p "$PLUGIN_DIR/skills"
        for skill in "$item"/*; do
            sname="$(basename "$skill")"
            rm -rf "$PLUGIN_DIR/skills/$sname"
            cp -rf "$skill" "$PLUGIN_DIR/skills/$sname"
        done
    else
        rm -rf "$PLUGIN_DIR/$name"
        cp -rf "$item" "$PLUGIN_DIR/$name"
    fi
done

echo "Successfully installed to $PLUGIN_DIR. Restart Google Antigravity (or start a new agent session), then run /stratosphere-setup in your project."
