#!/usr/bin/env python3
"""Milestone sequencing check (display and validation only; never feeds credit, the baseline, approvals or gates).

Rule: a milestone may not start while a milestone it depends on (v2/planning/milestones.json depends_on) is not closed.
A milestone has STARTED when it has accepted baseline weight or an approved plan task that is IN_PROGRESS, COMPLETE or ACCEPTED.
CLOSED means a closure record exists (v2/planning/milestones.json via the planning summary).

Result per started milestone: OK (every predecessor closed), WAIVED (an owner-approved waiver in
v2/planning/sequence_waivers.json covers every open predecessor) or VIOLATION (reported as a validation error).
Waivers are records of past, owner-approved decisions; they name the milestone, the predecessor and a decision ID.
"""
import json
import re
from pathlib import Path

MILESTONES = "v2/planning/milestones.json"
WAIVERS = "v2/planning/sequence_waivers.json"
STARTED_STATES = {"IN_PROGRESS", "COMPLETE", "COMPLETED", "ACCEPTED"}


def _short(mid):
    return mid.replace("V2-", "")


def load_waivers(root):
    p = Path(root) / WAIVERS
    if not p.exists():
        return {}, []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out, errs = {}, []
        for w in data.get("waivers", []):
            if not all(w.get(k) for k in ("milestone", "predecessor", "decision", "reason")):
                errs.append(f"waiver {w} needs milestone, predecessor, decision and reason")
                continue
            out[(w["milestone"], w["predecessor"])] = w
        return out, errs
    except (ValueError, AttributeError) as e:
        return {}, [f"{WAIVERS} is not valid: {e}"]


def check(root, c):
    """Return (rows, errors). rows: one per milestone with its dependencies; empty when plan data is missing."""
    p = Path(root) / MILESTONES
    vp = c.get("v2_plan")
    if not p.exists() or not vp:
        return [], []
    deps = {m["id"]: m.get("depends_on") or [] for m in json.loads(p.read_text(encoding="utf-8")).get("milestones", [])}
    closed = {m["id"]: bool(m.get("closed")) for m in vp["milestones"]}
    hold = {m["id"] for m in vp["milestones"] if not m.get("target_date")}
    waivers, errors = load_waivers(root)
    accepted = {}
    for k, v in (c.get("by_milestone") or {}).items():
        m = re.match(r"^(V2-M\d+)-", k)
        if m and v.get("weighted"):
            accepted[m.group(1)] = accepted.get(m.group(1), 0) + v["accepted_weight"]
    active = {("V2-" + t["milestone"]) for t in (c.get("plan_register") or {}).get("tasks", [])
              if t["status"].split(" ")[0] in STARTED_STATES}
    rows = []
    for mid in sorted(deps, key=lambda x: int(x.split("M")[-1])):
        if mid in hold:
            continue
        started = accepted.get(mid, 0) > 0 or mid in active
        open_pred = [d for d in deps[mid] if not closed.get(d, False)]
        if not started or not open_pred:
            status = "OK"
            used = []
        else:
            used = [waivers[(mid, d)] for d in open_pred if (mid, d) in waivers]
            status = "WAIVED" if len(used) == len(open_pred) else "VIOLATION"
        rows.append({"milestone": _short(mid), "depends_on": [_short(d) for d in deps[mid]], "started": started,
                     "open_predecessors": [_short(d) for d in open_pred], "status": status,
                     "waiver": sorted({w["decision"] for w in used})})
        if status == "VIOLATION":
            errors.append(f"sequence: {_short(mid)} has started while {', '.join(_short(d) for d in open_pred if (mid, d) not in waivers)} is not closed "
                          f"(close the predecessor or record an owner-approved waiver in {WAIVERS})")
    return rows, errors
