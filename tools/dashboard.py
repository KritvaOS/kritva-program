#!/usr/bin/env python3
"""Executive sections for v2/tracking/STATUS_VIEW.md (display only; plain Markdown, no Mermaid).

Everything here is derived from the already-validated consolidated data. It never feeds credit, the
baseline, approvals or readiness. Rules (aligned with the external review, 2026-10-17):

* The three measures (accepted progress, owner-estimated effort, capability) are never combined.
* Only dates recorded in the program files are drawn. Phase dates are not approved, so P0-P8 is an
  ordered sequence with no dates, durations or percentages.
* Every progress figure shows its numerator and denominator; every effort figure shows PM units and
  the estimate caveat.
* If totals do not reconcile, the chart is replaced by a NOT_VERIFIED line instead of being drawn.
* Views are snapshots, not approvals, schedule commitments or forecasts.
* Plain Markdown tables and text only: no Mermaid or other rich-display blocks (the owner's viewer did not render them).
* Nothing is invented: owners and dates appear only where a program record holds them; otherwise "not recorded".
"""
import re
from pathlib import Path

import planning as _pl
import readiness as _rd

BAR_WIDTH = 30


def phase_names(root):
    """Frozen phase names, read from v2/PROGRAM_PLAN.md (section 3). Empty if not exactly P0..P8."""
    p = Path(root) / "v2" / "PROGRAM_PLAN.md"
    if not p.is_file():
        return []
    rows = re.findall(r"^\| (P[0-8]) \| ([^|]+?) \|", p.read_text(encoding="utf-8"), flags=re.M)
    return [[a, b.strip()] for a, b in rows] if [a for a, _ in rows] == [f"P{i}" for i in range(9)] else []


def _progress_parts(c):
    m = re.match(r"(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?) weight", c["progress"].get("basis", ""))
    return (float(m.group(1)), float(m.group(2))) if m else None


def check(c):
    """Return a list of reconciliation problems; empty means the charts may be drawn."""
    probs = []
    parts = _progress_parts(c)
    bw = c.get("by_workstream") or {}
    if not parts:
        probs.append("progress basis has no numerator/denominator")
    elif bw:
        got = (sum(v["accepted_weight"] for v in bw.values()), sum(v["weight"] for v in bw.values()))
        if got != parts:
            probs.append(f"workstream weights {got[0]:g}/{got[1]:g} do not reconcile to {parts[0]:g}/{parts[1]:g}")
    ef = (c.get("effort") or {}).get("program_planning")
    if ef and ef["completed"] + ef["remaining"] != ef["total"]:
        probs.append("effort completed + remaining != total")
    return probs


def bar(done, total, width=BAR_WIDTH):
    n = 0 if not total else round(width * done / total)
    return "█" * n + "░" * (width - n)


def _fmt(x):
    return f"{x:g}"


SEVERITY = {"FAIL": 0, "DECISION": 1, "OPEN": 2}
CODE = {"PASS": "PASS", "ATTESTED": "ATT", "OPEN": "OPEN", "FAIL": "FAIL", "DECISION": "DEC", "NA": "NA"}
UNVERIFIED = re.compile(r"^(?P<w>[A-Z0-9_]+): no status source \(UNVERIFIED\)$")


def short_repo(name):
    n = name.split("/")[-1]
    for pre in ("kritva-actuator-", "kritvaos-", "kritva-"):
        if n.startswith(pre) and n != pre:
            return n[len(pre):]
    return n


def _pct(v):
    return f"{100 * v['accepted_weight'] / v['weight']:.1f}%" if v["weight"] else "n/a"


def header_lines(c):
    errs, warns = len(c["errors"]), len(c["warnings"])
    return [f"Snapshot generated {c['generated_at']} from committed data. Baseline v{c['baseline_version']} "
            f"({'APPROVED' if c['baseline_approved'] else 'DRAFT, not approved'}). "
            f"Validation: {errs} error(s), {warns} warning(s) (see Data quality). "
            "Full tables: [STATUS_DETAIL.md](STATUS_DETAIL.md).", "",
            "Views are snapshots of the records, not approvals, schedule commitments or forecasts. "
            "The three measures are never combined into one health figure.", ""]


def owner_action_rows(c):
    """Open items taken from program records only. Returns [(item, why, owner, record)]."""
    rows = []
    rd = c.get("readiness_doc")
    if rd:
        found = []
        for r in rd["repos"]:
            for ch in r["checks"]:
                if ch["status"] in SEVERITY:
                    found.append((SEVERITY[ch["status"]], r["repo"], ch))
        for _, repo, ch in sorted(found, key=lambda x: (x[0], x[1], x[2]["id"])):
            rows.append((f"{short_repo(repo)}: {ch['id']} is {ch['status']}", ch["detail"], "not recorded per check",
                         "v2/tracking/repo_readiness.json"))
    for g in c["gates"]:
        if g["status"] != "CLOSED":
            rows.append((f"{g['gate_id']} is {g['status']}", f"{g['title']}. Blocks {', '.join(g['blocking_effect'])}",
                         g.get("owner") or "not recorded", "v2/GATE_REGISTER.md, v2/tracking/gate_closures.json"))
    pd = c.get("v2_plan_data")
    if pd:
        for x in _pl.pending_decisions(pd):
            if x.get("blocking"):
                rows.append((f"{x['record_id']}: {x['title']}", x["required_action"], x.get("decision_authority") or "not recorded",
                             "v2/planning/PENDING_DECISIONS.md"))
        rv = _pl.pending_reviews(pd)
        if rv:
            rows.append((f"{len(rv)} review(s) pending ({', '.join(x['record_id'] for x in rv)})",
                         "Review obligations on the V2 plan and the new repositories; no reviewer is assigned yet" if all(not x.get("reviewer") for x in rv) else "See the queue",
                         "UNASSIGNED" if all(not x.get("reviewer") for x in rv) else "see queue", "v2/planning/PENDING_REVIEWS.md"))
    waiting = sorted(t["task_id"] for t in c["tasks"] if t.get("evidence_state") == "REPORTED_AWAITING_APPROVAL")
    if waiting:
        rows.append((f"{len(waiting)} task(s) have reported CI evidence awaiting central approval",
                     f"Zero credit until an approval is recorded: {', '.join(waiting)}", "not recorded", "v2/tracking/approvals.json"))
    return rows


def owner_actions_lines(c):
    L = ["## Owner actions and blockers", ""]
    rows = owner_action_rows(c)
    if not rows:
        return L + ["None recorded.", ""]
    L += ["Open items derived from the program records. Owners and due dates appear only where a record holds them. "
          "Blocking items from the V2 decision queue ([PENDING_DECISIONS.md](../planning/PENDING_DECISIONS.md)) are included; the append-only log [v2/DECISIONS.md](../DECISIONS.md) is not parsed.", "",
          "| # | Item | Why it matters | Recorded owner | Record |", "|---|---|---|---|---|"]
    for i, (a, b, o, r) in enumerate(rows, 1):
        L.append(f"| {i} | {a} | {b.replace('|', '/')} | {o} | {r} |")
    return L + [""]


def facts(c):
    rd = c.get("readiness") or {"repos": []}
    ef = (c.get("effort") or {}).get("program_planning") or {}
    return {"progress": c["progress"].get("basis"), "progress_pct": c["progress"].get("accepted_progress_pct"),
            "credited": sorted(t["task_id"] for t in c["tasks"] if t["credit"]),
            "gates": {g["gate_id"]: g["status"] for g in c["gates"]},
            "readiness": {r["repo"]: [r["readiness"], sorted(r["blocking"])] for r in rd["repos"]},
            "effort_completed": ef.get("completed"), "effort_remaining": ef.get("remaining"),
            "errors": len(c["errors"]), "warnings": len(c["warnings"]),
            "pending_decisions": (c.get("v2_plan") or {}).get("pending_decisions"), "pending_reviews": (c.get("v2_plan") or {}).get("pending_reviews")}


def diff_facts(old, new):
    out = []
    if old["progress"] != new["progress"]:
        out.append(f"Accepted progress: {old['progress']} -> {new['progress']}")
    a, b = set(old["credited"]), set(new["credited"])
    if a != b:
        out.append("Credited tasks: " + "; ".join(x for x in (
            f"added {', '.join(sorted(b - a))}" if b - a else "", f"removed {', '.join(sorted(a - b))}" if a - b else "") if x))
    for k in sorted(set(old["gates"]) | set(new["gates"])):
        if old["gates"].get(k) != new["gates"].get(k):
            out.append(f"Gate {k}: {old['gates'].get(k, 'absent')} -> {new['gates'].get(k, 'absent')}")
    for k in sorted(set(old["readiness"]) | set(new["readiness"])):
        o, n = old["readiness"].get(k), new["readiness"].get(k)
        if o != n:
            out.append(f"Readiness {short_repo(k)}: {o[0] if o else 'absent'} -> {n[0] if n else 'absent'}"
                       + (f" (open: {', '.join(n[1]) or 'none'})" if n else ""))
    for key, lab in (("effort_completed", "Effort completed (PM)"), ("effort_remaining", "Effort remaining (PM)")):
        if old[key] != new[key]:
            out.append(f"{lab}: {old[key]} -> {new[key]}")
    for key, lab in (("errors", "Validation errors"), ("warnings", "Warnings"), ("pending_decisions", "Pending decisions"), ("pending_reviews", "Pending reviews")):
        if key not in old and new.get(key) is None:
            continue
        if old.get(key) != new.get(key):
            out.append(f"{lab}: {old.get(key, 'not tracked')} -> {new.get(key)}")
    return out


def changes_record(prev, new_facts, generated_at):
    """prev: the previous consolidated_status.json (or None). Idempotent: unchanged facts carry the earlier record over."""
    pf = (prev or {}).get("status_facts")
    if pf is None:
        return {"since": None, "recorded_at": generated_at, "items": []}
    if pf == new_facts:
        return prev.get("changes") or {"since": None, "recorded_at": generated_at, "items": []}
    return {"since": prev.get("generated_at"), "recorded_at": generated_at, "items": diff_facts(pf, new_facts)}


def changes_lines(c):
    ch = c.get("changes")
    L = ["## What changed", ""]
    if not ch or ch.get("since") is None:
        return L + ["No earlier snapshot facts are recorded; changes are tracked from this snapshot onward.", ""]
    L += [f"Compared with the snapshot generated {ch['since']} (recorded {ch['recorded_at']}). "
          "The record is replaced only when a tracked fact changes.", ""]
    return L + ([f"- {x}" for x in ch["items"]] if ch["items"] else ["No tracked fact changed."]) + [""]


def progress_lines(c):
    L = ["## Accepted engineering progress by workstream", ""]
    probs = check(c)
    parts = _progress_parts(c)
    bw = c.get("by_workstream") or {}
    if probs or not parts or not bw:
        return L + [f"NOT_VERIFIED: {'; '.join(probs) or 'no baseline data'}. The breakdown is not shown.", ""]
    pct = c["progress"]["accepted_progress_pct"]
    L += ["```text", f"{_fmt(parts[0])}/{_fmt(parts[1])} weight  {bar(parts[0], parts[1])}  {pct}%", "```", ""]
    L += ["| Workstream | Accepted / baseline weight | Share | Tasks credited / baselined |", "|---|---|---|---|"]
    for k in sorted(bw, key=lambda k: (-bw[k]["weight"], k)):
        v = bw[k]
        L.append(f"| {k} | {_fmt(v['accepted_weight'])}/{_fmt(v['weight'])} | {_pct(v)} | {v['credited']}/{v['tasks']} |")
    L += ["", "Frozen baseline; credit needs a recorded approval and verified CI evidence. Only baselined workstreams are listed. "
          "A workstream that is NOT BASELINED has no accepted progress to report; that is not zero progress.", ""]
    return L


def effort_lines(c):
    ef = (c.get("effort") or {}).get("program_planning")
    L = ["## Estimated effort (owner estimate, person-months)", ""]
    if not ef or any("effort" in p for p in check(c)):
        return L + ["NOT_VERIFIED: no approved effort estimate, or its totals do not reconcile.", ""]
    return L + ["```text", f"~{ef['completed']:g} PM done of ~{ef['total']:g} PM  {bar(ef['completed'], ef['total'])}  ~{ef['remaining']:g} PM remaining", "```", "",
                "Owner estimates from delivered scope, not timesheets. Effort is not accepted progress and not a schedule forecast "
                f"(planning horizon stated by the owner: {ef.get('horizon_months', 'n/a')} months, not a demonstrated schedule).", ""]


def readiness_lines(c):
    doc = c.get("readiness_doc")
    L = ["## Repository readiness for the return to private", ""]
    if not doc:
        return L + ["NOT_VERIFIED: no readiness record.", ""]
    repos = doc["repos"]
    ready = [r for r in repos if _rd.readiness(r)[0] == "READY"]
    L += [f"{len(ready)} of {len(repos)} repositories READY. Display only: readiness adds no task credit and does not change the baseline or the progress figure. "
          "READY needs every check PASS, ATT (attested by the owner, not verified) or NA.", "",
          "| Check | " + " | ".join(short_repo(r["repo"]) for r in repos) + " |", "|---|" + "---|" * len(repos)]
    for cid in _rd.CHECK_IDS:
        cells = []
        for r in repos:
            ch = next((x for x in r["checks"] if x["id"] == cid), None)
            cells.append(CODE[ch["status"]] if ch else "-")
        L.append(f"| {cid} | " + " | ".join(cells) + " |")
    L.append("| **Readiness** | " + " | ".join("**" + _rd.readiness(r)[0] + "**" for r in repos) + " |")
    L += ["", "Codes: PASS verified from git; ATT owner-attested; OPEN work remains; FAIL verified problem; DEC owner decision needed; NA not applicable. "
          "Per-repo detail is in STATUS_DETAIL.md.", ""]
    return L


def plan_lines(c):
    L = ["## V2 milestone plan (proposed; not the baseline)", ""]
    vp, pdd = c.get("v2_plan"), c.get("v2_plan_data")
    if not vp:
        return L + ["NOT_VERIFIED: v2/planning records are missing or invalid.", ""]
    L += [f"Program start {vp['program_start']} and a horizon ending {vp['horizon_end']} are owner-approved (D-044). Phase dates are PROPOSED targets until decision PD-001 is made; "
          "they were not derived from a recorded capacity. P6 LAB & ROBOT is on HOLD and has no date. This plan adds no tasks, weights or credit and does not change accepted progress.", "",
          "| Milestone | Phase | Target | Schedule status | Closed |", "|---|---|---|---|---|"]
    for m in vp["milestones"]:
        L.append(f"| {m['id']} | {m['phase']} | {m['target_date'] or 'NO DATE (HOLD)'} | {m['schedule_status']} | {'yes' if m['closed'] else 'no'} |")
    L += ["", f"Pending: {vp['pending_decisions']} decisions ({vp['blocking_decisions']} blocking) and {vp['pending_reviews']} reviews. "
          "See [PENDING_DECISIONS.md](../planning/PENDING_DECISIONS.md), [PENDING_REVIEWS.md](../planning/PENDING_REVIEWS.md), "
          "[V2_MILESTONE_PLAN.md](../planning/V2_MILESTONE_PLAN.md) and the PR approval sequence in [V2_REPO_PLAN.md](../planning/V2_REPO_PLAN.md).", ""]
    return L


def milestones_lines(c):
    rd = c.get("readiness")
    L = ["## Dated milestones (approved dates only)", ""]
    if not rd:
        return L + ["NOT_VERIFIED: dates come from the readiness record, which is missing.", ""]
    return L + ["| Date | Milestone | Record |", "|---|---|---|",
                f"| {c['generated_at'][:10]} | This status snapshot | generated |",
                f"| {rd['report_due']} | Readiness report due | D-037, repo_readiness.json |",
                f"| {rd['target_date']} | Repositories return to private | D-037, repo_readiness.json |", "",
                "These are deadlines, not the start or length of any work. Phase dates are not approved.", ""]


def phase_lines(phases):
    L = ["## Phase order (dates not approved)", ""]
    if not phases:
        return L + ["NOT_VERIFIED: the frozen phase names could not be read from v2/PROGRAM_PLAN.md.", ""]
    return L + [" > ".join(f"{p} {n}" for p, n in phases), "",
                "Order only. Start and end dates, durations and percent complete are TBD in [v2/ROADMAP.md](../ROADMAP.md); none are inferred here.", ""]


def quality_lines(c):
    L = ["## Data quality", ""]
    unv, other = [], []
    for w in c["warnings"]:
        m = UNVERIFIED.match(w)
        (unv if m else other).append(m.group("w") if m else w)
    wsn = len(c["workstreams"])
    base = len(c.get("by_workstream") or {})
    L += ["| Measure | Value |", "|---|---|",
          f"| Validation errors | {len(c['errors'])} |",
          f"| Warnings | {len(c['warnings'])} |",
          f"| Workstreams registered / baselined | {wsn} / {base} |",
          f"| Workstreams with no status source (UNVERIFIED) | {len(unv)} |"]
    sf = c.get("source_freshness")
    if sf:
        from collections import Counter
        L.append("| Source freshness | " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(r["freshness"] for r in sf["rows"]).items())) + " |")
    L += [""]
    if c["errors"]:
        L += ["Errors:", ""] + [f"- {x}" for x in c["errors"]] + [""]
    if unv:
        L += [f"No status source, so no evidence and no credit (not zero progress): {', '.join(sorted(unv))}.", ""]
    if other:
        L += ["Other warnings:", ""] + [f"- {x}" for x in other] + [""]
    return L


def render_view_lines(c, phases, measures_table):
    """measures_table: list of lines for the three-measures table, built by the consolidator."""
    return [*header_lines(c), *owner_actions_lines(c), *changes_lines(c),
            "## Three separate measures (never blended)", "", *measures_table, "",
            *progress_lines(c), *effort_lines(c), *readiness_lines(c), *plan_lines(c), *milestones_lines(c), *phase_lines(phases), *quality_lines(c)]
