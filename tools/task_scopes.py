#!/usr/bin/env python3
"""Task scope registry (D-164, migration step 2): validate v2/planning/task_scopes.json against the baseline.

The registry says which repository paths belong to each baselined task and which paths are shared by every
task of a repository. The commit-gap currency rule (STATUS_CURRENCY_POLICY.md) uses it to decide which tasks a
change can affect. This tool only checks and (with --init) writes a skeleton. It never changes credit, the
baseline, approvals or any report, and nothing reads the registry for credit yet (steps 4 to 6 are report-only).

A path entry is a repo-relative file path, or a directory prefix ending in "/". No globs, no leading "/", no "..".
A task or repository whose review is UNREVIEWED is treated as unclassifiable by the policy, so its gaps fail closed.

Exit codes: 0 valid, 1 invalid.
"""
import argparse
import json
import sys
from pathlib import Path

REGISTRY = "v2/planning/task_scopes.json"
BASELINE = "v2/tracking/baseline.json"
SOURCES = "v2/tracking/sources.json"
REVIEWS = ("UNREVIEWED", "REVIEWED")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def bad_path(p):
    if not isinstance(p, str) or not p:
        return "must be a non-empty string"
    if p.startswith("/") or p.startswith("./") or "\\" in p:
        return "must be repo-relative with forward slashes"
    if ".." in p.split("/"):
        return "must not contain '..'"
    if any(c in p for c in "*?[]"):
        return "globs are not supported; use a file path or a directory prefix ending in '/'"
    return None


def matches(path, entries):
    """True when a changed file path falls under any entry (exact file or directory prefix)."""
    return any(path == e or (e.endswith("/") and path.startswith(e)) for e in entries)


IMPACT_CLASSES = ("TASK_SCOPE", "TASK_SHARED", "REPORT_INTEGRITY")


def classify_impact(files, truncated, relation, status_path, repo, tasks, tooling=()):
    """Per-task impact of the commits between a report's source.commit and the repository head (D-164).

    files: changed file paths in the gap; relation: IDENTICAL, AHEAD or UNKNOWN (as refresh_sources reports it);
    repo: the registry's repos entry; tasks: {task_id: registry entry} for this workstream.
    Returns {task_id: {"state": CURRENT | AFFECTED | UNKNOWN, "classes": [...], "files": [...]}}.

    - Files under the status directory are the report's own update and are ignored (a report can only name its parent).
    - The repository's own status generator and its test (tooling) are REPORT_INTEGRITY and affect every task.
    - A file in the repository's shared_paths is TASK_SHARED and affects every task.
    - A file inside a task's paths is TASK_SCOPE and affects that task only.
    - A file in no path is outside every scope and affects nothing (the registry is reviewed, so this is deliberate).
    - An unknown or truncated gap, or an UNREVIEWED repository or task that sees a non-status change, is UNKNOWN (fails closed).
    """
    out = {tid: {"state": "CURRENT", "classes": [], "files": []} for tid in tasks}
    if relation not in ("IDENTICAL", "AHEAD") or truncated:
        for e in out.values():
            e["state"] = "UNKNOWN"
        return out
    prefix = status_path.rsplit("/", 1)[0] + "/"
    repo_ok = repo.get("review") == "REVIEWED"

    def hit(tid, cls, f):
        e = out[tid]
        if e["state"] != "UNKNOWN":
            e["state"] = "AFFECTED"
        if cls not in e["classes"]:
            e["classes"].append(cls)
        if len(e["files"]) < 5 and f not in e["files"]:
            e["files"].append(f)

    for f in sorted(files):
        if f.startswith(prefix):
            continue
        if f.startswith("scripts/") and f.rsplit("/", 1)[-1] in tooling:
            for tid in tasks:
                hit(tid, "REPORT_INTEGRITY", f)
            continue
        if not repo_ok:
            for e in out.values():
                e["state"] = "UNKNOWN"
            continue
        if matches(f, repo.get("shared_paths", [])):
            for tid in tasks:
                hit(tid, "TASK_SHARED", f)
            continue
        for tid, t in tasks.items():
            if t.get("review") != "REVIEWED":
                out[tid]["state"] = "UNKNOWN"
            elif matches(f, t.get("paths", [])):
                hit(tid, "TASK_SCOPE", f)
    for e in out.values():
        e["classes"].sort()
    return out


def check_paths(label, paths, problems):
    if not isinstance(paths, list):
        problems.append(f"{label}: paths must be a list")
        return []
    seen = set()
    for p in paths:
        why = bad_path(p)
        if why:
            problems.append(f"{label}: path {p!r} {why}")
        elif p in seen:
            problems.append(f"{label}: duplicate path {p!r}")
        seen.add(p)
    return paths


def validate(reg, baseline, sources):
    problems = []
    if reg.get("schema_version") != "1.0":
        problems.append("schema_version must be '1.0'")
    if reg.get("baseline_version") != baseline.get("baseline_version"):
        problems.append(f"baseline_version {reg.get('baseline_version')!r} does not match the baseline "
                        f"({baseline.get('baseline_version')!r}); update the registry with the baseline")
    workstreams = [s["workstream_id"] for s in sources["sources"]]
    repos, tasks = reg.get("repos", {}), reg.get("tasks", {})
    for ws in workstreams:
        r = repos.get(ws)
        if r is None:
            problems.append(f"repos: no entry for workstream {ws}")
            continue
        if r.get("review") not in REVIEWS:
            problems.append(f"repos.{ws}: review must be one of {REVIEWS}")
        shared = check_paths(f"repos.{ws}.shared_paths", r.get("shared_paths", []), problems)
        if r.get("review") == "REVIEWED" and not shared:
            problems.append(f"repos.{ws}: REVIEWED needs at least one shared path")
    for ws in repos:
        if ws not in workstreams:
            problems.append(f"repos: {ws} is not a workstream in sources.json")
    base = {t["id"]: t for t in baseline["tasks"]}
    for tid, t in base.items():
        e = tasks.get(tid)
        if e is None:
            problems.append(f"tasks: baselined task {tid} has no scope entry")
            continue
        if e.get("workstream_id") != t["workstream_id"]:
            problems.append(f"tasks.{tid}: workstream_id {e.get('workstream_id')!r} != baseline {t['workstream_id']!r}")
        if e.get("review") not in REVIEWS:
            problems.append(f"tasks.{tid}: review must be one of {REVIEWS}")
        paths = check_paths(f"tasks.{tid}.paths", e.get("paths", []), problems)
        if e.get("review") == "REVIEWED" and not paths:
            problems.append(f"tasks.{tid}: REVIEWED needs at least one path")
    for tid in tasks:
        if tid not in base:
            problems.append(f"tasks: {tid} is not a baselined task")
    return problems


def skeleton(baseline, sources):
    return {
        "_note": "Task scope registry (D-164). UNREVIEWED entries are unclassifiable and fail closed. "
                 "Validate with: python3 tools/task_scopes.py --check",
        "schema_version": "1.0",
        "baseline_version": baseline["baseline_version"],
        "repos": {s["workstream_id"]: {"review": "UNREVIEWED", "shared_paths": []} for s in sources["sources"]},
        "tasks": {t["id"]: {"workstream_id": t["workstream_id"], "review": "UNREVIEWED", "paths": []}
                  for t in baseline["tasks"]},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="validate the registry (default)")
    mode.add_argument("--init", action="store_true", help="write a skeleton; refuses to overwrite an existing registry")
    a = ap.parse_args(argv)
    root = Path(a.root)
    baseline, sources = load(root / BASELINE), load(root / SOURCES)
    target = root / REGISTRY
    if a.init:
        if target.exists():
            print(f"refusing to overwrite {REGISTRY}", file=sys.stderr)
            return 1
        target.write_text(json.dumps(skeleton(baseline, sources), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {REGISTRY}")
        return 0
    problems = validate(load(target), baseline, sources)
    for p in problems:
        print("PROBLEM:", p, file=sys.stderr)
    if problems:
        return 1
    reg = load(target)
    n = sum(1 for t in reg["tasks"].values() if t["review"] == "REVIEWED")
    print(f"task_scopes OK: {len(reg['tasks'])} tasks ({n} reviewed), {len(reg['repos'])} repositories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
