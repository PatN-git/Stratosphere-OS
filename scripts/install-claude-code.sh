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

# Create directories
mkdir -p "$COMMANDS_DIR"
mkdir -p "$SKILLS_DIR"
mkdir -p "$PLUGINS_DIR"

# Copy commands
if [ -d "$REPO_ROOT/dist/claude-code/commands" ]; then
    cp -rf "$REPO_ROOT/dist/claude-code/commands/"* "$COMMANDS_DIR/"
fi

# Copy skills
if [ -d "$REPO_ROOT/dist/claude-code/skills" ]; then
    cp -rf "$REPO_ROOT/dist/claude-code/skills/"* "$SKILLS_DIR/"
fi

# Stage full plugin to plugins/stratosphere-os/
cp -rf "$REPO_ROOT/dist/claude-code/"* "$PLUGINS_DIR/"

echo "Successfully installed to $CLAUDE_DIR. Restart Claude Code for the commands to load."
