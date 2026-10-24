#!/usr/bin/env bash
# ship-prs.sh - apply a patch set to the Kritva repos, open one PR per repo, wait for the
# required checks, merge, delete the branch, and sync local main.
#
# Needs: git, GitHub CLI (gh) logged in as a repo admin (gh auth login), network.
# Safe by default: without --go it only prints what it would do.
#
# Usage:
#   ship-prs.sh [--go] [--admin] [--base DIR] [--patches DIR] [--branch NAME] [--repos "a b c"]
#               [--manifest FILE] [--body TEXT] [--tag TAG --milestone ID]
#
#   --go         actually do it (default is a dry run)
#   --admin      merge with `gh pr merge --admin` (uses your ruleset bypass; needed while you are
#                the only Code Owner and cannot approve your own PR)
#   --base DIR   folder holding the repo clones      (default /home/dinesha/workarea/kritvaos)
#   --patches D  folder with <repo>/*.patch          (default /tmp/gov4/out4)
#   --branch N   branch name                         (default chore/governance-wording)
#   --repos "…"  space-separated repo list           (default: all nine, or the manifest order)
#   --manifest F v2/planning/repo-pipeline.json: take the repo order from it (dependencies first), refuse
#                repos that are not in it, and require its GitHub checks to be present and passing
#   --body TEXT  PR body                              (default: a generic governance line)
#   --tag TAG    after the merge, create and push an annotated SemVer tag (one repo only; needs --manifest and
#                --milestone). The tag must pass `manifest.py tag-ok` and the repo needs a COMPLETION_RECORD.md
#                naming the milestone. A tag is evidence, not milestone closure.
#
# Rules it follows: never force-pushes, never touches main except fast-forward pulls, stops a
# repo (and continues with the next) if a check fails, a patch does not apply, or the working
# tree is dirty. Merge style is a merge commit, matching the existing history.

set -u
GO=0; ADMIN=0
BASE=/home/dinesha/workarea/kritvaos
PATCHES=/tmp/gov4/out4
BRANCH=chore/governance-wording
MANIFEST=""; BODY="Governance wording and AGENTS.md (D-040). See v2/DECISIONS.md in kritva-program."; TAG=""; MILESTONE=""; REPOS_SET=0
ORG=KritvaOS
REPOS="kritva-program kritvaos-community kritva-core kritva-actuator kritva-actuator-embedded kritva-actuator-s kritva-actuator-m kritva-actuator-l"
MAX_WAIT_FOR_CHECKS=120   # seconds to wait for checks to appear after the push

while [ $# -gt 0 ]; do
  case "$1" in
    --go) GO=1;; --admin) ADMIN=1;;
    --base) BASE=$2; shift;; --patches) PATCHES=$2; shift;;
    --branch) BRANCH=$2; shift;; --repos) REPOS=$2; REPOS_SET=1; shift;;
    --manifest) MANIFEST=$2; shift;; --body) BODY=$2; shift;; --tag) TAG=$2; shift;; --milestone) MILESTONE=$2; shift;;
    -h|--help) sed -n '2,32p' "$0"; exit 0;;
    *) echo "unknown option: $1" >&2; exit 2;;
  esac; shift
done

command -v gh  >/dev/null || { echo "gh (GitHub CLI) not found" >&2; exit 2; }
command -v git >/dev/null || { echo "git not found" >&2; exit 2; }
gh auth status >/dev/null 2>&1 || { echo "gh is not logged in: run 'gh auth login'" >&2; exit 2; }

# ---- manifest (optional): order, membership, required checks, tag rules
MSCRIPT=""
if [ -n "$MANIFEST" ]; then
  [ -f "$MANIFEST" ] || { echo "manifest not found: $MANIFEST" >&2; exit 2; }
  MANIFEST="$(cd "$(dirname "$MANIFEST")" && pwd)/$(basename "$MANIFEST")"   # absolute: the script cd's into each repo
  MSCRIPT="$(cd "$(dirname "$MANIFEST")/../.." 2>/dev/null && pwd)/scripts/pipeline/manifest.py"
  [ -f "$MSCRIPT" ] || { echo "manifest.py not found next to the manifest ($MSCRIPT)" >&2; exit 2; }
  command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 2; }
  python3 "$MSCRIPT" validate --manifest "$MANIFEST" || { echo "manifest is invalid" >&2; exit 2; }
  ORDER=$(python3 "$MSCRIPT" order --manifest "$MANIFEST")
  if [ $REPOS_SET -eq 0 ]; then REPOS=$ORDER
  else  # keep the manifest order for the repos asked for, and reject unknown ones
    SEL=""; for r in $REPOS; do echo "$ORDER" | grep -qx "$r" || { echo "repo $r is not in the manifest" >&2; exit 2; }; done
    for o in $ORDER; do for r in $REPOS; do [ "$o" = "$r" ] && SEL="$SEL $o"; done; done; REPOS=${SEL# }
  fi
fi
if [ -n "$TAG" ]; then
  [ -n "$MANIFEST" ] && [ -n "$MILESTONE" ] || { echo "--tag needs --manifest and --milestone" >&2; exit 2; }
  [ "$(echo $REPOS | wc -w)" -eq 1 ] || { echo "--tag works on exactly one repo at a time" >&2; exit 2; }
  python3 "$MSCRIPT" tag-ok "$REPOS" "$TAG" --manifest "$MANIFEST" || { echo "tag $TAG is not an acceptable annotated SemVer tag" >&2; exit 2; }
fi

run() { if [ $GO -eq 1 ]; then "$@"; else echo "   [dry-run] $*"; fi; }
OK=(); FAIL=()

ship() {
  local r=$1 dir="$BASE/$1" slug="$ORG/$1" n
  echo; echo "== $r"
  [ -d "$dir/.git" ] || { echo "   no clone at $dir"; return 1; }
  cd "$dir" || return 1
  [ -z "$(git status --porcelain)" ] || { echo "   working tree not clean"; return 1; }
  git fetch -q origin || return 1

  # 1. branch + patch + push (skipped if the branch is already on the remote)
  if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
    echo "   branch already on origin, skipping apply/push"
  else
    ls "$PATCHES/$r"/*.patch >/dev/null 2>&1 || { echo "   no patch in $PATCHES/$r"; return 1; }
    run git checkout main && run git pull --ff-only || return 1
    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
      echo "   stale local branch $BRANCH found, recreating it from main"
      run git branch -D "$BRANCH" || return 1
    fi
    run git checkout -b "$BRANCH" || return 1
    if ! run git am "$PATCHES/$r"/*.patch; then
      [ $GO -eq 1 ] && git am --abort; echo "   git am failed"; return 1
    fi
    run git push -u origin "$BRANCH" || return 1
  fi

  # 2. PR (reuse an open one)
  n=$(gh pr list -R "$slug" --head "$BRANCH" --state open --json number -q '.[0].number' 2>/dev/null)
  if [ -z "$n" ]; then
    local title; title=$(git log -1 --format=%s "origin/$BRANCH" 2>/dev/null || git log -1 --format=%s)
    if [ $GO -eq 1 ]; then
      if [ "$(git rev-list --count "origin/main..origin/$BRANCH" 2>/dev/null)" = "0" ]; then
        echo "   branch has no commits beyond main: already merged. Deleting the stale remote branch."
        git push origin --delete "$BRANCH"; git checkout main >/dev/null 2>&1; git pull --ff-only; git branch -D "$BRANCH" >/dev/null 2>&1
        return 0
      fi
      n=$(gh pr create -R "$slug" --base main --head "$BRANCH" --title "$title" \
            --body "$BODY" \
          | grep -o '[0-9]*$') || return 1
    else
      echo "   [dry-run] gh pr create -R $slug --base main --head $BRANCH --title \"$title\""; n="<new>"
    fi
  fi
  echo "   PR #$n"
  [ $GO -eq 1 ] || { echo "   [dry-run] wait for checks, merge (--merge$([ $ADMIN -eq 1 ] && echo ' --admin') --delete-branch), sync main"; return 0; }

  # 3. wait for checks to appear, then for them to finish
  local waited=0
  while ! gh pr checks "$n" -R "$slug" >/dev/null 2>&1 && \
        gh pr checks "$n" -R "$slug" 2>&1 | grep -qi "no checks reported"; do
    [ $waited -ge $MAX_WAIT_FOR_CHECKS ] && { echo "   no checks appeared after ${MAX_WAIT_FOR_CHECKS}s"; return 1; }
    sleep 10; waited=$((waited+10))
  done
  gh pr checks "$n" -R "$slug" --watch --interval 15 || { echo "   checks failed or were cancelled: not merging"; gh pr checks "$n" -R "$slug"; return 1; }

  # 3b. every check the manifest requires must be present and successful on this PR
  if [ -n "$MANIFEST" ]; then
    local need reqs rf cf
    reqs=$(python3 "$MSCRIPT" checks "$r" --manifest "$MANIFEST") || { echo "   cannot read the required checks from the manifest: not merging"; return 1; }
    [ -n "$reqs" ] || { echo "   the manifest lists no required checks for $r: not merging"; return 1; }
    rf=$(mktemp); cf=$(mktemp)
    gh pr view "$n" -R "$slug" --json statusCheckRollup > "$rf" 2>/dev/null
    gh pr checks "$n" -R "$slug" --json name,workflow,state > "$cf" 2>/dev/null || gh pr checks "$n" -R "$slug" --json name,state > "$cf" 2>/dev/null
    python3 "$MSCRIPT" verify-checks "$r" --manifest "$MANIFEST" --rollup "$rf" --checks "$cf" || { rm -f "$rf" "$cf"; echo "   a required check is missing or not SUCCESS: not merging"; return 1; }
    rm -f "$rf" "$cf"
  fi

  # 4. merge + delete remote branch
  local flags="--merge --delete-branch"; [ $ADMIN -eq 1 ] && flags="$flags --admin"
  local try=0 merged=0
  while [ $try -lt 8 ]; do
    if gh pr merge "$n" -R "$slug" $flags; then merged=1; break; fi
    try=$((try+1)); echo "   merge refused (required checks may still be queued, or review required: try --admin); retry $try/8 in 30s"; sleep 30
  done
  [ $merged -eq 1 ] || return 1
  [ "$(gh pr view "$n" -R "$slug" --json state -q .state)" = "MERGED" ] || { echo "   PR not in MERGED state"; return 1; }

  # 5. sync local main, drop local branch
  git checkout main >/dev/null 2>&1 && git pull --ff-only && git branch -D "$BRANCH" >/dev/null 2>&1
  echo "   merged and synced: $(git rev-parse --short HEAD)"

  # 6. annotated tag (only with --tag; needs the completion record)
  if [ -n "$TAG" ]; then
    python3 "$MSCRIPT" closed "$r" "$MILESTONE" --repo-dir "$dir" --manifest "$MANIFEST" || { echo "   no COMPLETION_RECORD.md naming $MILESTONE in $r: not tagging"; return 1; }
    git tag -a "$TAG" -m "$TAG ($MILESTONE): see COMPLETION_RECORD.md; commit $(git rev-parse HEAD)" && git push origin "$TAG" || return 1
    echo "   tagged $TAG at $(git rev-parse --short HEAD)"
  fi
}

for r in $REPOS; do
  if ( ship "$r" ); then OK+=("$r"); else FAIL+=("$r"); fi
done

echo; echo "---- summary ----"
echo "ok:     ${OK[*]:-none}"
echo "failed: ${FAIL[*]:-none}"
[ ${#FAIL[@]} -eq 0 ]
