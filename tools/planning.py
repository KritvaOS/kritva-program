#!/usr/bin/env python3
"""V2 planning layer (D-044): milestones, repository pipeline, pending decisions and pending reviews.

Display and planning only. Nothing here is read by the credit computation, the baseline, approvals or gates.
Inputs (v2/planning/): milestones.json, repo-pipeline.json, decisions.json, reviews.json.
Outputs (generated, never edited by hand): V2_MILESTONE_PLAN.md, V2_REPO_PLAN.md, PENDING_DECISIONS.md, PENDING_REVIEWS.md.

Rules:
* Status, owner, due date and blocking state come from structured fields only. Free text is never parsed.
* Missing owners and dates are shown as UNASSIGNED and NO_DUE_DATE_RECORDED, never guessed.
* A HOLD milestone has no target date. Dates are proposed until approved.
* Decisions in PROPOSED or IN_REVIEW are pending; reviews in PENDING, IN_PROGRESS or CHANGES_REQUESTED are pending.
  Superseded records leave the active queue.

  python3 tools/planning.py            # validate and write the generated Markdown
  python3 tools/planning.py --check    # validate and fail if the generated Markdown is out of date
Stdlib only.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

PLAN = "v2/planning"
OUTPUTS = ("V2_MILESTONE_PLAN.md", "V2_REPO_PLAN.md", "PENDING_DECISIONS.md", "PENDING_REVIEWS.md")
DECISION_STATUS = ("PROPOSED", "IN_REVIEW", "ACCEPTED", "REJECTED", "SUPERSEDED")
REVIEW_STATUS = ("PENDING", "IN_PROGRESS", "CHANGES_REQUESTED", "APPROVED", "REJECTED", "WAIVED")
MILESTONE_STATUS = ("PROPOSED", "READY", "IN_PROGRESS", "BLOCKED", "ON_HOLD", "IN_REVIEW", "CLOSED", "CANCELLED")
SCHEDULE_STATUS = ("PROPOSED", "APPROVED", "HOLD")
PENDING_D = {"PROPOSED", "IN_REVIEW"}
PENDING_R = {"PENDING", "IN_PROGRESS", "CHANGES_REQUESTED"}
PHASES = [f"V2-M{i}" for i in range(9)]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
MID = re.compile(r"^V2-M[0-8]$")
SUBID = re.compile(r"^V2-M[0-8]-[A-Z0-9]+-\d{3}$")
REPO_NAME = re.compile(r"^KritvaOS/[A-Za-z0-9._-]+$")


def load(root):
    d = Path(root) / PLAN
    return {k: json.loads((d / f).read_text(encoding="utf-8")) for k, f in
            (("milestones", "milestones.json"), ("pipeline", "repo-pipeline.json"),
             ("decisions", "decisions.json"), ("reviews", "reviews.json"))}


def _date_ok(s):
    if not (isinstance(s, str) and DATE.match(s)):
        return False
    try:
        dt.date.fromisoformat(s)
        return True
    except ValueError:
        return False


def topo(repos):
    """Return (ordered repo_ids, errors). Order: dependencies first, then sequence, then id."""
    ids = {r["repo_id"] for r in repos}
    errs, order, done = [], [], set()
    deps = {r["repo_id"]: r.get("depends_on", []) for r in repos}
    for rid, ds in deps.items():
        for d in ds:
            if d not in ids:
                errs.append(f"{rid}: depends on unknown repository {d!r}")
    if errs:
        return [], errs
    seq = {r["repo_id"]: (r["sequence"], r["repo_id"]) for r in repos}
    remaining = set(ids)
    while remaining:
        ready = sorted((x for x in remaining if all(d in done for d in deps[x])), key=lambda x: seq[x])
        if not ready:
            return [], [f"dependency cycle among: {', '.join(sorted(remaining))}"]
        order.append(ready[0])
        done.add(ready[0])
        remaining.discard(ready[0])
    return order, []


def validate(data):
    errs = []
    m, p, d, r = data["milestones"], data["pipeline"], data["decisions"], data["reviews"]
    # ---- milestones
    ms = m.get("milestones") or []
    ids = [x.get("id") for x in ms]
    if ids != PHASES:
        errs.append(f"milestones must be exactly {PHASES} in order")
    ps = m.get("program_start") or {}
    if not _date_ok(ps.get("date")):
        errs.append("program_start.date must be YYYY-MM-DD")
    hz = m.get("horizon") or {}
    if not _date_ok(hz.get("end")):
        errs.append("horizon.end must be YYYY-MM-DD")
    start, end = ps.get("date"), hz.get("end")
    prev = None
    for x in ms:
        i = x.get("id")
        if x.get("schedule_status") not in SCHEDULE_STATUS:
            errs.append(f"{i}: schedule_status must be one of {list(SCHEDULE_STATUS)}")
        if x.get("schedule_status") == "HOLD":
            if x.get("target_date") is not None:
                errs.append(f"{i}: a HOLD milestone must not have a target_date")
        else:
            t = x.get("target_date")
            if not _date_ok(t):
                errs.append(f"{i}: target_date must be YYYY-MM-DD unless HOLD")
            elif start and end and not (start <= t <= end):
                errs.append(f"{i}: target_date {t} is outside the program horizon {start}..{end}")
            elif prev and t < prev:
                errs.append(f"{i}: target_date {t} is earlier than a previous milestone ({prev})")
            if _date_ok(t):
                prev = t
        for dep in x.get("depends_on", []):
            if dep not in PHASES:
                errs.append(f"{i}: unknown dependency {dep!r}")
            elif PHASES.index(dep) >= PHASES.index(i):
                errs.append(f"{i}: depends on {dep}, which is not an earlier phase")
        if not x.get("outcome") or not x.get("exit_conditions"):
            errs.append(f"{i}: outcome and exit_conditions are required")
        if x.get("schedule_status") == "APPROVED" and not x.get("approval"):
            errs.append(f"{i}: an APPROVED schedule needs an approval record")
        if x.get("closure_record") and not str(x["closure_record"]).endswith("COMPLETION_RECORD.md"):
            errs.append(f"{i}: closure_record must point to a COMPLETION_RECORD.md")
        if x.get("owner") is not None and not str(x["owner"]).strip():
            errs.append(f"{i}: owner must be null or a name")
    # ---- pipeline
    repos = p.get("repositories") or []
    rids = [x.get("repo_id") for x in repos]
    if len(set(rids)) != len(rids):
        errs.append("duplicate repo_id in repo-pipeline.json")
    codes = [x.get("code") for x in repos]
    if len(set(codes)) != len(codes):
        errs.append("duplicate repo code in repo-pipeline.json")
    roles = set((p.get("roles") or {}))
    kg, kl = set(p.get("known_github_checks", [])), set(p.get("known_local_gates", []))
    for x in repos:
        n = x.get("repo_id")
        if not REPO_NAME.match(str(x.get("github_repo", ""))) or x["github_repo"].split("/")[-1] != n:
            errs.append(f"{n}: github_repo must be KritvaOS/{n}")
        if not re.match(r"^[A-Z0-9]+$", str(x.get("code", ""))):
            errs.append(f"{n}: code must be upper-case alphanumeric")
        if not isinstance(x.get("sequence"), int):
            errs.append(f"{n}: sequence must be an integer")
        for role in x.get("required_approvals", []):
            if role not in roles:
                errs.append(f"{n}: unknown approval role {role!r}")
        if not x.get("required_approvals"):
            errs.append(f"{n}: at least one required approval role")
        for c in x.get("required_github_checks", []):
            if c not in kg:
                errs.append(f"{n}: unknown GitHub check {c!r}")
        for c in x.get("local_gates", []):
            if c not in kl:
                errs.append(f"{n}: unknown local gate {c!r}")
        for pm in x.get("phase_milestones", []):
            if pm not in PHASES:
                errs.append(f"{n}: unknown phase milestone {pm!r}")
        if (x.get("release_policy") or {}).get("annotated") is not True:
            errs.append(f"{n}: release tags must be annotated")
    people = p.get("people") or {}
    for role, info in (p.get("roles") or {}).items():
        for h in info.get("holders", []):
            if h not in people or not people[h].get("github_login"):
                errs.append(f"role {role}: holder {h!r} has no github_login in people")
    for x in repos:
        for q in x.get("protected_paths", []):
            if not isinstance(q, str) or q.startswith("/") or ".." in q:
                errs.append(f"{x.get('repo_id')}: protected path {q!r} must be a relative path")
    _, terrs = topo(repos)
    errs += terrs
    if p.get("merge_policy", {}).get("method") not in ("merge", "squash", "rebase"):
        errs.append("merge_policy.method must be merge, squash or rebase")
    code_set = set(codes)
    # ---- repo milestones
    seen = set()
    by_repo = {x["code"]: x for x in repos if "code" in x}
    for s in m.get("repo_milestones") or []:
        i = s.get("id")
        if not SUBID.match(str(i)):
            errs.append(f"repo milestone id {i!r} must look like V2-M2-SENSE-001")
            continue
        if i in seen:
            errs.append(f"{i}: duplicate repo milestone id")
        seen.add(i)
        if s.get("milestone_id") not in PHASES or not i.startswith(s["milestone_id"] + "-"):
            errs.append(f"{i}: milestone_id does not match the id")
        if s.get("repo_code") not in code_set or f"-{s.get('repo_code')}-" not in i:
            errs.append(f"{i}: repo_code is not a registered code or does not match the id")
        else:
            if s["milestone_id"] not in by_repo[s["repo_code"]].get("phase_milestones", []):
                errs.append(f"{i}: the repository does not list {s['milestone_id']} in phase_milestones")
        if s.get("status") not in MILESTONE_STATUS:
            errs.append(f"{i}: status must be one of {list(MILESTONE_STATUS)}")
        hold = next((x for x in ms if x.get("id") == s.get("milestone_id")), {}).get("schedule_status") == "HOLD"
        if hold and s.get("status") not in ("ON_HOLD", "CANCELLED"):
            errs.append(f"{i}: a milestone under a HOLD phase must be ON_HOLD")
        if not s.get("outcome"):
            errs.append(f"{i}: outcome is required")
        if s.get("tasks"):
            errs.append(f"{i}: tasks must stay empty until a real task exists (no placeholder tasks)")
    for x in repos:
        for pm in x.get("phase_milestones", []):
            if not any(s.get("repo_code") == x["code"] and s.get("milestone_id") == pm for s in m.get("repo_milestones", [])):
                errs.append(f"{x['repo_id']}: lists {pm} but has no repo milestone for it")
    # ---- decisions and reviews
    ids_seen = set()
    for kind, doc, statuses in (("DECISION", d, DECISION_STATUS), ("REVIEW", r, REVIEW_STATUS)):
        recs = doc.get("records") or []
        for x in recs:
            i = x.get("record_id")
            if not re.match(r"^(PD|REV)-\d{3}$", str(i)):
                errs.append(f"{kind} id {i!r} must look like PD-001 or REV-001")
            if i in ids_seen:
                errs.append(f"{i}: duplicate record id")
            ids_seen.add(i)
            if x.get("record_type") != kind:
                errs.append(f"{i}: record_type must be {kind}")
            if x.get("status") not in statuses:
                errs.append(f"{i}: status must be one of {list(statuses)}")
            if not _date_ok(x.get("created_at")):
                errs.append(f"{i}: created_at must be YYYY-MM-DD")
            if x.get("due_date") is not None and not _date_ok(x.get("due_date")):
                errs.append(f"{i}: due_date must be null or YYYY-MM-DD")
            for b in x.get("blocks", []):
                if b not in PHASES:
                    errs.append(f"{i}: blocks unknown milestone {b!r}")
            if kind == "REVIEW":
                a = x.get("artifact") or {}
                if not (REPO_NAME.match(str(a.get("repo", ""))) and a.get("path")):
                    errs.append(f"{i}: artifact needs repo and path")
                if a.get("commit_sha") is not None and not SHA.match(str(a["commit_sha"])):
                    errs.append(f"{i}: commit_sha must be null or 40 hex characters (no placeholders)")
                if x.get("review_role") not in roles:
                    errs.append(f"{i}: unknown review_role {x.get('review_role')!r}")
            else:
                if x.get("status") == "ACCEPTED" and not x.get("approval_ref"):
                    errs.append(f"{i}: an ACCEPTED decision needs approval_ref")
                if not x.get("required_action"):
                    errs.append(f"{i}: required_action is required")
            if x.get("status") == "WAIVED" and not x.get("approval_ref"):
                errs.append(f"{i}: WAIVED needs approval_ref")
            for s in x.get("supersedes", []):
                if s not in {y.get("record_id") for y in recs}:
                    errs.append(f"{i}: supersedes unknown record {s!r}")
    return errs


def _superseded(recs):
    return {s for x in recs for s in x.get("supersedes", [])}


def pending_decisions(data):
    recs = data["decisions"]["records"]
    gone = _superseded(recs)
    return [x for x in recs if x["status"] in PENDING_D and x["record_id"] not in gone]


def pending_reviews(data):
    recs = data["reviews"]["records"]
    gone = _superseded(recs)
    return [x for x in recs if x["status"] in PENDING_R and x["record_id"] not in gone]


def summary(data):
    """Compact facts for the status view. Counts only; never credit."""
    pd, pr = pending_decisions(data), pending_reviews(data)
    ms = data["milestones"]["milestones"]
    return {"plan_status": data["milestones"]["status"], "program_start": data["milestones"]["program_start"]["date"],
            "horizon_end": data["milestones"]["horizon"]["end"],
            "milestones": [{"id": x["id"], "phase": f"{x['phase_id']} {x['phase_name']}", "target_date": x["target_date"],
                            "schedule_status": x["schedule_status"], "closed": bool(x.get("closure_record"))} for x in ms],
            "pending_decisions": len(pd), "blocking_decisions": sum(1 for x in pd if x.get("blocking")),
            "pending_reviews": len(pr), "repositories": len(data["pipeline"]["repositories"])}


def _cell(x):
    return str(x).replace("|", "/").replace("\n", " ")


def render_milestones(data):
    m, p = data["milestones"], data["pipeline"]
    L = ["<!-- GENERATED by tools/planning.py from v2/planning/*.json. Do not edit by hand. -->", "",
         "# V2 Milestone Plan (proposed)", "",
         f"Plan {m['plan_id']}, status **{m['status']}**. Program start {m['program_start']['date']} ({m['program_start']['status']}: {m['program_start']['approval']}); "
         f"horizon {m['horizon']['months']} months, ending {m['horizon']['end']} ({m['horizon']['status']}). {m['date_status_note']}", "",
         "This is a planning layer. It is not the frozen baseline: it adds no tasks, weights or credit, and it never changes accepted progress "
         "(baseline v2 stays as recorded in [tracking/STATUS_VIEW.md](../tracking/STATUS_VIEW.md)). A milestone closes only through an approved COMPLETION_RECORD.md; "
         "a merge, a passing CI run or a tag does not close it.", "",
         "## Top-level milestones", "", "| ID | Phase | Target | Schedule status | Depends on | Outcome |", "|---|---|---|---|---|---|"]
    for x in m["milestones"]:
        L.append(f"| {x['id']} | {x['phase_id']} {x['phase_name']} | {x['target_date'] or 'NO DATE (HOLD)'} | {x['schedule_status']} | "
                 f"{', '.join(x['depends_on']) or '-'} | {_cell(x['outcome'])} |")
    L += ["", "Dependency rule: V2-M7 and V2-M8 close only for the scope actually validated. Any criterion that needs physical-robot evidence stays blocked by V2-M6.", ""]
    for x in m["milestones"]:
        L += [f"### {x['id']} {x['phase_id']} {x['phase_name']}", "",
              f"Target: {x['target_date'] or 'none (HOLD)'}; schedule status {x['schedule_status']}; owner {x['owner'] or 'UNASSIGNED'}; "
              f"closure record {x['closure_record'] or 'none'}.", "", "Exit conditions:", ""]
        L += [f"- {c}" for c in x["exit_conditions"]]
        subs = [s for s in m["repo_milestones"] if s["milestone_id"] == x["id"]]
        L += ["", "| Repository milestone | Repository | Status | Outcome |", "|---|---|---|---|"]
        for s in subs:
            repo = next(r["repo_id"] for r in p["repositories"] if r["code"] == s["repo_code"])
            L.append(f"| {s['id']} | {repo} | {s['status']} | {_cell(s['outcome'])} |")
        L.append("")
    return "\n".join(L).rstrip("\n") + "\n"


def render_repos(data):
    p, m = data["pipeline"], data["milestones"]
    order, _ = topo(p["repositories"])
    by = {r["repo_id"]: r for r in p["repositories"]}
    L = ["<!-- GENERATED by tools/planning.py from v2/planning/*.json. Do not edit by hand. -->", "",
         "# V2 Repository Plan and PR Approval Sequence (proposed)", "",
         f"Manifest {p['manifest_id']}, status **{p['status']}**. The order is a default topological order from the dependency list, not permission to merge "
         "every repository regardless of readiness. Independent work can go in parallel; a downstream PR pins the exact dependency versions it was tested against. "
         "The manifest is consumed by `scripts/pipeline/manifest.py` and `ship-prs.sh`. Standards: [ACCEPTANCE_STANDARD.md](ACCEPTANCE_STANDARD.md).", "",
         f"Merge method: **{p['merge_policy']['method']}** (decision {p['merge_policy']['method_decision']} is pending). Releases use annotated SemVer tags created only after the approved merge; a tag is evidence, not milestone closure.", "",
         "## Approval roles", "", "| Role | Holders | Basis |", "|---|---|---|"]
    for k, v in p["roles"].items():
        L.append(f"| {k} | {', '.join(v['holders']) or 'UNASSIGNED'} | {v['basis']} |")
    L += ["", "## PR approval sequence", "",
          "| # | Repository | Kind | Depends on | Required approvals | Required GitHub checks (workflow names) | Local gates | Phase milestones |", "|---|---|---|---|---|---|---|---|"]
    for i, rid in enumerate(order, 1):
        r = by[rid]
        L.append(f"| {i} | {rid}{' (HOLD)' if r['on_hold'] else ''} | {r['kind']} | {', '.join(r['depends_on']) or '-'} | {', '.join(r['required_approvals'])} | "
                 f"{', '.join(r['required_github_checks'])} | {', '.join(r['local_gates'])} | {', '.join(r['phase_milestones'])} |")
    L += ["", "## Repository registry", "", "| Repository | Code | Workstream | Task ID prefix | Baselined |", "|---|---|---|---|---|"]
    for rid in order:
        r = by[rid]
        L.append(f"| {rid} | {r['code']} | {r['workstream_id']} | {r['task_prefix']} | {'yes' if r['baselined'] else 'no (planning only)'} |")
    L += ["", "## Per-repository milestones", ""]
    for rid in order:
        r = by[rid]
        L += [f"### {rid}", ""]
        for s in m["repo_milestones"]:
            if s["repo_code"] == r["code"]:
                d = next(x for x in m["milestones"] if x["id"] == s["milestone_id"])
                L.append(f"- {s['id']} ({d['target_date'] or 'no date, HOLD'}, {s['status']}): {s['outcome']}")
        L.append("")
    return "\n".join(L).rstrip("\n") + "\n"


def _queue(title, recs, kind, data):
    L = ["<!-- GENERATED by tools/planning.py from v2/planning/*.json. Do not edit by hand. -->", "", f"# {title}", "",
         "Generated from structured records only (status, owner, due date and blocking state are fields, not parsed text). "
         "Missing owners and dates are shown as UNASSIGNED and NO_DUE_DATE_RECORDED. Superseded records are excluded. "
         "Open gates are tracked separately in the Gates section of [tracking/STATUS_DETAIL.md](../tracking/STATUS_DETAIL.md), not here.", ""]
    if not recs:
        return "\n".join(L + ["No pending records."]) + "\n"
    if kind == "D":
        L += [f"{len(recs)} pending, {sum(1 for x in recs if x.get('blocking'))} marked blocking. Decision authority is the owner (Dinesh) unless a record says otherwise.", "",
              "| ID | Decision needed | Status | Blocking | Blocks | Scope | Owner | Due | Required action |", "|---|---|---|---|---|---|---|---|---|"]
        for x in recs:
            sc = ", ".join(x["scope"].get("repo_ids", []) + x["scope"].get("phase_ids", [])) or "program"
            L.append(f"| {x['record_id']} | {_cell(x['title'])} | {x['status']} | {'yes' if x.get('blocking') else 'no'} | {', '.join(x.get('blocks', [])) or '-'} | "
                     f"{_cell(sc)} | {x.get('owner') or 'UNASSIGNED'} | {x.get('due_date') or 'NO_DUE_DATE_RECORDED'} | {_cell(x['required_action'])} |")
    else:
        L += [f"{len(recs)} pending.", "",
              "| ID | Review | Status | Role | Reviewer | Artifact | Revision | Required checks | Blocks |", "|---|---|---|---|---|---|---|---|---|"]
        for x in recs:
            a = x["artifact"]
            L.append(f"| {x['record_id']} | {_cell(x['title'])} | {x['status']} | {x['review_role']} | {x.get('reviewer') or 'UNASSIGNED'} | "
                     f"{a['repo'].split('/')[-1]}:{a['path']} | {a['commit_sha'][:7] if a.get('commit_sha') else 'NOT_YET_PINNED'} | {_cell(', '.join(x.get('required_checks', [])))} | {', '.join(x.get('blocks', [])) or '-'} |")
    return "\n".join(L).rstrip("\n") + "\n"


def render_all(data):
    return {"V2_MILESTONE_PLAN.md": render_milestones(data), "V2_REPO_PLAN.md": render_repos(data),
            "PENDING_DECISIONS.md": _queue("Pending Decisions (generated)", pending_decisions(data), "D", data),
            "PENDING_REVIEWS.md": _queue("Pending Reviews (generated)", pending_reviews(data), "R", data)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root)
    data = load(root)
    errs = validate(data)
    for e in errs:
        print(f"ERROR: {e}", file=sys.stderr)
    if errs:
        return 1
    out = render_all(data)
    base = root / PLAN
    if a.check:
        drift = [n for n, t in out.items() if not (base / n).exists() or (base / n).read_text(encoding="utf-8") != t]
        if drift:
            print("generated planning output out of date: " + ", ".join(drift), file=sys.stderr)
            return 4
        return 0
    for n, t in out.items():
        (base / n).write_text(t, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
