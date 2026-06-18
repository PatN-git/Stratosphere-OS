#!/bin/bash
# L1 - deterministic install/scaffold/sync E2E (bash installers), for Linux/CI.
# Mirrors run-L1.ps1: {claude-code, antigravity} x {local, global}.
# Isolation: temp project per cell; --global cells redirect HOME to a temp dir
# (bash honours a runtime HOME, and Python's Path.home() uses HOME on POSIX).
# The current scaffold.py does no system mutation, so no venv is needed.
#
#   bash tests/install-harness/run-L1.sh
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
PY="${PYTHON:-python3}"
pass=0; fail=0; failures=()

assert() { # $1 label  $2 cond(0/1)
  if [ "$2" = "1" ]; then echo "  PASS  $1"; pass=$((pass+1));
  else echo "  FAIL  $1"; fail=$((fail+1)); failures+=("$1"); fi
}
exists()  { [ -e "$1" ] && echo 1 || echo 0; }
nmd()     { local n; n=$(find "$1" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l); echo "$((n))"; }

[ -d "$REPO/dist/claude-code" ] && [ -d "$REPO/dist/antigravity" ] || "$PY" "$REPO/build/build.py" >/dev/null

assert_scaffold_tree() { # $1 proj
  local p="$1"
  for f in AGENT.md CLAUDE.md GEMINI.md .gitignore .gitattributes index.md; do
    assert "scaffold: $f" "$(exists "$p/$f")"
  done
  assert "scaffold: .memory 9 md" "$([ "$(nmd "$p/.memory")" = "9" ] && echo 1 || echo 0)"
  assert "scaffold: .agents/rules 3 md" "$([ "$(nmd "$p/.agents/rules")" = "3" ] && echo 1 || echo 0)"
  assert "scaffold: .agents/workflows 15 md" "$([ "$(nmd "$p/.agents/workflows")" = "15" ] && echo 1 || echo 0)"
  assert "scaffold: validate_memory.py" "$(exists "$p/.agents/scripts/validate_memory.py")"
  assert "scaffold: okf_view.py" "$(exists "$p/.agents/scripts/okf_view.py")"
  assert "scaffold: okf_viewer/generator.py" "$(exists "$p/.agents/scripts/okf_viewer/generator.py")"
  assert "scaffold: docs/discovery/.gitkeep" "$(exists "$p/docs/discovery/.gitkeep")"
  assert "scaffold: docs/knowledge/index.md" "$(exists "$p/docs/knowledge/index.md")"
  grep -q '\*\.work\.md' "$p/.gitignore" 2>/dev/null && assert "scaffold: .gitignore has *.work.md" 1 || assert "scaffold: .gitignore has *.work.md" 0
}

run_cell() { # $1 tool  $2 scope
  local tool="$1" scope="$2"
  echo ""; echo "== $tool / $scope (sh) =="
  local proj home plugin base
  proj="$(mktemp -d)"
  if [ "$scope" = "global" ]; then home="$(mktemp -d)"; fi

  # install
  if [ "$scope" = "local" ]; then
    ( cd "$proj" && bash "$REPO/scripts/install-$tool.sh" --local >/dev/null )
  else
    # USERPROFILE too: on Windows git-bash, Python's Path.home() reads USERPROFILE, not HOME.
    HOME="$home" USERPROFILE="$home" bash "$REPO/scripts/install-$tool.sh" --global >/dev/null
  fi

  # install-tree assertions + resolve plugin root
  if [ "$tool" = "claude-code" ]; then
    if [ "$scope" = "local" ]; then base="$proj/.claude"; else base="$home/.claude"; fi
    plugin="$base/plugins/stratosphere-os"
    assert "install: 16 commands" "$([ "$(nmd "$base/commands")" = "16" ] && echo 1 || echo 0)"
    assert "install: micro-tdd skill" "$(exists "$base/skills/micro-tdd")"
  else
    if [ "$scope" = "local" ]; then plugin="$proj/.agents/plugins/stratosphere-os"; else plugin="$home/.gemini/config/plugins/stratosphere-os"; fi
    assert "install: plugin.json" "$(exists "$plugin/plugin.json")"
    assert "install: 15 workflows" "$([ "$(nmd "$plugin/workflows")" = "15" ] && echo 1 || echo 0)"
    assert "install: no stratosphere-setup.md in workflows" "$([ -e "$plugin/workflows/stratosphere-setup.md" ] && echo 0 || echo 1)"
  fi
  assert "install: bundled scaffold.py" "$(exists "$plugin/scripts/scaffold.py")"

  # scaffold
  if [ "$scope" = "local" ]; then
    ( cd "$proj" && "$PY" "$plugin/scripts/scaffold.py" >/tmp/sc.out 2>&1 )
  else
    ( cd "$proj" && HOME="$home" USERPROFILE="$home" "$PY" "$plugin/scripts/scaffold.py" >/tmp/sc.out 2>&1 )
  fi
  grep -q 'StratosphereOS scaffold (applied)' /tmp/sc.out && assert "scaffold reports applied" 1 || assert "scaffold reports applied" 0
  assert_scaffold_tree "$proj"

  # sync (dry-run, offline)
  local g=""; [ "$scope" = "global" ] && g="--global"
  if [ "$scope" = "local" ]; then
    ( cd "$proj" && "$PY" "$plugin/scripts/sync_skills.py" --category system --dry-run $g >/tmp/sy.out 2>&1 )
  else
    ( cd "$proj" && HOME="$home" USERPROFILE="$home" "$PY" "$plugin/scripts/sync_skills.py" --category system --dry-run $g >/tmp/sy.out 2>&1 )
  fi
  grep -q "($scope scope)" /tmp/sy.out && assert "sync reports $scope scope" 1 || assert "sync reports $scope scope" 0
  grep -q '\[DRY\]' /tmp/sy.out && assert "sync is dry-run" 1 || assert "sync is dry-run" 0

  rm -rf "$proj"; [ "$scope" = "global" ] && rm -rf "$home"
}

for tool in claude-code antigravity; do
  for scope in local global; do
    run_cell "$tool" "$scope"
  done
done

echo ""; echo "----- install-harness L1 (sh): $pass passed, $fail failed -----"
if [ "$fail" -gt 0 ]; then printf '  - %s\n' "${failures[@]}"; exit 1; fi
exit 0
