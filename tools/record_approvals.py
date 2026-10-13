#!/usr/bin/env python3
"""Record the OWNER's PASS approvals in v2/tracking/approvals.json from the evidence map (D-011).

  Dry run (default):  python3 tools/record_approvals.py --tasks I4-001 I4-002
  Record:             python3 tools/record_approvals.py --tasks I4-001 I4-002 --approver Dinesh \\
                          --reason "<what you checked>" --approve
  Everything in one workstream's milestone:  --prefix I4-   (matches task IDs that start with it)

Recording a PASS means YOU have judged that the task's acceptance criteria are met on the evidence
commit, not merely that CI was green. Claude only prepares; this tool never runs unless you pass --approve.

What --approve does (and refuses to do):
  * requires an approved, frozen baseline and --approver in approvals.json authorized_approvers;
  * requires every named task to have a row in v2/tracking/evidence_map_proposal.json;
  * refuses a task that already has an effective approval for the same commit (nothing is duplicated);
    a task approved earlier on a different commit is superseded by a new record naming the old one;
  * appends records (never edits or deletes): review_status APPROVED, acceptance PASS, baseline_version from
    baseline.json, source_commit = the evidence commit, evidence_refs = the CI run URL;
  * prints the review flags for each task (MILESTONE = accepted as of a later commit; RERUN = re-run result).
Stdlib only. Never commits or pushes. Exit 0 ok | 1 refused | 2 usage/IO.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import consolidate_status as cs  # noqa: E402


def plan(root, tasks, prefix):
    t = root / "v2/tracking"
    base = json.loads((t / "baseline.json").read_text())
    ledger = json.loads((t / "approvals.json").read_text())
    emap = json.loads((t / "evidence_map_proposal.json").read_text())
    repos = {w["id"]: w["repo"] for w in json.loads((t / "workstreams.json").read_text())["workstreams"]}
    rows = {r["task_id"]: r for r in emap["rows"]}
    wanted = list(tasks or []) + [i for i in rows if prefix and i.startswith(prefix) and i not in (tasks or [])]
    problems, picks = [], []
    if not base.get("baseline_approved"):
        problems.append("baseline is not approved and frozen")
    errors, effective = cs.validate_approvals(ledger, {b["id"] for b in base["tasks"]}, base["baseline_version"])
    problems += [f"existing ledger: {x}" for x in errors]
    if not wanted:
        problems.append("no tasks selected (use --tasks or --prefix)")
    for tid in wanted:
        r = rows.get(tid)
        if r is None:
            problems.append(f"{tid}: no row in the evidence map (unmapped or unknown)"); continue
        commit = r["evidence"]["commit"]
        old = effective.get(tid)
        if old and old["source_commit"] == commit and old["acceptance"] == "PASS":
            problems.append(f"{tid}: already approved PASS on {commit[:7]} ({old['approval_id']})"); continue
        picks.append((r, repos[r["workstream_id"]], old))
    return base, ledger, picks, problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--tasks", nargs="*", default=[])
    ap.add_argument("--prefix")
    ap.add_argument("--approve", action="store_true")
    ap.add_argument("--approver")
    ap.add_argument("--reason", help="what you checked; stored as the rationale on every record")
    ap.add_argument("--at", help="ISO-8601 UTC approval time (default: now)")
    a = ap.parse_args()
    root = Path(a.root)
    try:
        base, ledger, picks, problems = plan(root, a.tasks, a.prefix)
    except (OSError, ValueError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    for r, repo, old in picks:
        ev = r["evidence"]
        print(f"{r['task_id']:<16} PASS on {ev['commit'][:7]} via run {ev['ci_run']} [{r['mode']}]"
              + (f" flags: {', '.join(r['review_flags'])}" if r["review_flags"] else "")
              + (f" (supersedes {old['approval_id']})" if old else ""))
    for p in problems:
        print(f"REFUSED: {p}", file=sys.stderr)
    if problems:
        return 1
    if not a.approve:
        print(f"dry run only; {len(picks)} approval(s) would be recorded; nothing written")
        return 0
    if not a.approver or a.approver not in ledger.get("authorized_approvers", []):
        print(f"REFUSED: approver {a.approver!r} is not an authorized approver", file=sys.stderr)
        return 1
    if not (a.reason or "").strip():
        print("REFUSED: --reason is required (say what you checked)", file=sys.stderr)
        return 1
    at = a.at or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        cs.parse_ts(at)
    except (ValueError, AttributeError):
        print("REFUSED: --at is not ISO-8601", file=sys.stderr)
        return 1
    n = 1 + max([int(x["approval_id"][1:]) for x in ledger["approvals"]
                 if str(x.get("approval_id", "")).startswith("A") and x["approval_id"][1:].isdigit()] or [0])
    for r, repo, old in picks:
        rec = {"approval_id": f"A{n:03d}", "task_id": r["task_id"], "baseline_version": base["baseline_version"],
               "source_repo": repo, "source_commit": r["evidence"]["commit"], "review_status": "APPROVED",
               "acceptance": "PASS", "approver": a.approver, "approved_at": at,
               "evidence_refs": [r["evidence"]["url"]], "rationale": a.reason.strip()}
        if old:
            rec["supersedes"] = old["approval_id"]
        ledger["approvals"].append(rec)
        n += 1
    out = root / "v2/tracking/approvals.json"
    out.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(f"recorded {len(picks)} approval(s) by {a.approver}; run tools/consolidate_status.py next")
    return 0


if __name__ == "__main__":
    sys.exit(main())
