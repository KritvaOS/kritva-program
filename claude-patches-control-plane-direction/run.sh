#!/usr/bin/env bash
# Apply the patch on a branch from main, check, push and open the PR. Run from the kritva-program repo root.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BR=docs/control-plane-working-direction
[ "$(basename "$(git rev-parse --show-toplevel)")" = "kritva-program" ] || { echo "Run this inside kritva-program"; exit 1; }
git switch main && git pull --ff-only
grep -q '^| D-148 |' v2/DECISIONS.md && { echo "D-148 is already taken: renumber before applying"; exit 1; } || true
git switch -c "$BR"
git am "$HERE"/0001-control-plane-direction.patch
python3 tools/planning.py --root . --check
make verify
make preflight
git push -u origin "$BR"
gh pr create --base main --head "$BR" --title "docs(decisions): record the Control Plane working direction (D-148, PD-020)" --body-file "$HERE/PR-description.md"
