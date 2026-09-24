#!/bin/bash
set -e

# Resolve repo root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Verify build output exists
BUILD_DIR="$REPO_ROOT/dist/claude-code"
if [ ! -d "$BUILD_DIR" ] || [ -z "$(find "$BUILD_DIR" -type f | head -1)" ]; then
    echo "ERROR: dist/claude-code is missing or empty — run 'python build/build.py' first." >&2
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
    CLAUDE_DIR="$HOME/.claude"
    echo "Installing globally under ~/.claude/..."
else
    CLAUDE_DIR="$RESOLVED_TARGET/.claude"
    echo "Installing locally under $CLAUDE_DIR..."
fi

COMMANDS_DIR="$CLAUDE_DIR/commands"
SKILLS_DIR="$CLAUDE_DIR/skills"
PLUGINS_DIR="$CLAUDE_DIR/plugins/stratosphere-os"

# Replace each shipped entry wholesale (drops stale files inside it, e.g. a
# template removed upstream) while preserving foreign entries in shared dirs.
shopt -s dotglob  # include dotfiles/dirs (e.g. .claude-plugin/), matching the ps1 -Force
overlay() {  # overlay <src-dir> <dest-dir>
    mkdir -p "$2"
    for item in "$1"/*; do
        [ -e "$item" ] || continue
        rm -rf "$2/$(basename "$item")"
        cp -rf "$item" "$2/"
    done
}

[ -d "$BUILD_DIR/commands" ] && overlay "$BUILD_DIR/commands" "$COMMANDS_DIR"
[ -d "$BUILD_DIR/skills" ] && overlay "$BUILD_DIR/skills" "$SKILLS_DIR"

# Stage full plugin to plugins/stratosphere-os/ (skills/ merged per skill).
mkdir -p "$PLUGINS_DIR"
for item in "$BUILD_DIR"/*; do
    name="$(basename "$item")"
    if [ "$name" = "skills" ] && [ -d "$item" ]; then
        overlay "$item" "$PLUGINS_DIR/skills"
    else
        rm -rf "$PLUGINS_DIR/$name"
        cp -rf "$item" "$PLUGINS_DIR/"
    fi
done

# v4 retired two top-level bundle dirs. The overlay only replaces what the CURRENT
# bundle ships, so a dir we no longer ship is never touched and its stale v3 contents
# survive an upgrade -- leaving /0a_start-session resolving from the plugin alongside
# /0a-start-session. Both dirs are unambiguously framework-owned.
for retired in workflows commands; do
    if [ -d "$PLUGINS_DIR/$retired" ]; then
        echo "removing retired $retired/ from plugin dir (v3 leftovers)"
        rm -rf "${PLUGINS_DIR:?}/$retired"
    fi
done

echo "Successfully installed to $CLAUDE_DIR. Restart Claude Code for the commands to load."
