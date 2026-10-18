#!/usr/bin/env bash
# merge-pr.sh - merge a PR that is already open (pushed from your own clone), with the same safety as ship-prs.sh.
# What `make merge` calls.
#
#   merge-pr.sh --repo kritva-sense --pr 7 [--base DIR] [--no-admin] [--dry]
#
# Steps: wait for the checks, require every check the manifest lists to be SUCCESS, read the PR gate report (stops on REJECT), merge with a merge commit (--admin unless --no-admin) and delete the remote branch, then fast-forward your local
# main in DIR/<repo> and drop the local branch. --dry stops before the merge. It never force-pushes or edits the PR.
# Run it from the kritva-program checkout (it reads v2/planning/repo-pipeline.json).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
MANIFEST="$ROOT/v2/planning/repo-pipeline.json"
BASE=/home/dinesha/workarea/kritvaos; REPO=""; PR=""; ADMIN=1; DRY=0; ORG=KritvaOS
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO=$2; shift;; --pr) PR=$2; shift;; --base) BASE=$2; shift;; --no-admin) ADMIN=0;; --dry) DRY=1;;
    -h|--help) sed -n '2,11p' "$0"; exit 0;;
    *) echo "unknown option: $1" >&2; exit 2;;
  esac; shift
done
[ -n "$REPO" ] && [ -n "$PR" ] || { echo "give REPO=<repo id> and PR=<number>" >&2; exit 2; }
case "$PR" in *[!0-9]*|"") echo "PR must be a number" >&2; exit 2;; esac
command -v gh >/dev/null || { echo "gh (GitHub CLI) not found" >&2; exit 2; }
gh auth status >/dev/null 2>&1 || { echo "gh is not logged in: run 'gh auth login'" >&2; exit 2; }
python3 "$HERE/manifest.py" info "$REPO" --manifest "$MANIFEST" >/dev/null || { echo "repo $REPO is not in the manifest" >&2; exit 2; }
SLUG="$ORG/$REPO"

STATE=$(gh pr view "$PR" -R "$SLUG" --json state,baseRefName,headRefName -q '.state+" "+.baseRefName+" "+.headRefName') || { echo "cannot read PR #$PR in $SLUG" >&2; exit 2; }
set -- $STATE; PSTATE=$1; PBASE=$2; PHEAD=$3
[ "$PSTATE" = OPEN ] || { echo "PR #$PR is $PSTATE, not OPEN" >&2; exit 2; }
[ "$PBASE" = main ] || { echo "PR #$PR targets $PBASE, not main: not merging" >&2; exit 2; }
echo "== $REPO #$PR ($PHEAD -> main)"

# 1. wait for checks, then require the manifest's checks to be SUCCESS
waited=0
while gh pr checks "$PR" -R "$SLUG" 2>&1 | grep -qi "no checks reported"; do
  [ $waited -ge 120 ] && { echo "   no checks appeared after 120s"; exit 1; }
  sleep 10; waited=$((waited+10))
done
gh pr checks "$PR" -R "$SLUG" --watch --interval 15 || { echo "   checks failed or were cancelled: not merging"; exit 1; }
reqs=$(python3 "$HERE/manifest.py" checks "$REPO" --manifest "$MANIFEST") || { echo "   cannot read the required checks: not merging"; exit 1; }
[ -n "$reqs" ] || { echo "   the manifest lists no required checks for $REPO: not merging"; exit 1; }
for c in $reqs; do
  st=$(gh pr checks "$PR" -R "$SLUG" --json workflow,state -q ".[] | select(.workflow==\"$c\") | .state" 2>/dev/null)
  if [ -z "$st" ] || [ -n "$(printf '%s\n' "$st" | grep -vx SUCCESS)" ]; then
    echo "   required check '$c' is '$(printf '%s' "$st" | tr '\n' ' ')' (empty means missing): not merging"; exit 1
  fi
done

# 2. gate report (after the checks have run, so R06 sees them): REJECT stops here
GATE=$(python3 "$HERE/pr_gate.py" remote --manifest "$MANIFEST" --repo "$REPO" --pr "$PR"); RC=$?
echo "$GATE" | sed -n '2,30p'
[ $RC -eq 0 ] || { echo "   the PR acceptance gate says REJECT: not merging"; exit 1; }

# 3. merge
flags="--merge --delete-branch"; [ $ADMIN -eq 1 ] && flags="$flags --admin"
if [ $DRY -eq 1 ]; then echo "   [dry-run] gh pr merge $PR -R $SLUG $flags; then sync $BASE/$REPO"; exit 0; fi
gh pr merge "$PR" -R "$SLUG" $flags || { echo "   merge refused (a review may be required: omit --no-admin, or ask for a review)"; exit 1; }
[ "$(gh pr view "$PR" -R "$SLUG" --json state -q .state)" = "MERGED" ] || { echo "   PR not in MERGED state"; exit 1; }

# 4. sync the local clone
dir="$BASE/$REPO"
if [ -d "$dir/.git" ] && [ -z "$(git -C "$dir" status --porcelain)" ]; then
  git -C "$dir" checkout main >/dev/null 2>&1 && git -C "$dir" pull -q --ff-only && git -C "$dir" branch -D "$PHEAD" >/dev/null 2>&1
  echo "   merged and synced: $(git -C "$dir" rev-parse --short HEAD)"
else
  echo "   merged; local clone $dir missing or not clean, so it was not synced"
fi
