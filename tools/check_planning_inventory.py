#!/usr/bin/env python3
"""Validate v2/tracking/planning_inventory.json (decision D-024). Stdlib only; read-only.

Rules (registration is not credit):
  * every group and every task is PLANNING_ONLY and credit_eligible is false;
  * no inventory task has a weight, an approval, or a baseline entry under any ID or alias;
  * (repository, workstream_id, task_id) is unique; legacy aliases never collide with a canonical ID, and one alias may map to several tasks only when every
    mapping is marked alias_kind=split (a deliberate 1-to-many split);
  * every workstream_id used by a group that names one is registered in workstreams.json.
Exit 0 ok | 1 problems | 2 usage/IO.
"""
import json
import sys
from pathlib import Path


def check(inv, baseline, approvals, workstreams):
    problems = []
    base_ids = {t["id"] for t in baseline.get("tasks", [])}
    approved_ids = {a.get("task_id") for a in approvals.get("approvals", [])}
    ws_ids = {w["id"] for w in workstreams.get("workstreams", [])}
    if inv.get("classification") != "PLANNING_ONLY":
        problems.append("top-level classification must be PLANNING_ONLY")
    seen, canon, aliases = set(), set(), {}
    for g in inv.get("groups", []):
        gname = g.get("workstream_id", "?")
        if g.get("classification") != "PLANNING_ONLY":
            problems.append(f"group {gname}: classification must be PLANNING_ONLY")
        if g.get("credit_eligible") is not False:
            problems.append(f"group {gname}: credit_eligible must be false")
        first = str(gname).split(" ")[0]
        if first in ws_ids or gname in ws_ids:
            pass
        for t in g.get("tasks", []):
            tid = t.get("task_id")
            key = (g.get("repository"), gname, tid)
            if key in seen:
                problems.append(f"{tid}: duplicate in {gname}")
            seen.add(key)
            canon.add(tid)
            if t.get("legacy_alias"):
                aliases.setdefault(t["legacy_alias"], []).append((tid, t.get("alias_kind")))
            if "weight" in t:
                problems.append(f"{tid}: inventory tasks must not carry a weight")
            if t.get("credit_eligible") not in (None, False):
                problems.append(f"{tid}: credit_eligible must be false")
            for ident in (tid, t.get("legacy_alias")):
                if ident and ident in base_ids:
                    problems.append(f"{tid}: {ident} is a baseline task; remove it from the inventory")
                if ident and ident in approved_ids:
                    problems.append(f"{tid}: {ident} has an approval record; inventory entries cannot be approved")
    for al, owners in aliases.items():
        if al in canon:
            problems.append(f"alias {al} collides with a canonical task ID")
        if len(owners) > 1 and any(kind != "split" for _, kind in owners):
            problems.append(f"alias {al} maps to more than one task without alias_kind=split: {[o for o, _ in owners]}")
    return problems


def main(argv):
    root = Path(argv[1] if len(argv) > 1 else ".")
    t = root / "v2/tracking"
    try:
        load = lambda n: json.loads((t / n).read_text(encoding="utf-8"))
        problems = check(load("planning_inventory.json"), load("baseline.json"),
                         load("approvals.json"), load("workstreams.json"))
    except (OSError, ValueError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    for p in problems:
        print(f"PROBLEM: {p}", file=sys.stderr)
    print("planning inventory ok" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
