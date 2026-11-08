#!/usr/bin/env bash
# Owner-run installer for the program CI workflows (KRP-M0-004). .github/ is protected from remote tools, so you run this.
#   bash tools/ci-templates/install_ci.sh          # copy the three workflows and write .github/kritva-gate.json
#   bash tools/ci-templates/install_ci.sh --check  # only report whether the installed files match the templates
# It never commits or pushes. After it runs: git switch -c ci/add-m0-checks, commit with a Tasks: KRP-M0-004 footer, open a PR.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
T=tools/ci-templates
FILES="unit-tests pr-acceptance-gate tag-policy-check"
gate() { python3 scripts/pipeline/pr_gate.py export --manifest v2/planning/repo-pipeline.json --repo kritva-program; }
if [ "${1:-}" = "--check" ]; then
  rc=0
  for f in $FILES; do cmp -s "$T/$f.yml" ".github/workflows/$f.yml" || { echo "differs or missing: .github/workflows/$f.yml"; rc=1; }; done
  gate | cmp -s - .github/kritva-gate.json || { echo "differs or missing: .github/kritva-gate.json"; rc=1; }
  [ $rc -eq 0 ] && echo "installed CI files match the templates"
  exit $rc
fi
mkdir -p .github/workflows
for f in $FILES; do cp "$T/$f.yml" ".github/workflows/$f.yml"; echo "installed .github/workflows/$f.yml"; done
gate > .github/kritva-gate.json
echo "wrote .github/kritva-gate.json"
echo
echo "Next: run 'python3 -m unittest discover -s tests', then commit and open a PR."
echo "After the PR merges, add these as required status checks in the main ruleset: pr-acceptance-gate, unit-tests, tag-policy-check."
