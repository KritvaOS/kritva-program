#!/usr/bin/env python3
"""Record the OWNER's gate closure (or re-opening) in v2/tracking/gate_closures.json (D-016, D-019).

  Dry run (default):
    python3 tools/record_gate_closure.py --gates GATE-KOS-I3-SAFETY --evidence-commit <40hex>
  Record:
    python3 tools/record_gate_closure.py --gates GATE-KOS-I3-SAFETY --closer Dinesh --evidence-commit <40hex> \\
        --reviewer-name Dinesh --reviewer-role "owner" --findings "..." --limitations "..." --reason "..." --approve
  Re-open a closed gate: add --reopen (the last record for a gate wins).

A safety gate is closed by a HUMAN safety review. This tool only records that the owner says it happened:
  * the record names the reviewer, role, commit reviewed, findings, limitations and rationale (all required;
    write 'none' or 'not provided' explicitly rather than leaving them out);
  * scope_reviewed is copied from the gate, so the record covers exactly what the gate covers;
  * records are appended, never edited; the frozen baseline is not touched, so approvals stay valid;
  * a CLOSED gate stops blocking task credit; tasks still need their own approvals.
Stdlib only. Never commits or pushes. Exit 0 ok | 1 refused | 2 usage/IO.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import consolidate_status as cs  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--gates", nargs="+", required=True)
    ap.add_argument("--evidence-commit", help="40-hex Community/Core commit that was reviewed")
    ap.add_argument("--closer")
    ap.add_argument("--reviewer-name")
    ap.add_argument("--reviewer-role")
    ap.add_argument("--independent", choices=["yes", "no", "not-stated"], default="not-stated",
                    help="is the reviewer independent of the implementation?")
    ap.add_argument("--findings")
    ap.add_argument("--limitations")
    ap.add_argument("--reason")
    ap.add_argument("--evidence-ref", action="append", default=[])
    ap.add_argument("--reopen", action="store_true")
    ap.add_argument("--approve", action="store_true")
    ap.add_argument("--at")
    a = ap.parse_args()
    root = Path(a.root)
    t = root / cs.TRACK
    try:
        base = json.loads((t / "baseline.json").read_text(encoding="utf-8"))
        approvals = json.loads((t / "approvals.json").read_text(encoding="utf-8"))
        path = t / cs.GATE_CLOSURES_FILE
        ledger = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"closures": []}
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    gates = {g["gate_id"]: g for g in base.get("gates", [])}
    problems = [f"unknown gate {g}" for g in a.gates if g not in gates]
    _, eff = cs.validate_closures(ledger, base.get("gates", []), set(approvals.get("authorized_approvers", [])))
    for g in a.gates:
        if g in gates and not a.reopen and g in eff:
            problems.append(f"{g} is already CLOSED ({eff[g]['closure_id']})")
        if g in gates and a.reopen and g not in eff:
            problems.append(f"{g} is not closed; nothing to re-open")
        if g in gates:
            sc = gates[g]["scope"]
            print(f"{g}: scope {', '.join(sc.get('milestone_ids', []) + sc.get('task_ids', []))}; "
                  f"closure criteria: {gates[g]['closure_criteria']}")
    if not a.reopen and not re.fullmatch(r"[0-9a-f]{40}", a.evidence_commit or ""):
        problems.append("--evidence-commit must be the full 40-hex commit that was reviewed")
    for p in problems:
        print(f"REFUSED: {p}", file=sys.stderr)
    if problems:
        return 1
    if not a.approve:
        print(f"dry run only; would {'re-open' if a.reopen else 'close'} {len(a.gates)} gate(s); nothing written")
        return 0
    miss = [n for n, v in (("--closer", a.closer), ("--reviewer-name", a.reviewer_name),
                           ("--reviewer-role", a.reviewer_role), ("--findings", a.findings),
                           ("--limitations", a.limitations), ("--reason", a.reason)) if not (v or "").strip()]
    if miss:
        print(f"REFUSED: required with --approve: {', '.join(miss)}", file=sys.stderr)
        return 1
    if a.closer not in approvals.get("authorized_approvers", []):
        print(f"REFUSED: closer {a.closer!r} is not an authorized approver", file=sys.stderr)
        return 1
    at = a.at or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    n = 1 + max([int(c["closure_id"][1:]) for c in ledger["closures"]
                 if str(c.get("closure_id", "")).startswith("C") and c["closure_id"][1:].isdigit()] or [0])
    for g in a.gates:
        rec = {"closure_id": f"C{n:03d}", "gate_id": g, "disposition": "REOPENED" if a.reopen else "CLOSED",
               "evidence_commit": a.evidence_commit if not a.reopen else None, "closed_at": at,
               "closed_by": a.closer,
               "reviewer": {"name": a.reviewer_name, "role": a.reviewer_role, "independent_of_implementation": a.independent},
               "scope_reviewed": gates[g]["scope"], "findings": a.findings, "limitations": a.limitations,
               "rationale": a.reason, "criteria_ref": gates[g]["closure_criteria"]}
        if a.evidence_ref:
            rec["evidence_refs"] = a.evidence_ref
        ledger["closures"].append(rec)
        n += 1
    ledger.setdefault("_note", "Append-only gate-closure ledger. Never edit or delete records; the last record per gate wins. "
                               "CLOSED records the owner's human safety review (D-016, D-019).")
    errs, _ = cs.validate_closures(ledger, base.get("gates", []), set(approvals.get("authorized_approvers", [])))
    if errs:
        for e in errs:
            print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(f"recorded {len(a.gates)} {'re-opening' if a.reopen else 'closure'} record(s); run tools/consolidate_status.py next")
    return 0


if __name__ == "__main__":
    sys.exit(main())
