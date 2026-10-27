#!/usr/bin/env bash
# pr-land.sh - merge the pull request of the branch you are on, then return to an updated main.
# What `make pr_land` calls. For a PR in another repository use `make merge REPO=... PR=...`.
#
#   pr-land.sh [--no-admin] [--dry]
#
# Steps: wait for the checks and require every one to pass; merge with a merge commit (--admin unless --no-admin, for
# the ruleset bypass while you are the only code owner) and delete the remote branch; switch to main, fast-forward it and
# delete the local branch. --dry stops after the checks. It never force-pushes. Run it from the branch of the PR.
set -u
ADMIN=1; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --no-admin) ADMIN=0;; --dry) DRY=1;;
    -h|--help) sed -n '2,9p' "$0"; exit 0;;
    *) echo "unknown option: $1" >&2; exit 2;;
  esac; shift
done
die() { echo "pr-land: $*" >&2; exit 1; }
command -v gh >/dev/null || die "gh (GitHub CLI) not found"
gh auth status >/dev/null 2>&1 || die "gh is not logged in: run 'gh auth login'"
BR=$(git rev-parse --abbrev-ref HEAD); case "$BR" in main|master|HEAD) die "you are on $BR; switch to the PR branch first";; esac
[ -z "$(git status --porcelain)" ] || die "working tree is not clean"
gh pr view --json number,state,title --jq '"PR #\(.number) [\(.state)] \(.title)"' || die "no pull request for branch $BR"
gh pr view --json state --jq .state | grep -q OPEN || die "that PR is not open"
gh pr checks --watch || die "checks did not all pass; not merging"
[ "$DRY" = 1 ] && { echo "dry run: checks passed; would merge $BR and sync main."; exit 0; }
gh pr merge --merge --delete-branch $( [ "$ADMIN" = 1 ] && echo --admin ) || die "merge failed"
git checkout main >/dev/null 2>&1 && git pull --ff-only && { git branch -D "$BR" >/dev/null 2>&1 || true; }
echo "landed: $BR; local main is now $(git rev-parse --short HEAD)"
