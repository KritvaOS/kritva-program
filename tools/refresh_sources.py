#!/usr/bin/env python3
"""Refresh the committed copies in sources/ from each engineering repo's default branch.

Read-only toward the engineering repos. Never touches the baseline, approvals, gate ledgers or the
generated report. It reuses consolidate_status.fetch_sources, so the same fail-closed rules apply:
the ref is resolved to a commit, the file is read at that commit, repo/workstream identity must match
sources.json, and the report's own source.commit must be an ancestor of (or equal to) the fetched commit.

It writes sources/<WORKSTREAM>.json (only when content changed) and sources/MANIFEST.json, which records
for each source the fetched head, the commit the report says it inspected, how far the head is ahead of
that commit, and whether the files in between are only under the status path. A report can only name its
parent commit, so a gap that touches nothing but status/ is expected and is labelled STATUS_ONLY.

Freshness: FRESH <= warn_hours, WARN <= stale_hours, STALE beyond. FETCH_FAILED keeps the old snapshot on
disk (for reproducibility) and is recorded as such; it is never presented as fresh.

Exit codes: 0 ok, 2 a source failed to fetch or validate, 3 nothing changed (with --fail-if-unchanged).
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import consolidate_status as cs  # noqa: E402

MANIFEST = "MANIFEST.json"
WARN_HOURS, STALE_HOURS = 24, 72


TOOLING = {"gen_status.py", "test_gen_status.py"}  # the repo's own status generator and its test


def gap_kind(files, status_path):
    prefix = status_path.rsplit("/", 1)[0] + "/"
    if all(f.startswith(prefix) for f in files):
        return "STATUS_ONLY"
    if all(f.startswith(prefix) or (f.startswith("scripts/") and f.rsplit("/", 1)[-1] in TOOLING) for f in files):
        return "STATUS_TOOLING"
    return "OTHER_FILES"


def classify_gap(report_commit, head, repo, status_path, gh=None):
    """How the fetched head relates to the commit the report inspected."""
    gh = gh or cs.gh_json
    if not cs.SHA.match(str(report_commit or "")):
        return {"relation": "UNKNOWN", "ahead_by": None, "status_only": None, "gap_kind": "UNKNOWN", "changed_files": []}
    if report_commit == head:
        return {"relation": "IDENTICAL", "ahead_by": 0, "status_only": True, "gap_kind": "NONE", "changed_files": []}
    cmp = gh(f"repos/{repo}/compare/{report_commit}...{head}")
    if not cmp or cmp.get("status") not in ("ahead", "identical"):
        return {"relation": "UNKNOWN", "ahead_by": None, "status_only": None, "gap_kind": "UNKNOWN", "changed_files": []}
    files = sorted(f.get("filename", "") for f in cmp.get("files", []))
    truncated = len(files) >= 300 or cmp.get("total_commits", 0) > len(cmp.get("commits", []))
    return {"relation": "AHEAD", "ahead_by": cmp.get("ahead_by"),
            "gap_kind": "UNKNOWN" if truncated else gap_kind(files, status_path),
            "status_only": (not truncated) and gap_kind(files, status_path) == "STATUS_ONLY",
            "changed_files": files[:50], "changed_files_truncated": truncated or len(files) > 50}


def freshness(fetched_at, now):
    h = (now - cs.parse_ts(fetched_at)).total_seconds() / 3600
    return "FRESH" if h <= WARN_HOURS else ("WARN" if h <= STALE_HOURS else "STALE")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--now", help="ISO time (tests)")
    ap.add_argument("--fail-if-unchanged", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root)
    cfg = cs.load_json(root / cs.TRACK / "sources.json")
    now = cs.parse_ts(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    sdir = root / "sources"
    sdir.mkdir(exist_ok=True)

    found, problems, meta = cs.fetch_sources(cfg)
    mpath = sdir / MANIFEST
    old = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {"sources": {}}
    entries, changed = {}, []
    for s in cfg["sources"]:
        ws = s["workstream_id"]
        prev = old.get("sources", {}).get(ws, {})
        if ws not in found:
            entries[ws] = {**prev, "repo": s["repo"], "state": "FETCH_FAILED", "last_attempt_at": stamp}
            continue
        _, doc = found[ws]
        head = meta[ws]["resolved_commit"]
        target = sdir / f"{ws}.json"
        text = json.dumps(doc, indent=2) + "\n"
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            target.write_text(text, encoding="utf-8")
            changed.append(ws)
        gap = classify_gap(doc["source"].get("commit"), head, s["repo"], cfg["status_path"])
        entries[ws] = {"repo": s["repo"], "ref": s["ref"], "state": "FETCHED", "fetched_at": stamp,
                       "last_attempt_at": stamp, "fetched_head": head,
                       "report_source_commit": doc["source"].get("commit"),
                       "report_updated_at": doc["updated_at"], "tasks": len(doc["tasks"]), **gap}
    out = {"_note": "Written by tools/refresh_sources.py. Records which revision each committed source copy was fetched "
                    "from. STATUS_ONLY means the commits between the report's inspected commit and the fetched head touch "
                    "only the status path; STATUS_TOOLING also touches the repo's own status generator and its test; "
                    "OTHER_FILES means review the listed files. It is a freshness aid, not acceptance.",
           "warn_hours": WARN_HOURS, "stale_hours": STALE_HOURS, "sources": entries}
    mtext = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if not mpath.exists() or mpath.read_text(encoding="utf-8") != mtext:
        mpath.write_text(mtext, encoding="utf-8")
        changed.append(MANIFEST)
    for p in problems:
        print("PROBLEM:", p, file=sys.stderr)
    for ws, e in entries.items():
        extra = f" ahead_by={e.get('ahead_by')} gap={e.get('gap_kind')}" if e["state"] == "FETCHED" else ""
        print(f"{ws}: {e['state']}{extra}")
    print("changed: " + (", ".join(changed) or "nothing"))
    if problems:
        return 2
    if a.fail_if_unchanged and not changed:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
