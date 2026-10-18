#!/usr/bin/env bash
# ship.sh - short front end for ship-prs.sh (what `make ship` calls).
#
#   ship.sh --branch NAME (--tar FILE | --patches DIR) [--only "a b"] [--body TEXT] [--tag TAG --milestone ID] [--dry] [--print]
#
#   --tar FILE      a patch tarball (layout <repo>/*.patch); extracted to a new folder under /tmp, never next to your repos
#   --patches DIR   an already extracted folder
#   --only "a b"    ship just these repos (default: every repo folder in the patches)
#   --dry           show what would happen (ship-prs.sh without --go)
#   --print         print the ship-prs.sh command and stop
# Always passes --admin and --manifest v2/planning/repo-pipeline.json, so the repos are shipped in dependency order and the
# required checks are enforced. Run it from the kritva-program checkout.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
TAR=""; PATCHES=""; BRANCH=""; ONLY=""; BODY="Shipped with make ship. See v2/DECISIONS.md in kritva-program."; TAG=""; MILESTONE=""; DRY=0; PRINT=0
while [ $# -gt 0 ]; do
  case "$1" in
    --tar) TAR=$2; shift;; --patches) PATCHES=$2; shift;; --branch) BRANCH=$2; shift;; --only) ONLY=$2; shift;;
    --body) BODY=$2; shift;; --tag) TAG=$2; shift;; --milestone) MILESTONE=$2; shift;; --dry) DRY=1;; --print) PRINT=1;;
    -h|--help) sed -n '2,13p' "$0"; exit 0;;
    *) echo "unknown option: $1" >&2; exit 2;;
  esac; shift
done
[ -n "$BRANCH" ] || { echo "give a branch name (BRANCH=feat/...)" >&2; exit 2; }
if [ -n "$TAR" ] && [ -n "$PATCHES" ]; then echo "give TAR or PATCHES, not both" >&2; exit 2; fi
if [ -n "$TAR" ]; then
  [ -f "$TAR" ] || { echo "tarball not found: $TAR" >&2; exit 2; }
  PATCHES="$(mktemp -d /tmp/ship.XXXXXX)" || exit 2
  tar xzf "$TAR" -C "$PATCHES" || { echo "could not extract $TAR" >&2; exit 2; }
fi
[ -n "$PATCHES" ] && [ -d "$PATCHES" ] || { echo "give TAR=file.tar.gz or PATCHES=folder" >&2; exit 2; }
if [ -z "$ONLY" ]; then
  for d in "$PATCHES"/*/; do ls "$d"*.patch >/dev/null 2>&1 && ONLY="$ONLY $(basename "$d")"; done
  ONLY=${ONLY# }
fi
[ -n "$ONLY" ] || { echo "no <repo>/*.patch found under $PATCHES" >&2; exit 2; }
CMD=(bash "$HERE/ship-prs.sh" --admin --manifest "$ROOT/v2/planning/repo-pipeline.json" --repos "$ONLY" --patches "$PATCHES" --branch "$BRANCH" --body "$BODY")
[ $DRY -eq 1 ] || CMD+=(--go)
[ -z "$TAG" ] || CMD+=(--tag "$TAG" --milestone "$MILESTONE")
if [ $PRINT -eq 1 ]; then printf '%q ' "${CMD[@]}"; echo; exit 0; fi
echo "repos: $ONLY  patches: $PATCHES  branch: $BRANCH$([ $DRY -eq 1 ] && echo '  (dry run)')"
exec "${CMD[@]}"
