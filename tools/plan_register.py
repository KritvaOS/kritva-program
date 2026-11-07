#!/usr/bin/env python3
"""Display-only summary of v2/planning/SEVEN_REPO_PLAN_REGISTER.md for STATUS_VIEW.md (D-109).

The register is an owner-approved planning record. Its weights are planning estimates, not baseline
weights: nothing here feeds compute(), credit, the baseline, approvals or gates. The three measures stay
separate in the view: accepted progress (baseline), V2 baseline weight, and the approved plan.

Validation (errors, reported by the consolidator): every counted row has a unique ID, a non-zero point with
low <= point <= high, credit 0 and plan state APPROVED_PLAN; retired parents carry no weight; every child
names a retired parent; the totals stated in the register match the rows.
"""
import re
from pathlib import Path

FILE = "v2/planning/SEVEN_REPO_PLAN_REGISTER.md"
COLS = ["record_type", "id", "repo", "milestone", "title", "parent_id", "weight_point", "low", "high",
        "plan_state", "execution_status", "credit", "counted", "dependencies"]
REPOS = ["Program", "Core", "Community", "Sense", "Mind", "Motion", "Skill"]
V2_MILESTONE = re.compile(r"^V2-(M\d+)-")


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse(text):
    """Return the list of register rows (dicts keyed by COLS)."""
    rows = []
    for line in text.split("\n"):
        if not line.startswith("| PLANNING_TASK |") and not line.startswith("| RETIRED_PARENT |"):
            continue
        cells = _cells(line)
        if len(cells) != len(COLS):
            raise ValueError(f"register row has {len(cells)} columns, expected {len(COLS)}: {cells[:2]}")
        rows.append(dict(zip(COLS, cells)))
    return rows


def _stated_totals(text):
    """The reconciliation table: 'Counted planning register | 59 | 275 | 213 | 338'."""
    m = re.search(r"^\| Counted planning register \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|", text, re.M)
    return tuple(int(x) for x in m.groups()) if m else None


def validate(rows, text):
    errs = []
    planned = [r for r in rows if r["record_type"] == "PLANNING_TASK"]
    retired = [r for r in rows if r["record_type"] == "RETIRED_PARENT"]
    ids = [r["id"] for r in rows]
    for i in sorted({x for x in ids if ids.count(x) > 1}):
        errs.append(f"duplicate id {i}")
    retired_ids = {r["id"] for r in retired}
    for r in planned:
        try:
            pt, lo, hi = int(r["weight_point"]), int(r["low"]), int(r["high"])
        except ValueError:
            errs.append(f"{r['id']}: weight_point, low and high must be integers")
            continue
        if pt <= 0:
            errs.append(f"{r['id']}: weight_point must be non-zero")
        if not lo <= pt <= hi:
            errs.append(f"{r['id']}: low <= weight_point <= high does not hold ({lo}, {pt}, {hi})")
        if r["credit"] != "0":
            errs.append(f"{r['id']}: a planning row must carry credit 0")
        if r["plan_state"] != "APPROVED_PLAN" or r["counted"] != "true":
            errs.append(f"{r['id']}: a counted row must be APPROVED_PLAN and counted")
        if r["parent_id"] and r["parent_id"] not in retired_ids:
            errs.append(f"{r['id']}: parent {r['parent_id']} is not a retired parent")
    for r in retired:
        if r["weight_point"] or r["low"] or r["high"] or r["counted"] != "false" or r["credit"] != "0":
            errs.append(f"{r['id']}: a retired parent carries no weight, is not counted and has credit 0")
    stated = _stated_totals(text)
    got = (len(planned), sum(int(r["weight_point"]) for r in planned if r["weight_point"].isdigit()),
           sum(int(r["low"]) for r in planned if r["low"].isdigit()), sum(int(r["high"]) for r in planned if r["high"].isdigit()))
    if stated is None:
        errs.append("the reconciliation table row 'Counted planning register' is missing")
    elif stated != got:
        errs.append(f"stated totals {stated} do not match the rows {got}")
    return errs


def _base_by_program_milestone(c):
    out = {}
    for k, v in (c.get("by_milestone") or {}).items():
        m = V2_MILESTONE.match(k)
        if m and v.get("weighted"):
            a = out.setdefault(m.group(1), [0, 0])
            a[0] += v["weight"]
            a[1] += v["accepted_weight"]
    return out


def titles(text):
    """Milestone titles declared by the register ('| M4 | DEVELOPER EXPERIENCE & ECOSYSTEM |'). Empty when absent."""
    sec = text.split("| Milestone | Plan title |", 1)
    if len(sec) < 2:
        return {}
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"^\| (M\d) \| ([^|]+?) \|$", sec[1], re.M)}


def _base_cells(c):
    out = {}
    for k, v in (c.get("by_milestone") or {}).items():
        m = re.match(r"^V2-(M\d+)-([A-Z]+)-", k)
        if m and v.get("weighted"):
            a = out.setdefault((m.group(2).capitalize(), m.group(1)), [0, 0])
            a[0] += v["weight"]
            a[1] += v["accepted_weight"]
    return out


def _base_by_repo(c):
    out = {}
    for k, v in (c.get("by_milestone") or {}).items():
        m = re.match(r"^V2-M\d+-([A-Z]+)-", k)
        if m and v.get("weighted"):
            name = m.group(1).capitalize()
            a = out.setdefault(name, [0, 0])
            a[0] += v["weight"]
            a[1] += v["accepted_weight"]
    return out


def summary(rows, c, text=None):
    """Plan summary for consolidated_status.json (no row detail)."""
    planned = [r for r in rows if r["record_type"] == "PLANNING_TASK"]
    base_m = _base_by_program_milestone(c)
    base_r = _base_by_repo(c)
    by_m, by_r = {}, {}
    for r in planned:
        for d, k in ((by_m, r["milestone"]), (by_r, r["repo"])):
            a = d.setdefault(k, [0, 0, 0, 0])
            a[0] += 1
            a[1] += int(r["weight_point"])
            a[2] += int(r["low"])
            a[3] += int(r["high"])
    for k in base_m:
        by_m.setdefault(k, [0, 0, 0, 0])
    for k in base_r:
        by_r.setdefault(k, [0, 0, 0, 0])
    base_total = sum(v[0] for v in base_m.values())
    acc_total = sum(v[1] for v in base_m.values())
    tot = [len(planned), sum(v[1] for v in by_m.values()), sum(v[2] for v in by_m.values()), sum(v[3] for v in by_m.values())]
    cells = {}
    for r in planned:
        a = cells.setdefault(r["repo"], {}).setdefault(r["milestone"], {"rows": 0, "point": 0, "baseline": 0, "accepted": 0})
        a["rows"] += 1
        a["point"] += int(r["weight_point"])
    for (repo, ms), (b, acc) in _base_cells(c).items():
        a = cells.setdefault(repo, {}).setdefault(ms, {"rows": 0, "point": 0, "baseline": 0, "accepted": 0})
        a["baseline"] += b
        a["accepted"] += acc
    tasks = [{"id": r["id"], "repo": r["repo"], "milestone": r["milestone"], "title": r["title"],
              "weight": int(r["weight_point"]), "status": r["execution_status"]} for r in planned]
    return {"titles": titles(text) if text else {}, "matrix": cells, "tasks": tasks, "file": FILE, "rows": tot[0], "point": tot[1], "low": tot[2], "high": tot[3],
            "retired_parents": sum(1 for r in rows if r["record_type"] == "RETIRED_PARENT"),
            "v2_baseline_weight": base_total, "v2_accepted_weight": acc_total,
            "by_milestone": {k: {"rows": v[0], "point": v[1], "low": v[2], "high": v[3],
                                 "baseline": (base_m.get(k) or [0, 0])[0], "accepted": (base_m.get(k) or [0, 0])[1]}
                             for k, v in sorted(by_m.items())},
            "by_repo": {k: {"rows": v[0], "point": v[1], "low": v[2], "high": v[3],
                                   "baseline": (base_r.get(k) or [0, 0])[0], "accepted": (base_r.get(k) or [0, 0])[1]} for k, v in sorted(by_r.items(), key=lambda kv: REPOS.index(kv[0]) if kv[0] in REPOS else 99)}}


def view_lines(c):
    s = c.get("plan_register")
    L = ["## Approved plan by milestone and repository (owner-approved; no credit; not the baseline)", ""]
    if not s:
        return []
    total = s["v2_baseline_weight"] + s["point"]
    lo_t, hi_t = s["v2_baseline_weight"] + s["low"], s["v2_baseline_weight"] + s["high"]
    share = f"{s['v2_accepted_weight'] / total * 100:.1f}%"
    share_lo, share_hi = f"{s['v2_accepted_weight'] / hi_t * 100:.1f}%", f"{s['v2_accepted_weight'] / lo_t * 100:.1f}%"
    L += [f"Source: [SEVEN_REPO_PLAN_REGISTER.md](../planning/SEVEN_REPO_PLAN_REGISTER.md), recorded as an owner-approved planning record in D-109. "
          "Planning weights are estimates, not baseline weights: they earn no credit and are not part of the 155/171 figure above. "
          "Each row below keeps the V2 baseline and the approved plan in separate columns.", "",
          f"V2 baseline weight {s['v2_baseline_weight']} ({s['v2_accepted_weight']} accepted). Approved plan {s['rows']} rows, {s['point']} "
          f"[{s['low']}-{s['high']}] ({s['retired_parents']} retired parents not counted). Total V2 plan weight {total} [{lo_t}-{hi_t}]; "
          f"provisional accepted share {s['v2_accepted_weight']}/{total} = {share} [{share_lo}-{share_hi}].", "",
          "| Milestone | V2 baseline weight | Accepted weight | Plan rows | Plan weight [low-high] | Total plan weight |", "|---|---|---|---|---|---|"]
    for k, v in s["by_milestone"].items():
        L.append(f"| {k} | {v['baseline']} | {v['accepted']} | {v['rows']} | {v['point']} [{v['low']}-{v['high']}] | {v['baseline'] + v['point']} |")
    L.append(f"| Total | {s['v2_baseline_weight']} | {s['v2_accepted_weight']} | {s['rows']} | {s['point']} [{s['low']}-{s['high']}] | {total} |")
    L += ["", "| Repository | Plan rows | Plan weight [low-high] |", "|---|---|---|"]
    for k, v in s["by_repo"].items():
        L.append(f"| {k} | {v['rows']} | {v['point']} [{v['low']}-{v['high']}] |")
    L.append(f"| Total | {s['rows']} | {s['point']} [{s['low']}-{s['high']}] |")
    L += ["", "V2-M6 (physical validation) is on HOLD and excluded. Mechanical, actuator, kritva-enterprise_program and kritva-raas work are outside this plan.", ""]
    return L


def load(root):
    """Return (rows, text, errors); (None, None, []) when the register is absent."""
    p = Path(root) / FILE
    if not p.exists():
        return None, None, []
    text = p.read_text(encoding="utf-8")
    try:
        rows = parse(text)
    except ValueError as e:
        return None, text, [str(e)]
    return rows, text, validate(rows, text)
