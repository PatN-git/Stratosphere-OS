#!/bin/bash
# L1 - deterministic install/scaffold/sync E2E for the canonical dist/skills bundle, for
# Linux/CI. Mirrors run-L1.ps1:
#   Track B (plain copy)  {.claude/skills, .agents/skills} x {local, global}, + scaffold/sync
#   Track A (npx skills add ./dist/skills --copy -y)  same 2x2 matrix; SKIPs without npx/network
#   Track D (Antigravity bridge, scripts/install-antigravity-bridge.sh --target)
# There is no per-host installer any more: a skills installer (skills.sh, marketplace, or
# a plain copy) only places skill folders, and stratosphere-setup carries its own payload.
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

[ -d "$REPO/dist/skills" ] || "$PY" "$REPO/build/build.py" >/dev/null

assert_bundle_tree() { # $1 skills dir  $2 label prefix
  local base="$1" t="$2"
  assert "$t: 27 skills" "$([ "$(ls -1 "$base"/*/SKILL.md 2>/dev/null | wc -l | tr -d " ")" = "27" ] && echo 1 || echo 0)"
  assert "$t: 23 HITL sidecars" "$([ "$(ls -1 "$base"/*/agents/openai.yaml 2>/dev/null | wc -l | tr -d " ")" = "23" ] && echo 1 || echo 0)"
  assert "$t: micro-tdd skill" "$(exists "$base/micro-tdd/SKILL.md")"
  assert "$t: no legacy commands/workflows dir" "$([ -d "$base/commands" ] || [ -d "$base/workflows" ] && echo 0 || echo 1)"
  assert "$t: setup carries scaffold.py" "$(exists "$base/stratosphere-setup/scripts/scaffold.py")"
  assert "$t: setup carries versions.json" "$(exists "$base/stratosphere-setup/versions.json")"
  assert "$t: setup carries templates" "$(exists "$base/stratosphere-setup/assets/templates/memory")"
}

assert_scaffold_tree() { # $1 proj
  local p="$1"
  for f in AGENTS.md CLAUDE.md GEMINI.md .gitignore .gitattributes index.md; do
    assert "scaffold: $f" "$(exists "$p/$f")"
  done
  assert "scaffold: .memory 9 md" "$([ "$(nmd "$p/.memory")" = "9" ] && echo 1 || echo 0)"
  assert "scaffold: .agents/rules 3 md" "$([ "$(nmd "$p/.agents/rules")" = "3" ] && echo 1 || echo 0)"
  assert "scaffold: .agents/skills 27 SKILL.md" "$([ "$(ls -1 "$p"/.agents/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d " ")" = "27" ] && echo 1 || echo 0)"
  assert "scaffold: no legacy .agents/workflows" "$([ -d "$p/.agents/workflows" ] && echo 0 || echo 1)"
  assert "scaffold: copilot skills 27" "$([ "$(ls -1 "$p"/.github/copilot/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d " ")" = "27" ] && echo 1 || echo 0)"
  assert "scaffold: setup payload not copied into copilot skill" "$([ -e "$p/.github/copilot/skills/stratosphere-setup/scripts" ] && echo 0 || echo 1)"
  assert "scaffold: validate_memory.py" "$(exists "$p/.agents/scripts/validate_memory.py")"
  assert "scaffold: okf_view.py" "$(exists "$p/.agents/scripts/okf_view.py")"
  assert "scaffold: okf_viewer/generator.py" "$(exists "$p/.agents/scripts/okf_viewer/generator.py")"
  assert "scaffold: docs/discovery/.gitkeep" "$(exists "$p/docs/discovery/.gitkeep")"
  assert "scaffold: docs/knowledge/index.md" "$(exists "$p/docs/knowledge/index.md")"
  assert "scaffold: docs/nightly/index.md" "$(exists "$p/docs/nightly/index.md")"
  grep -q '\*\.work\.md' "$p/.gitignore" 2>/dev/null && assert "scaffold: .gitignore has *.work.md" 1 || assert "scaffold: .gitignore has *.work.md" 0
}

run_cell() { # $1 host dir (.claude|.agents)  $2 scope
  local hostdir="$1" scope="$2"
  echo ""; echo "== $hostdir / $scope (sh) =="
  local proj home base bundle
  proj="$(mktemp -d)"
  if [ "$scope" = "global" ]; then home="$(mktemp -d)"; base="$home/$hostdir/skills"; else base="$proj/$hostdir/skills"; fi

  # Track B: plain copy of the canonical bundle, exactly as documented.
  mkdir -p "$base" && cp -r "$REPO"/dist/skills/* "$base"/
  bundle="$base/stratosphere-setup"

  assert_bundle_tree "$base" "install"

  # scaffold
  if [ "$scope" = "local" ]; then
    ( cd "$proj" && "$PY" "$bundle/scripts/scaffold.py" >/tmp/sc.out 2>&1 )
  else
    ( cd "$proj" && HOME="$home" USERPROFILE="$home" "$PY" "$bundle/scripts/scaffold.py" >/tmp/sc.out 2>&1 )
  fi
  grep -q 'StratosphereOS scaffold (applied)' /tmp/sc.out && assert "scaffold reports applied" 1 || assert "scaffold reports applied" 0
  assert_scaffold_tree "$proj"

  # sync (dry-run, offline)
  local g=""; [ "$scope" = "global" ] && g="--global"
  if [ "$scope" = "local" ]; then
    ( cd "$proj" && "$PY" "$bundle/scripts/sync_skills.py" --category system --dry-run $g >/tmp/sy.out 2>&1 )
  else
    ( cd "$proj" && HOME="$home" USERPROFILE="$home" "$PY" "$bundle/scripts/sync_skills.py" --category system --dry-run $g >/tmp/sy.out 2>&1 )
  fi
  grep -q "($scope scope)" /tmp/sy.out && assert "sync reports $scope scope" 1 || assert "sync reports $scope scope" 0
  grep -q '\[DRY\]' /tmp/sy.out && assert "sync is dry-run" 1 || assert "sync is dry-run" 0

  rm -rf "$proj"; [ "$scope" = "global" ] && rm -rf "$home"
}

# Track A: the skills.sh CLI installing the local bundle. No -a flag targets the universal
# .agents/skills; -a claude-code targets .claude/skills; -g redirects into HOME.
run_trackA_cell() { # $1 host dir (.claude|.agents)  $2 scope
  local hostdir="$1" scope="$2" agent="" g="" proj home base rc
  [ "$hostdir" = ".claude" ] && agent="-a claude-code"
  [ "$scope" = "global" ] && g="-g"
  echo ""; echo "== Track A: npx skills add / $hostdir / $scope (sh) =="
  proj="$(mktemp -d)"; home="$(mktemp -d)"
  if [ "$scope" = "global" ]; then base="$home/$hostdir/skills"; else base="$proj/$hostdir/skills"; fi
  # shellcheck disable=SC2086
  ( cd "$proj" && HOME="$home" USERPROFILE="$home" npx -y skills add "$REPO/dist/skills" --copy -y $agent $g >"$home/npx-add.out" 2>&1 )
  rc=$?
  assert "trackA: npx skills add exit 0 ($hostdir/$scope)" "$([ "$rc" = 0 ] && echo 1 || echo 0)"
  assert_bundle_tree "$base" "trackA"
  rm -rf "$proj" "$home"
}

run_trackA() {
  # One npm cache for all four cells: the skills CLI is fetched once, not per cell.
  local cache prev="${npm_config_cache-}" had="${npm_config_cache+1}"
  cache="$(mktemp -d)"; export npm_config_cache="$cache"
  if ! command -v npx >/dev/null 2>&1; then
    echo ""; echo "  SKIP  Track A: npx not found (install Node.js to cover 'npx skills add')"
  elif ! npx -y skills --version >/dev/null 2>&1; then
    echo ""; echo "  SKIP  Track A: skills CLI unavailable (offline or npm registry unreachable)"
  else
    for hostdir in .claude .agents; do
      for scope in local global; do run_trackA_cell "$hostdir" "$scope"; done
    done
  fi
  rm -rf "$cache"
  if [ -n "$had" ]; then export npm_config_cache="$prev"; else unset npm_config_cache; fi
}

# Track D: the Antigravity bridge copies the bundle to an explicit --target; re-running replaces
# shipped skills (drops stale files) and leaves foreign skills untouched.
run_trackD_cell() {
  echo ""; echo "== Track D: antigravity bridge --target (sh) =="
  local root tgt rc; root="$(mktemp -d)"; tgt="$root/skills"
  bash "$REPO/scripts/install-antigravity-bridge.sh" --target "$tgt" >"$root/bridge.out" 2>&1
  rc=$?
  assert "trackD: bridge exit 0" "$([ "$rc" = 0 ] && echo 1 || echo 0)"
  grep -q 'Copied 27 skills' "$root/bridge.out" && assert "trackD: bridge reports 27 copied" 1 || assert "trackD: bridge reports 27 copied" 0
  assert_bundle_tree "$tgt" "trackD"
  mkdir -p "$tgt/foreign-skill"; echo x > "$tgt/foreign-skill/SKILL.md"; echo x > "$tgt/micro-tdd/stale.txt"
  bash "$REPO/scripts/install-antigravity-bridge.sh" --target "$tgt" >/dev/null 2>&1
  assert "trackD: rerun preserves foreign skill" "$(exists "$tgt/foreign-skill/SKILL.md")"
  assert "trackD: rerun drops stale file in shipped skill" "$([ -e "$tgt/micro-tdd/stale.txt" ] && echo 0 || echo 1)"
  rm -rf "$root"
}

for hostdir in .claude .agents; do
  for scope in local global; do
    run_cell "$hostdir" "$scope"
  done
done
run_trackA
run_trackD_cell

echo ""; echo "----- install-harness L1 (sh): $pass passed, $fail failed -----"
if [ "$fail" -gt 0 ]; then printf '  - %s\n' "${failures[@]}"; exit 1; fi
exit 0
