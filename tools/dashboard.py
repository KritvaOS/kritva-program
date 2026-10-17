#!/usr/bin/env python3
"""At-a-glance charts for v2/tracking/STATUS_VIEW.md (display only).

Everything here is derived from the already-validated consolidated data. It never feeds credit, the
baseline, approvals or readiness. Rules (aligned with the external review, 2026-10-17):

* The three measures (accepted progress, owner-estimated effort, capability) are never combined.
* Only dates recorded in the program files are drawn. Phase dates are not approved, so P0-P8 is an
  ordered sequence with no dates, durations or percentages.
* Every progress figure shows its numerator and denominator; every effort figure shows PM units and
  the estimate caveat.
* If totals do not reconcile, the chart is replaced by a NOT_VERIFIED line instead of being drawn.
* Charts are snapshots, not approvals, schedule commitments or forecasts.
"""
import re
from pathlib import Path

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


def render_lines(c, phases):
    L = ["", "## At a glance", "",
         f"Snapshot of committed data, generated {c['generated_at']}. These charts are views of the records below: "
         "they are not approvals, schedule commitments or forecasts, and the three measures are never combined into one health figure.", ""]
    probs = check(c)
    # 1. accepted progress by workstream
    L += ["### Accepted engineering progress (frozen baseline, approval- and CI-evidence-credited)", ""]
    parts = _progress_parts(c)
    bw = c.get("by_workstream") or {}
    if probs or not parts or not bw:
        L += [f"NOT_VERIFIED: {'; '.join(probs) or 'no baseline data'}. The chart is not drawn.", ""]
    else:
        pct = c["progress"]["accepted_progress_pct"]
        L += ["```text", f"{_fmt(parts[0])}/{_fmt(parts[1])} weight  {bar(parts[0], parts[1])}  {pct}%", "```", "",
              "| Workstream | Accepted weight | Baseline weight | Accepted share | Tasks credited / baselined |", "|---|---|---|---|---|"]
        order = sorted(bw, key=lambda k: (-bw[k]["weight"], k))
        for k in order:
            v = bw[k]
            L.append(f"| {k} | {_fmt(v['accepted_weight'])} | {_fmt(v['weight'])} | "
                     f"{_fmt(v['accepted_weight'])}/{_fmt(v['weight'])} = {100 * v['accepted_weight'] / v['weight']:.1f}% | "
                     f"{v['credited']}/{v['tasks']} |")
        L += ["", "```mermaid", "xychart-beta",
              "    title \"Accepted weight as % of each workstream's baseline weight\"",
              "    x-axis [" + ", ".join(order) + "]",
              "    y-axis \"Accepted / baseline weight (%)\" 0 --> 100",
              "    bar [" + ", ".join(f"{100 * bw[k]['accepted_weight'] / bw[k]['weight']:.1f}" for k in order) + "]",
              "```", "",
              "Only the baselined workstreams are shown. Workstreams that are NOT BASELINED have no accepted progress to report; that is not zero progress.", ""]
    # 2. effort
    ef = (c.get("effort") or {}).get("program_planning")
    L += ["### Estimated effort (owner estimate, person-months)", ""]
    if not ef or any("effort" in p for p in probs):
        L += ["NOT_VERIFIED: no approved effort estimate, or its totals do not reconcile.", ""]
    else:
        L += ["```text", f"~{ef['completed']} PM done of ~{ef['total']} PM  {bar(ef['completed'], ef['total'])}  ~{ef['remaining']} PM remaining", "```", "",
              "Owner estimates from delivered scope, not timesheets. Effort is not accepted progress and not a schedule forecast "
              f"(planning horizon stated by the owner: {ef.get('horizon_months', 'n/a')} months, not a demonstrated schedule).", ""]
    # 3. readiness
    rd = c.get("readiness")
    L += ["### Repository readiness for the return to private (display only)", ""]
    if not rd:
        L += ["NOT_VERIFIED: no readiness record.", ""]
    else:
        ready = [r for r in rd["repos"] if r["readiness"] == "READY"]
        L += [f"{len(ready)} of {len(rd['repos'])} repositories READY. Readiness is an operational checklist; it adds no task credit and does not change the baseline or the progress figure above.", "",
              "| Repository | Readiness | Open checks | Attested, not verified |", "|---|---|---|---|"]
        for r in rd["repos"]:
            L.append(f"| {r['repo']} | {r['readiness']} | {', '.join(r['blocking']) or '-'} | {', '.join(r['attested']) or '-'} |")
        L += ["", "Owners and due dates for open checks are not recorded in the readiness file, so none are shown here.", ""]
    # 4. dated milestones
    L += ["### Dated governance milestones (approved dates only)", ""]
    if not rd:
        L += ["NOT_VERIFIED: dates come from the readiness record, which is missing.", ""]
    else:
        snap = c["generated_at"][:10]
        L += ["```mermaid", "gantt",
              "    title Approved dates only (D-037); milestones carry no duration or work estimate",
              "    dateFormat YYYY-MM-DD", "    axisFormat %d %b", "    todayMarker off",
              "    section This report", f"    Status snapshot :milestone, m0, {snap}, 0d",
              "    section Return to private", f"    Readiness report due :milestone, m1, {rd['report_due']}, 0d",
              f"    Repositories return to private :milestone, m2, {rd['target_date']}, 0d",
              "```", "",
              "These are deadlines, not the start or length of any work. Open readiness checks are listed in the table above without invented dates.", ""]
    # 5. phase sequence
    L += ["### Phase sequence (dates not approved)", ""]
    if not phases:
        L += ["NOT_VERIFIED: the frozen phase names could not be read from v2/PROGRAM_PLAN.md.", ""]
    else:
        nodes = " --> ".join(f"{p}[\"{p} {n.replace('&', '#amp;')}\"]" for p, n in phases)
        L += ["```mermaid", "flowchart LR", f"    {nodes}", "```", "",
              "Order only. Phase start and end dates, durations and percent complete are TBD in [v2/ROADMAP.md](../ROADMAP.md); none are inferred here.", ""]
    return L
