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
import plan_register as _pr

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
            f"Validation: {errs} error(s), {warns} warning(s) (see Data health). "
            "Full tables: [STATUS_DETAIL.md](STATUS_DETAIL.md).", "",
            "Views are snapshots of the records, not approvals, schedule commitments or forecasts. "
            "Progress is one weight-based figure; estimated effort and repository readiness are reported separately and are not mixed into it.", ""]


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
    if not ef:
        return []  # public program: no effort estimates are published
    if any("effort" in p for p in check(c)):
        return L + ["NOT_VERIFIED: no approved effort estimate, or its totals do not reconcile.", ""]
    return L + ["```text", f"~{ef['completed']:g} PM done of ~{ef['total']:g} PM  {bar(ef['completed'], ef['total'])}  ~{ef['remaining']:g} PM remaining", "```", "",
                "Owner estimates from delivered scope, not timesheets. Effort is not accepted progress and not a schedule forecast "
                f"(planning horizon stated by the owner: {ef.get('horizon_months', 'n/a')} months, not a demonstrated schedule).", ""]


def readiness_lines(c):
    doc = c.get("readiness_doc")
    L = ["## Repository readiness for the return to private", ""]
    if not doc:
        return []  # public program: no private-return checklist
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
    L += [f"Program start {vp['program_start']} and a horizon ending {vp['horizon_end']} are owner-approved (D-044). " + ("Phase dates are owner-approved planning dates (D-076, PD-001); " if all(m['schedule_status'] == 'APPROVED' for m in vp['milestones'] if m['target_date']) else "Phase dates are PROPOSED targets until decision PD-001 is made; ")
          + "they were not derived from a recorded capacity. P6 LAB & ROBOT is on HOLD and has no date. This plan adds no tasks, weights or credit and does not change accepted progress.", "",
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


def _bar20(done, total):
    return bar(done, total, 20)


def _share(done, total):
    return f"{100 * done / total:.1f}%" if total else "n/a"


_FOUNDATION_REPO = {"CORE": "Core", "COMMUNITY": "Community", "CI_DEV_INFRA": "Program"}


def _foundation_by_repo(c):
    """Completed-before-V2 baseline work per repository: [accepted weight, weight, accepted tasks, tasks]."""
    out = {}
    bm = c.get("by_milestone") or {}
    for r in c.get("milestone_alignment") or []:
        if r.get("class") == "PRE_V2" and r.get("workstream") in _FOUNDATION_REPO:
            a = out.setdefault(_FOUNDATION_REPO[r["workstream"]], [0, 0, 0, 0])
            m = bm.get(r.get("milestone"), {})
            a[0] += r["accepted_weight"] or 0
            a[1] += r["weight"] or 0
            a[2] += m.get("credited", 0)
            a[3] += m.get("tasks", 0)
    return out


def _v2_tasks_by_milestone(c):
    out = {}
    for k, v in (c.get("by_milestone") or {}).items():
        m = re.match(r"^V2-(M\d+)-", k)
        if m:
            a = out.setdefault(m.group(1), [0, 0])
            a[0] += v.get("credited", 0)
            a[1] += v.get("tasks", 0)
    return out


def totals(c):
    """Single program view: completed foundation + V2 baseline + approved plan (not yet baselined). None if the register is missing."""
    s = c.get("plan_register")
    if not s:
        return None
    fnd = _foundation_by_repo(c)
    fa, fw = sum(v[0] for v in fnd.values()), sum(v[1] for v in fnd.values())
    fta, ft = sum(v[2] for v in fnd.values()), sum(v[3] for v in fnd.values())
    ba, bw = s["v2_accepted_weight"], s["v2_baseline_weight"]
    bta = sum(v["accepted_tasks"] for v in s["by_repo"].values())
    bt = sum(v["baseline_tasks"] for v in s["by_repo"].values())
    return {"fa": fa, "fw": fw, "fta": fta, "ft": ft, "ba": ba, "bw": bw, "bta": bta, "bt": bt,
            "pw": s["point"], "plo": s["low"], "phi": s["high"], "pt": s["rows"],
            "acc": fa + ba, "tot": fw + bw + s["point"], "lo": fw + bw + s["low"], "hi": fw + bw + s["high"],
            "tacc": fta + bta, "ttot": ft + bt + s["rows"]}


def headline_lines(c):
    t = totals(c)
    L = ["## Program progress at a glance", ""]
    if not t:
        return L + ["NOT_VERIFIED: the approved plan register is missing or invalid.", ""]
    L += ["```text", f"Program completion: {_share(t['acc'], t['tot'])}  ({t['acc']} / {t['tot']} weight)", _bar20(t["acc"], t["tot"]), "```", "",
          "Accepted weight across completed Foundation work and accepted V2 baseline tasks, divided by total Foundation weight, V2 baseline weight and owner-approved V2 planning weight. "
          "Planning-only tasks are in the denominator but earn no credit until they are baselined and accepted. "
          f"Plan estimate range {_share(t['acc'], t['hi'])} to {_share(t['acc'], t['lo'])} (total weight {t['lo']} to {t['hi']}). "
          f"Tasks accepted: {t['tacc']} of {t['ttot']}.", "",
          "| Component | Accepted / total weight | Tasks accepted / total | What it is |", "|---|---|---|---|",
          f"| Completed Foundation (PRE_V2) | {_fmt(t['fa'])} / {_fmt(t['fw'])} | {t['fta']} / {t['ft']} | Core R1.0, Community I2-I4 and the program CI task, completed before the V2 plan |",
          f"| V2 baselined | {t['ba']} / {t['bw']} | {t['bta']} / {t['bt']} | Approved baseline tasks (Sense, Motion) |",
          f"| V2 approved planning scope (not baselined) | 0 / {t['pw']} | 0 / {t['pt']} | Owner-approved scope not yet in the baseline; not necessarily ready to execute; no credit until baselined and accepted |",
          f"| **Total** | **{t['acc']} / {t['tot']}** | **{t['tacc']} / {t['ttot']}** | **{_share(t['acc'], t['tot'])}** |", "",
          "Moving approved-plan tasks into the baseline later changes which row they sit in, not the total or the percentage. "
          "Credit comes only from baselined tasks with an approval, a completed task and CI evidence. Plan weights are estimates. "
          "Physical validation (V2-M6) is on HOLD and excluded; mechanical, actuator, enterprise and raas work are outside this view.", ""]
    return L


def milestone_table_lines(c):
    s = c.get("plan_register")
    t = totals(c)
    L = ["## Milestones", ""]
    if not s or not t:
        return L + ["NOT_VERIFIED: the approved plan register is missing or invalid.", ""]
    meta = {m["id"].replace("V2-", ""): m for m in (c.get("v2_plan") or {}).get("milestones", [])}
    titles = s.get("titles") or {}
    vt = _v2_tasks_by_milestone(c)
    L += ["Accepted weight over total weight (completed foundation, V2 baseline and approved plan).", "",
          "| Milestone | Title | Target | Depends on | Sequence | Progress | Accepted / total weight | Share | Tasks accepted / total |", "|---|---|---|---|---|---|---|---|---|",
          f"| Foundation (PRE_V2) | Completed before V2 | done | none | n/a | `{_bar20(t['fa'], t['fw'])}` | {_fmt(t['fa'])} / {_fmt(t['fw'])} | {_share(t['fa'], t['fw'])} | {t['fta']} / {t['ft']} |"]
    seq = {r["milestone"]: r for r in c.get("sequence") or []}
    today = (c.get("generated_at") or "")[:10]
    changed = False
    for i in range(9):
        k = f"M{i}"
        m = meta.get(k, {})
        rec = (m.get("phase") or "").split(" ", 1)[-1] if m.get("phase") else ""
        title = titles.get(k) or rec
        if k == "M6":
            L.append(f"| M6 | {rec or 'LAB & ROBOT'} | HOLD | M5 | n/a | HOLD (excluded) | n/a | n/a | n/a |")
            continue
        date = m.get("target_date") or "none"
        if titles.get(k) and rec and titles[k] != rec:
            date += " *"
            changed = True
        v = s["by_milestone"].get(k, {"baseline": 0, "accepted": 0, "point": 0, "rows": 0})
        tot = v["baseline"] + v["point"]
        bt = vt.get(k, [0, 0])
        sq = seq.get(k)
        if m.get("target_date") and today and m["target_date"] < today and not m.get("closed"):
            date += " OVERDUE"
        dep = ", ".join(sq["depends_on"]) if sq and sq["depends_on"] else "none"
        if not sq:
            sqt = "n/a"
        elif sq["status"] == "OK":
            sqt = "OK"
        elif sq["status"] == "WAIVED":
            sqt = f"STARTED before {', '.join(sq['open_predecessors'])} closed (waived {', '.join(sq['waiver'])})"
        else:
            sqt = f"VIOLATION: started before {', '.join(sq['open_predecessors'])} closed"
        L.append(f"| {k} | {title} | {date} | {dep} | {sqt} | `{_bar20(v['accepted'], tot)}` | {v['accepted']} / {tot} | {_share(v['accepted'], tot)} | {bt[0]} / {bt[1] + v['rows']} |")
    L.append(f"| **Total** | | | | | `{_bar20(t['acc'], t['tot'])}` | **{t['acc']} / {t['tot']}** | **{_share(t['acc'], t['tot'])}** | **{t['tacc']} / {t['ttot']}** |")
    L += ["", "Target dates are the owner-approved planning dates; they are not commitments or forecasts. "
          "Rule (D-112): a milestone may not start until the milestones it depends on are closed. Closure needs a recorded completion record; none of M0-M8 is closed yet. "
          "STARTED means accepted weight or an in-progress plan task. Existing out-of-sequence work is grandfathered by waivers; a new start without a waiver is a validation error."]
    if changed:
        L.append("\\* The plan title differs from the V2 milestone record (booking and commercial work belongs to kritva-raas, outside this plan); the date is carried over and must be re-confirmed.")
    return L + [""]


def repo_table_lines(c):
    s = c.get("plan_register")
    t = totals(c)
    L = ["## Repositories", ""]
    if not s or not t:
        return L + ["NOT_VERIFIED: the approved plan register is missing or invalid.", ""]
    fnd = _foundation_by_repo(c)
    L += ["Task and weight totals combine completed Foundation (PRE_V2) work, V2 baseline tasks and approved V2 planning tasks. Each repository row adds up to the program totals.", "",
          "| Repository | Accepted tasks / total tasks | Accepted weight / total weight | Completion |", "|---|---|---|---|"]
    for k, v in s["by_repo"].items():
        f = fnd.get(k, [0, 0, 0, 0])
        acc = f[0] + v["accepted"]
        tot = f[1] + v["baseline"] + v["point"]
        ta = f[2] + v.get("accepted_tasks", 0)
        tn = f[3] + v.get("baseline_tasks", 0) + v["rows"]
        L.append(f"| {k} | {ta} / {tn} | {_fmt(acc)} / {_fmt(tot)} | `{_bar20(acc, tot)}` {_share(acc, tot)} |")
    L.append(f"| **Total** | **{t['tacc']} / {t['ttot']}** | **{t['acc']} / {t['tot']}** | `{_bar20(t['acc'], t['tot'])}` **{_share(t['acc'], t['tot'])}** |")
    return L + [""]


def matrix_lines(c):
    s = c.get("plan_register")
    L = ["## Work by repository and milestone", ""]
    if not s or not s.get("matrix"):
        return L + ["NOT_VERIFIED: the approved plan register is missing or invalid.", ""]
    fnd = _foundation_by_repo(c)
    ms = [f"M{i}" for i in range(9) if i != 6]
    L += ["Each cell is accepted / total weight (share). A dot means no work planned for that repository in that milestone.", "",
          "| Repository | Foundation (PRE_V2) | " + " | ".join(ms) + " | All |", "|---|---|" + "---|" * (len(ms) + 1)]
    col = {m: [0, 0] for m in ["Foundation"] + ms}
    cell = lambda a, n: f"{_fmt(a)}/{_fmt(n)} ({100 * a / n:.0f}%)"
    for repo in s["by_repo"]:
        f = fnd.get(repo)
        row, ra, rt = [], 0, 0
        if f and f[1]:
            row.append(cell(f[0], f[1])); ra += f[0]; rt += f[1]
            col["Foundation"][0] += f[0]; col["Foundation"][1] += f[1]
        else:
            row.append("·")
        for m in ms:
            v = s["matrix"].get(repo, {}).get(m)
            if not v or not (v["baseline"] + v["point"]):
                row.append("·")
                continue
            tot = v["baseline"] + v["point"]
            row.append(cell(v["accepted"], tot))
            ra += v["accepted"]; rt += tot
            col[m][0] += v["accepted"]; col[m][1] += tot
        L.append(f"| {repo} | " + " | ".join(row) + f" | {_fmt(ra)}/{_fmt(rt)} ({_share(ra, rt)}) |")
    ta = sum(v[0] for v in col.values()); tt = sum(v[1] for v in col.values())
    L.append("| **All** | " + " | ".join(cell(v[0], v[1]) if v[1] else "·" for v in col.values()) + f" | **{_fmt(ta)}/{_fmt(tt)} ({_share(ta, tt)})** |")
    return L + ["", "Task-level detail for every cell is in [STATUS_DETAIL.md](STATUS_DETAIL.md) (Plan tasks by milestone and repository).", ""]


def plan_tasks_lines(c):
    s = c.get("plan_register")
    if not s or not s.get("tasks"):
        return []
    L = ["", "## Plan tasks by milestone and repository", "",
         "Approved plan rows (no credit). Weights are planning estimates. Status is the execution status recorded in the register.", "",
         "| Milestone | Repository | Task | Title | Weight | Status |", "|---|---|---|---|---|---|"]
    order = {r: i for i, r in enumerate(_pr.REPOS)}
    for t in sorted(s["tasks"], key=lambda t: (int(t["milestone"][1:]), order.get(t["repo"], 99), t["id"])):
        L.append(f"| {t['milestone']} | {t['repo']} | {t['id']} | {t['title'].replace('|', '/')} | {t['weight']} | {t['status']} |")
    return L + [""]


def open_milestone_lines(c):
    """Task list for the earliest milestone that still has open tasks (currently M0): approved plan rows plus
    baseline tasks of that milestone (a plan row leaves the register when baseline v11 adds it as a baseline task)."""
    s = c.get("plan_register")
    L = []
    if not s or not (s.get("tasks") or c.get("tasks")):
        return L
    titles = s.get("titles") or {}
    order = {r: i for i, r in enumerate(_pr.REPOS)}
    for i in range(9):
        k = f"M{i}"
        tasks = [t for t in s.get("tasks", []) if t["milestone"] == k]
        base_rows = [t for t in c.get("tasks", []) if str(t.get("milestone_id") or "").startswith(f"V2-{k}-")]
        v = s["by_milestone"].get(k)
        if not (tasks or base_rows) or not v or v["accepted"] >= v["baseline"] + v["point"]:
            continue
        tot = v["baseline"] + v["point"]
        rows = [(t["repo"], t["id"], t["title"], t["weight"], t["status"]) for t in tasks]
        for t in base_rows:
            repo = str(t["milestone_id"]).split("-")[2].capitalize()
            status = (t.get("execution") or "NOT_REPORTED") + (" (credited)" if t.get("credit") else "")
            rows.append((repo, t["task_id"], t.get("title") or "-", t.get("weight") if t.get("weight") is not None else "N/A", status))
        done = sum(1 for t in base_rows if t.get("credit"))
        L = [f"## Open work: {k} {titles.get(k, '')}".rstrip(), "",
             f"{k} is the earliest milestone with open tasks: {v['accepted']} of {tot} weight accepted, {len(rows)} tasks ({len(base_rows)} baselined, {len(tasks)} approved plan rows), {done} credited. "
             "Each task needs to be baselined, completed and backed by CI evidence before it earns credit.", "",
             "| Repository | Task | Title | Weight | Status |", "|---|---|---|---|---|"]
        for r in sorted(rows, key=lambda r: (order.get(r[0], 99), r[1])):
            L.append(f"| {r[0]} | {r[1]} | {str(r[2]).replace('|', '/')} | {r[3]} | {r[4]} |")
        pdata = c.get("v2_plan_data")
        if pdata:
            mid = f"V2-{k}"
            items = []
            for x in _pl.pending_reviews(pdata) + _pl.pending_decisions(pdata):
                scope = (x.get("scope") or {}).get("phase_ids") or []
                if mid in (x.get("blocks") or []):
                    items.append((x["record_id"], x["title"], "blocks closing " + k, x.get("reviewer") or x.get("owner") or "UNASSIGNED"))
                elif mid in scope:
                    items.append((x["record_id"], x["title"], "in scope, not blocking", x.get("reviewer") or x.get("owner") or "UNASSIGNED"))
            if items:
                L += ["", f"What stands between {k} and closure: the items below, then an approved completion record. "
                      "Closing a milestone does not by itself award weighted credit; credit needs baselined tasks that are completed with approval and CI evidence.", "",
                      "| ID | Item | Effect | Reviewer / owner |", "|---|---|---|---|"]
                L += [f"| {a} | {b} | {c_} | {d} |" for a, b, c_, d in items]
        blocked = [r for r in rows if "BLOCKED" in str(r[4])]
        L += ["", f"Weights add up to {sum(r[3] for r in rows if isinstance(r[3], int))}. "
              + (f"{len(blocked)} task(s) are blocked on a pending owner decision: " + ", ".join(f"{r[1]} ({r[4]})" for r in blocked) + ". " if blocked else "")
              + "Every milestone's tasks are listed in [STATUS_DETAIL.md](STATUS_DETAIL.md).", ""]
        break
    return L


def attention_lines(c, limit=5):
    rows = owner_action_rows(c)
    L = ["## Needs owner attention", ""]
    if not rows:
        return L + ["None recorded.", ""]
    L += ["| # | Item | Why it matters | Owner |", "|---|---|---|---|"]
    for i, (a, b, o, _r) in enumerate(rows[:limit], 1):
        L.append(f"| {i} | {a} | {b.replace('|', '/')} | {o} |")
    more = len(rows) - limit
    return L + ["", (f"{more} more open item(s) are listed in [STATUS_DETAIL.md](STATUS_DETAIL.md)." if more > 0 else "All open items are shown."), ""]


def foundation_lines(c):
    """Notes on the single total: how it relates to the earlier 90.64% figure, and the Community safety caveat."""
    t = totals(c)
    if not t:
        return []
    parts = _progress_parts(c)
    L = ["## Notes on the total", ""]
    if parts:
        L += [f"The previously displayed {c['progress']['accepted_progress_pct']}% ({_fmt(parts[0])}/{_fmt(parts[1])}) used the same accepted weight but a narrower denominator: "
              f"it excluded the {t['pw']} points of approved V2 planning scope not yet baselined. The consolidated measure includes that scope, giving {t['acc']}/{t['tot']} ({_share(t['acc'], t['tot'])}).", "",
              "Consolidated program completion is a reporting aggregate across Foundation and V2 scope. It does not merge their baselines, alter task ownership, "
              "transfer credit between phases, or make planning-only tasks credit-eligible. Promoting planning tasks into a later baseline changes their classification, not the denominator or the accepted credit.", ""]
    fnd = _foundation_by_repo(c)
    if "Community" in fnd:
        L += ["Community I3/I4 software implementation credit is included in Foundation (PRE_V2). The KOS-I3 and KOS-I4 human safety reviews remain open, KOS-I4 formal closure and physical actuator deployment stay blocked by them, and KOS-CI-001 is deferred. "
              "Software acceptance does not establish human-safety approval or physical validation.", ""]
    return L


def health_lines(c):
    L = ["## Data health", ""]
    unv = [w for w in c["warnings"] if UNVERIFIED.match(w)]
    sf = c.get("source_freshness")
    L += ["| Check | Value |", "|---|---|",
          f"| Validation errors | {len(c['errors'])} |",
          f"| Warnings | {len(c['warnings'])} ({len(unv)} workstreams with no status source) |"]
    if sf:
        from collections import Counter
        L.append("| Source freshness | " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(r["freshness"] for r in sf["rows"]).items())) + " |")
    L += ["", "Details: [STATUS_DETAIL.md](STATUS_DETAIL.md).", ""]
    for x in c["errors"]:
        L.append(f"- ERROR: {x}")
    return L + ([""] if c["errors"] else [])


def detail_extra_lines(c, phases):
    """Sections moved out of STATUS_VIEW.md; appended to STATUS_DETAIL.md."""
    return ["", *plan_tasks_lines(c), *owner_actions_lines(c), *changes_lines(c), *_pr.view_lines(c), *progress_lines(c), *effort_lines(c), *readiness_lines(c),
            *plan_lines(c), *milestones_lines(c), *phase_lines(phases), *quality_lines(c)]


def render_view_lines(c, phases, measures_table):
    """Executive view. measures_table is kept for the detail file; it is not shown here."""
    return [*header_lines(c), *headline_lines(c), *milestone_table_lines(c), *repo_table_lines(c), *matrix_lines(c), *open_milestone_lines(c),
            *attention_lines(c), *foundation_lines(c), *health_lines(c)]
