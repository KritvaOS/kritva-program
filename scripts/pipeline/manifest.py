#!/usr/bin/env python3
"""Read the PR pipeline manifest (v2/planning/repo-pipeline.json) for ship-prs.sh.

  manifest.py validate [--manifest FILE]        validate the whole planning layer; exit 1 on errors
  manifest.py order    [--manifest FILE]        print repo ids in dependency order, one per line
  manifest.py info REPO [--manifest FILE]       print one repository entry as JSON
  manifest.py checks REPO [--manifest FILE]     print the required GitHub check names, one per line
  manifest.py tag-ok REPO TAG [--manifest FILE] exit 0 only if TAG is an acceptable annotated SemVer tag for REPO
  manifest.py closed REPO MILESTONE --repo-dir D  exit 0 only if D has a COMPLETION_RECORD.md naming MILESTONE

Rules enforced: unknown repositories, duplicate ids, missing dependencies, dependency cycles, unknown checks and unknown
approval roles are rejected. Role holders are read from the manifest; nothing is guessed. Stdlib only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import planning  # noqa: E402

SEMVER = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$")
PRERELEASE_MILESTONE = re.compile(r"^-milestone\.v2-m[0-8]$")


def load_all(manifest_path):
    base = Path(manifest_path).resolve().parent if manifest_path else ROOT / planning.PLAN
    return {k: json.loads((base / f).read_text(encoding="utf-8")) for k, f in
            (("milestones", "milestones.json"), ("pipeline", "repo-pipeline.json"),
             ("decisions", "decisions.json"), ("reviews", "reviews.json"))}


def find(data, repo):
    for r in data["pipeline"]["repositories"]:
        if repo in (r["repo_id"], r["github_repo"]):
            return r
    return None


def tag_ok(tag):
    """Release tag: vMAJOR.MINOR.PATCH, or a milestone prerelease vX.Y.Z-milestone.v2-mN. Other prereleases are rejected."""
    m = SEMVER.match(tag)
    if not m:
        return False
    pre = m.group(4)
    return pre is None or bool(PRERELEASE_MILESTONE.match(pre))


def closed(repo_dir, milestone):
    p = Path(repo_dir) / "COMPLETION_RECORD.md"
    if not p.is_file():
        return False
    t = p.read_text(encoding="utf-8")
    return bool(re.search(rf"^\s*Milestone(?: ID)?\s*:\s*{re.escape(milestone)}\s*$", t, re.M | re.I))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["validate", "order", "info", "checks", "tag-ok", "closed"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--manifest")
    ap.add_argument("--repo-dir")
    a = ap.parse_args(argv)
    data = load_all(a.manifest)
    if a.cmd == "validate":
        errs = planning.validate(data)
        for e in errs:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1 if errs else 0
    errs = planning.validate(data)
    if errs:
        for e in errs:
            print(f"ERROR: {e}", file=sys.stderr)
        print("manifest is invalid; refusing to continue", file=sys.stderr)
        return 1
    if a.cmd == "order":
        order, _ = planning.topo(data["pipeline"]["repositories"])
        print("\n".join(order))
        return 0
    if not a.args:
        ap.error("repository argument required")
    r = find(data, a.args[0])
    if r is None:
        print(f"unknown repository {a.args[0]!r}: not in the manifest", file=sys.stderr)
        return 2
    if a.cmd == "info":
        print(json.dumps(r, indent=2, sort_keys=True))
    elif a.cmd == "checks":
        print("\n".join(r["required_github_checks"]))
    elif a.cmd == "tag-ok":
        if len(a.args) < 2:
            ap.error("tag argument required")
        return 0 if tag_ok(a.args[1]) else 1
    elif a.cmd == "closed":
        if len(a.args) < 2 or not a.repo_dir:
            ap.error("milestone argument and --repo-dir required")
        return 0 if closed(a.repo_dir, a.args[1]) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
