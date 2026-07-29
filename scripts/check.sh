#!/usr/bin/env bash
# Single local gate — mirrors .github/workflows/build-guard.yml so that
# `bash scripts/check.sh` reproduces CI locally. Run from anywhere.
#
#   bash scripts/check.sh          # full deterministic gate (what CI runs)
#   pytest -m integration          # separately, for the live/network suite
#
# Requires: python 3.13, pytest (pip install pytest), node.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== build ==";           python build/build.py
echo "== validate ==";        python build/validate.py .
echo "== bump-guard ==";      python build/bump_guard.py . || echo "(bump-guard is PR-only; non-fatal locally)"
echo "== pytest ==";          python -m pytest            # pytest.ini restricts to -m 'not integration'
echo "== verify_scripts ==";  python tests/verify_scripts.py
echo "== plan-html (node) =="; node tests/verify_plan_html.mjs
echo "== install-harness L1 =="; bash tests/install-harness/run-L1.sh

echo "== dist drift =="
DRIFT="$(git status --porcelain dist/ .claude-plugin/marketplace.json)"
if [ -n "$DRIFT" ]; then
  echo "::error:: dist/ or marketplace.json out of sync — run 'python build/build.py' and commit."
  echo "$DRIFT"
  exit 1
fi

echo ""
echo "ALL CHECKS PASSED"
