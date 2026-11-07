#!/usr/bin/env python3
"""Carry the owner's existing PASS approvals forward onto a newly frozen baseline version (D-027).

Run by the OWNER right after tools/freeze_baseline.py, with the same --at time:

  Dry run (default):  python3 tools/carry_forward_approvals.py
  Record:             python3 tools/carry_forward_approvals.py --approver Dinesh --at <freeze time> \\
                          --reason "<why>" --approve

An approval is bound to one baseline version, so freezing a new version leaves every effective approval stale.
For each effective approval made under an older version that is PASS and APPROVED, and whose task is still in the
baseline, this tool appends a record for the current version with the same evidence commit and evidence_refs,
naming the old record in `supersedes`. It makes no new judgement and changes no evidence. The ledger is append-only:
old records are never edited. Tasks with no effective approval (for example new baseline tasks) get nothing.
Stdlib only. Never commits or pushes. Exit 0 ok | 1 refused | 2 usage/IO.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import consolidate_status as cs  # noqa: E402


def plan(root):
    t = Path(root) / "v2/tracking"
    base = json.loads((t / "baseline.json").read_text(encoding="utf-8"))
    ledger = json.loads((t / "approvals.json").read_text(encoding="utf-8"))
    problems = []
    if not base.get("baseline_approved"):
        problems.append("baseline is not approved and frozen")
    ids = {b["id"] for b in base["tasks"]}
    errors, effective = cs.validate_approvals(ledger, ids, base["baseline_version"], allow_stale_baseline=True)
    problems += [f"existing ledger: {x}" for x in errors]
    picks = [a for a in effective.values()
             if a["baseline_version"] < base["baseline_version"] and a["acceptance"] == "PASS"
             and a["review_status"] == "APPROVED" and a["task_id"] in ids]
    return base, ledger, picks, problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--approve", action="store_true")
    ap.add_argument("--approver")
    ap.add_argument("--reason")
    ap.add_argument("--at", help="ISO-8601 UTC approval time (use the baseline freeze time)")
    a = ap.parse_args()
    root = Path(a.root)
    try:
        base, ledger, picks, problems = plan(root)
    except (OSError, ValueError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    v = base["baseline_version"]
    for p in picks:
        print(f"{p['task_id']:<18} {p['approval_id']} (v{p['baseline_version']}) -> v{v}, evidence {p['source_commit'][:7]}")
    for p in problems:
        print(f"REFUSED: {p}", file=sys.stderr)
    if problems:
        return 1
    if not a.approve:
        print(f"dry run only; {len(picks)} approval(s) would be carried to baseline v{v}; nothing written")
        return 0
    if not a.approver or a.approver not in ledger.get("authorized_approvers", []):
        print(f"REFUSED: approver {a.approver!r} is not an authorized approver", file=sys.stderr)
        return 1
    if not (a.reason or "").strip():
        print("REFUSED: --reason is required", file=sys.stderr)
        return 1
    at = a.at or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        cs.parse_ts(at)
    except (ValueError, AttributeError):
        print("REFUSED: --at is not ISO-8601", file=sys.stderr)
        return 1
    n = 1 + max([int(x["approval_id"][1:]) for x in ledger["approvals"]
                 if str(x.get("approval_id", "")).startswith("A") and x["approval_id"][1:].isdigit()] or [0])
    for p in picks:
        ledger["approvals"].append({
            "approval_id": f"A{n:03d}", "task_id": p["task_id"], "baseline_version": v, "source_repo": p["source_repo"],
            "source_commit": p["source_commit"], "review_status": "APPROVED", "acceptance": "PASS", "approver": a.approver,
            "approved_at": at, "evidence_refs": list(p["evidence_refs"]), "rationale": a.reason.strip(),
            "supersedes": p["approval_id"]})
        n += 1
    (root / "v2/tracking/approvals.json").write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(f"carried {len(picks)} approval(s) to baseline v{v} by {a.approver}; run tools/consolidate_status.py next")
    return 0


if __name__ == "__main__":
    sys.exit(main())
