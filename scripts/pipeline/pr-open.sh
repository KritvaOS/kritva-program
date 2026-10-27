#!/usr/bin/env bash
# pr-open.sh - turn a handoff tarball into a pull request: branch, extract, test, commit, push, open the PR.
# What `make pr_open` calls.
#
#   pr-open.sh --tar FILE --branch NAME --msg "subject" [--task ID] [--body TEXT] [--no-test] [--dry]
#
# Steps: refuse a dirty tree; update main (fast-forward only); refuse a branch name that already exists locally or on
# origin; create the branch; extract the tarball; refuse an empty change; run the tests; commit with a Task footer;
# push; open the PR. It never touches main except a fast-forward pull, never force-pushes and never merges (see pr-land.sh).
# --dry validates the tarball and prints the plan; it changes nothing. Run it from the root of the clone.
set -u
TAR=""; BRANCH=""; MSG=""; TASK="KRP-ENG-001"; BODY=""; TEST=1; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --tar) TAR=$2; shift;; --branch) BRANCH=$2; shift;; --msg) MSG=$2; shift;; --task) TASK=$2; shift;;
    --body) BODY=$2; shift;; --no-test) TEST=0;; --dry) DRY=1;;
    -h|--help) sed -n '2,11p' "$0"; exit 0;;
    *) echo "unknown option: $1" >&2; exit 2;;
  esac; shift
done
die() { echo "pr-open: $*" >&2; exit 1; }
[ -n "$TAR" ] && [ -n "$BRANCH" ] && [ -n "$MSG" ] || { echo "give TAR=<file.tar.gz> BRANCH=<name> MSG=\"<commit subject>\"" >&2; exit 2; }
TAR="${TAR/#\~/$HOME}"
[ -f "$TAR" ] || die "tarball not found: $TAR"
git check-ref-format --branch "$BRANCH" >/dev/null 2>&1 || die "not a valid branch name: $BRANCH"
case "$BRANCH" in main|master) die "pick a feature branch name, not $BRANCH";; esac
# never extract an absolute path or a path that climbs out of the clone
LIST=$(tar tzf "$TAR") || die "cannot read $TAR as a .tar.gz"
printf '%s\n' "$LIST" | grep -Eq '^/|(^|/)\.\.(/|$)' && die "tarball has an absolute or parent-relative path; refusing"
echo "tarball: $TAR ($(printf '%s\n' "$LIST" | grep -vc '/$') files)"; printf '%s\n' "$LIST" | sed 's/^/  /'
if [ "$DRY" = 1 ]; then
  echo "dry run: would update main, create $BRANCH, extract, $( [ "$TEST" = 1 ] && echo test, )commit \"$MSG\" (Task: $TASK), push and open a PR. Nothing changed."
  exit 0
fi
command -v git >/dev/null && command -v gh >/dev/null || die "git and gh are required"
gh auth status >/dev/null 2>&1 || die "gh is not logged in: run 'gh auth login'"
[ -z "$(git status --porcelain)" ] || die "working tree is not clean; commit or stash first"
git checkout main >/dev/null 2>&1 || die "cannot switch to main"
git pull --ff-only || die "main did not fast-forward"
git show-ref --verify --quiet "refs/heads/$BRANCH" && die "branch $BRANCH already exists locally; pick a new name (git branch -D $BRANCH if it is stale)"
git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1 && die "branch $BRANCH already exists on origin; pick a new name"
git checkout -b "$BRANCH" || die "cannot create $BRANCH"
tar xzf "$TAR" || die "extract failed (branch $BRANCH is left in place)"
[ -n "$(git status --porcelain)" ] || { git checkout main >/dev/null 2>&1; git branch -D "$BRANCH" >/dev/null; die "the tarball changed nothing; branch removed"; }
git status --short
if [ "$TEST" = 1 ]; then python3 -m unittest discover -s tests >/tmp/pr-open-tests.log 2>&1 || { tail -15 /tmp/pr-open-tests.log; die "tests failed; nothing committed (branch $BRANCH is left in place)"; }; echo "tests: OK"; fi
git add -A && git commit -q -m "$MSG" -m "Task: $TASK" || die "commit failed"
git push -u origin "$BRANCH" || die "push failed"
gh pr create --fill ${BODY:+--body "$BODY"} || die "PR creation failed (the branch is pushed)"
echo "next: make pr_watch   then   make pr_land"
