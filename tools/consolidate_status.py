#!/usr/bin/env python3
"""Consolidate per-repo task reports and central approvals into program status.

Authority model (D-011):
  * Engineering repos REPORT facts: execution, git_sync, readiness, evidence.
  * kritva-program DECIDES: baseline (task IDs, weights, ownership), approvals
    (review/acceptance/waivers). A repo can never accept its own work.
  * This script COMPUTES: accepted progress and the generated status views.

Reads (kritva-program repo):
  v2/tracking/workstreams.json  canonical workstream registry
  v2/tracking/baseline.json     approved baseline (tasks, weights, ownership)
  v2/tracking/approvals.json    append-only approval ledger
  v2/tracking/sources.json      where to fetch each repo's status.json
Inputs: status.json (schema 2.0) per repo, via `gh api` (--fetch) or a
directory (--sources-dir).
Outputs (deterministic, no wall-clock values):
  v2/tracking/consolidated_status.json, v2/tracking/STATUS_VIEW.md

Also (D-015..D-017):
  * gates are first-class baseline records; an OPEN gate that blocks TASK_CREDIT
    gives zero credit to every task in its scope, whatever the approvals say.
  * every task row carries a credit_reason (the audited chain, or why zero).
  * an approved baseline must match its frozen record in v2/tracking/baselines/.
  * --fetch pins each source to a resolved commit SHA and fails closed.
  * --snapshot appends a hash-chained record to v2/history/ (failed
    reconciliations go to v2/history/failures/, never into snapshots).

Exit codes: 0 ok | 1 validation errors | 2 config/IO error |
            3 stale/missing sources (--strict) | 4 --check drift |
            5 history verification failed
Stdlib only. Never commits, pushes, or handles tokens (gh reads GH_TOKEN itself).
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPORT_ENUMS = {
    "execution": {"NOT_STARTED", "IN_PROGRESS", "BLOCKED", "COMPLETE"},
    "git_sync": {"NOT_COMMITTED", "COMMITTED", "NOT_SYNCED", "SYNCED"},
    "readiness": {"PLANNABLE", "IMPLEMENTABLE", "HARDWARE-BLOCKED"},
}
REVIEW = {"NOT_REVIEWED", "IN_REVIEW", "CHANGES_REQUIRED", "APPROVED"}
ACCEPTANCE = {"NOT_RUN", "PASS", "FAIL", "WAIVED"}
EVIDENCE_TYPES = {"software", "simulation", "physical"}
TOP_KEYS = {"schema_version", "workstream_id", "repo", "source", "tasks", "updated_at"}
TASK_KEYS = {"task_id", *REPORT_ENUMS, "evidence"}
EV_REQ = {"type", "uri", "description"}
EV_KEYS = EV_REQ | {"commit", "ci_run", "report_sha256", "result"}
APPROVAL_REQ = {"approval_id", "task_id", "baseline_version", "source_repo", "source_commit",
                "review_status", "acceptance", "approver", "approved_at", "evidence_refs"}
APPROVAL_KEYS = APPROVAL_REQ | {"rationale", "supersedes"}
SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
TRACK = "v2/tracking"
HISTORY = "v2/history"
GATE_STATUS = {"OPEN", "CLOSED"}
GATE_EFFECTS = {"TASK_CREDIT", "PHASE_EXIT", "RELEASE"}
PHASES = ["FOUNDATION", "STUDIO", "BUILD & ARTIFACT", "CONTROL PLANE", "BOOKING & COMMERCIAL",
          "EXECUTION", "LAB & ROBOT", "LIVE & RESULTS", "PRODUCTION"]


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f"config/IO error: {path}: {e}") from None


def parse_ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def gh_json(*args):
    r = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def fetch_sources(cfg):
    """Fetch each status.json at a PINNED commit. Fails closed: any problem excludes the source.

    ref (branch, tag or SHA) is resolved to a commit SHA first and the file is read at that SHA, so a
    run is reproducible. Repo and workstream identity must match sources.json, and the report's own
    source.commit must be the fetched commit or one of its ancestors. Pinning proves WHICH revision was
    read, not that its facts are true. Returns (found, problems, meta).
    """
    found, problems, meta = {}, [], {}
    for s in cfg["sources"]:
        ws, repo = s["workstream_id"], s["repo"]
        if SHA.match(str(s["ref"])):
            sha = s["ref"]
        else:
            c = gh_json(f"repos/{repo}/commits/{s['ref']}")
            sha = (c or {}).get("sha", "")
        if not SHA.match(str(sha)):
            problems.append(f"{ws}: cannot resolve {repo}@{s['ref']} to a commit (UNVERIFIED)")
            continue
        api = f"repos/{repo}/contents/{cfg['status_path']}?ref={sha}"
        f = gh_json(api)
        if f is None:
            problems.append(f"{ws}: fetch failed for {repo}@{sha[:7]} (UNVERIFIED)")
            continue
        try:
            doc = json.loads(base64.b64decode(f["content"]))
        except (KeyError, ValueError) as e:
            problems.append(f"{ws}: unparseable status file ({e})")
            continue
        if not isinstance(doc, dict) or str(doc.get("repo", "")).lower() != repo.lower() or doc.get("workstream_id") != ws:
            problems.append(f"{ws}: report identity does not match sources.json ({repo}); rejected")
            continue
        sc = (doc.get("source") or {}).get("commit", "")
        if SHA.match(str(sc)) and sc != sha:
            cmp = gh_json(f"repos/{repo}/compare/{sc}...{sha}")
            if (cmp or {}).get("status") not in ("ahead", "identical"):
                problems.append(f"{ws}: report source.commit {sc[:7]} is not an ancestor of {sha[:7]}; rejected")
                continue
        found[ws] = (f"{repo}@{sha[:7]}", doc)
        meta[ws] = {"repo": repo, "ref": s["ref"], "resolved_commit": sha}
    return found, problems, meta


def read_dir(path):
    found = {}
    for p in sorted(Path(path).glob("*.json")):
        d = load_json(p)
        found[d.get("workstream_id", p.stem)] = (p.name, d)
    return found


def validate_report(doc, reg, base_tasks):
    """Validate one repo report (schema 2.0). Returns list of errors."""
    e = []
    if set(doc) - TOP_KEYS:
        e.append(f"unknown top-level keys {sorted(set(doc) - TOP_KEYS)}")
    if TOP_KEYS - set(doc):
        return e + [f"missing keys {sorted(TOP_KEYS - set(doc))}"]
    if doc["schema_version"] != "2.0":
        return e + [f"unsupported schema_version {doc['schema_version']!r} (expected 2.0)"]
    ws_id = doc["workstream_id"]
    ws = reg.get(ws_id)
    if ws is None:
        return e + [f"unknown workstream_id {ws_id!r}"]
    if ws.get("repo") and ws["repo"] != doc["repo"]:
        e.append(f"repo {doc['repo']!r} conflicts with registry {ws['repo']!r}")
    if not isinstance(doc["source"], dict) or not SHA.match(str(doc["source"].get("commit", ""))):
        e.append("source.commit must be a 40-hex SHA")
    try:
        parse_ts(doc["updated_at"])
    except (ValueError, AttributeError):
        e.append("updated_at is not an ISO-8601 date-time")
    seen = set()
    for t in doc["tasks"]:
        tid = t.get("task_id", "?")
        tag = f"{ws_id}/{tid}"
        if set(t) != TASK_KEYS:
            e.append(f"{tag}: keys must be exactly {sorted(TASK_KEYS)} (repos must not report review/acceptance)")
            continue
        if tid in seen:
            e.append(f"{tag}: duplicate task_id")
        seen.add(tid)
        bt = base_tasks.get(tid)
        if base_tasks and bt is None:
            e.append(f"{tag}: task_id not in approved baseline")
        elif bt and bt["workstream_id"] != ws_id:
            e.append(f"{tag}: owned by {bt['workstream_id']} in baseline")
        for k, allowed in REPORT_ENUMS.items():
            if t[k] not in allowed:
                e.append(f"{tag}: {k}={t[k]!r} not allowed")
        for ev in t["evidence"]:
            if not EV_REQ <= set(ev) or set(ev) - EV_KEYS:
                e.append(f"{tag}: malformed evidence entry")
                continue
            if ev["type"] not in EVIDENCE_TYPES:
                e.append(f"{tag}: evidence type {ev['type']!r} not allowed")
            if not isinstance(ev["uri"], str) or not ev["uri"].strip():
                e.append(f"{tag}: evidence uri must be a non-empty string")
            if ev.get("commit") and not SHA.match(str(ev["commit"])):
                e.append(f"{tag}: evidence commit must be a 40-hex SHA")
            if ev.get("report_sha256") and not SHA256.match(str(ev["report_sha256"])):
                e.append(f"{tag}: evidence report_sha256 must be 64-hex")
        if ws.get("hold") and t["execution"] != "NOT_STARTED":
            e.append(f"{tag}: mechanical HOLD violated (execution must stay NOT_STARTED)")
        if ws.get("hold") and t["readiness"] == "IMPLEMENTABLE":
            e.append(f"{tag}: mechanical HOLD violated (readiness IMPLEMENTABLE)")
    owned = lambda mid: [b for b in base_tasks.values() if b.get("milestone_id") == mid and b["workstream_id"] == ws_id]
    for pid in ws.get("protected_ids", []):  # protected MILESTONE IDs must keep baseline tasks
        if base_tasks and not owned(pid):
            e.append(f"{ws_id}: protected milestone {pid} has no baseline tasks (missing or renamed)")
    reported = {t.get("task_id"): t for t in doc["tasks"]}
    for cid in ws.get("closed_ids", []):  # closed MILESTONES must stay COMPLETE
        for b in owned(cid):
            t = reported.get(b["id"])
            if t is None or t.get("execution") != "COMPLETE":
                e.append(f"{ws_id}: task {b['id']} of closed milestone {cid} is missing or reopened")
    return e


def validate_approvals(ledger, base_tasks, base_version):
    """Validate the approval ledger. Returns (errors, effective approval per task)."""
    e, by_id, authorized = [], {}, set(ledger.get("authorized_approvers", []))
    for a in ledger["approvals"]:
        aid = a.get("approval_id", "?")
        if not APPROVAL_REQ <= set(a) or set(a) - APPROVAL_KEYS:
            e.append(f"approval {aid}: malformed record")
            continue
        if aid in by_id:
            e.append(f"approval {aid}: duplicate approval_id")
            continue
        by_id[aid] = a
        if a["task_id"] not in base_tasks:
            e.append(f"approval {aid}: unknown task_id {a['task_id']!r}")
        if a["review_status"] not in REVIEW or a["acceptance"] not in ACCEPTANCE:
            e.append(f"approval {aid}: invalid review/acceptance value")
        if not SHA.match(str(a["source_commit"])):
            e.append(f"approval {aid}: source_commit must be 40-hex")
        if a["approver"] not in authorized:
            e.append(f"approval {aid}: approver {a['approver']!r} is not an authorized approver")
        if a["acceptance"] in ("FAIL", "WAIVED") and not str(a.get("rationale", "")).strip():
            e.append(f"approval {aid}: rationale required for {a['acceptance']}")
        if a["acceptance"] == "PASS" and (a["review_status"] != "APPROVED" or not a["evidence_refs"]):
            e.append(f"approval {aid}: PASS requires review APPROVED and evidence_refs")
        try:
            parse_ts(a["approved_at"])
        except (ValueError, AttributeError):
            e.append(f"approval {aid}: approved_at is not ISO-8601")
        if a["baseline_version"] != base_version:
            e.append(f"approval {aid}: baseline_version {a['baseline_version']} != current {base_version}")
    superseded = set()
    for aid, a in by_id.items():
        s = a.get("supersedes")
        if s:
            if s not in by_id:
                e.append(f"approval {aid}: supersedes unknown approval {s!r}")
            superseded.add(s)
    effective = {}
    for aid, a in by_id.items():  # file order = append order
        if aid not in superseded:
            effective[a["task_id"]] = a
    return e, effective


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def baseline_hash(base):
    """Hash of the baseline DATA (the `approval` block is excluded so it can record the hash)."""
    return sha256_text(canonical({k: v for k, v in base.items() if k != "approval"}))


def validate_baseline(base, authorized, root):
    """Baseline integrity: gates, phases, and (when approved) weights, approval record and frozen copy."""
    e = []
    ids = {t["id"] for t in base["tasks"]}
    ms_ids = {m["id"] for m in base.get("milestones", [])}
    for t in base["tasks"]:
        if t.get("phase") is not None and t["phase"] not in PHASES:
            e.append(f"baseline task {t['id']}: unknown phase {t['phase']!r}")
    seen = set()
    for g in base.get("gates", []):
        gid = g.get("gate_id", "?")
        if gid in seen:
            e.append(f"gate {gid}: duplicate gate_id")
        seen.add(gid)
        if g.get("status") not in GATE_STATUS:
            e.append(f"gate {gid}: status must be one of {sorted(GATE_STATUS)}")
        eff = set(g.get("blocking_effect", []))
        if not eff or eff - GATE_EFFECTS:
            e.append(f"gate {gid}: blocking_effect must be a non-empty subset of {sorted(GATE_EFFECTS)}")
        sc = g.get("scope", {})
        for m in sc.get("milestone_ids", []):
            if m not in ms_ids:
                e.append(f"gate {gid}: unknown milestone {m!r} in scope")
        for t in sc.get("task_ids", []):
            if t not in ids:
                e.append(f"gate {gid}: unknown task {t!r} in scope")
        if not (sc.get("milestone_ids") or sc.get("task_ids")):
            e.append(f"gate {gid}: scope is empty")
        if not str(g.get("closure_criteria", "")).strip():
            e.append(f"gate {gid}: closure_criteria required")
        if g.get("status") == "CLOSED":
            if not SHA.match(str(g.get("evidence_commit") or "")):
                e.append(f"gate {gid}: CLOSED requires a 40-hex evidence_commit")
            try:
                parse_ts(g.get("closed_at"))
            except (ValueError, AttributeError, TypeError):
                e.append(f"gate {gid}: CLOSED requires closed_at (ISO-8601)")
            if g.get("closed_by") not in authorized:
                e.append(f"gate {gid}: closed_by must be an authorized approver")
    if base.get("baseline_approved"):
        for t in base["tasks"]:
            w = t.get("weight")
            if not isinstance(w, int) or isinstance(w, bool) or w <= 0:
                e.append(f"baseline task {t['id']}: approved baseline needs a positive integer weight")
        ap = base.get("approval")
        if not isinstance(ap, dict):
            e.append("approved baseline has no approval record")
        else:
            if ap.get("approver") not in authorized:
                e.append("baseline approval: approver is not an authorized approver")
            if not SHA.match(str(ap.get("canonical_commit", ""))):
                e.append("baseline approval: canonical_commit must be 40-hex")
            if ap.get("baseline_sha256") != baseline_hash(base):
                e.append("baseline approval: baseline_sha256 does not match baseline data (tampered or edited after approval)")
            frozen = root / TRACK / "baselines" / f"baseline_v{base['baseline_version']}.json"
            if not frozen.exists():
                e.append(f"approved baseline has no frozen record {frozen.name}")
            elif frozen.read_text(encoding="utf-8") != (root / TRACK / "baseline.json").read_text(encoding="utf-8"):
                e.append(f"baseline.json differs from frozen record {frozen.name}; a new baseline_version is required")
    return e


def gates_for(task, gates):
    """OPEN gates that block TASK_CREDIT for this task."""
    out = []
    for g in gates:
        if g["status"] != "OPEN" or "TASK_CREDIT" not in g["blocking_effect"]:
            continue
        sc = g["scope"]
        if task["id"] in sc.get("task_ids", []) or task.get("milestone_id") in sc.get("milestone_ids", []):
            out.append(g["gate_id"])
    return sorted(out)


def has_verifiable_evidence(t, commit):
    return [ev for ev in t["evidence"] if ev.get("commit") == commit
            and (ev.get("ci_run") or ev.get("report_sha256"))
            and str(ev.get("result") or "").upper() == "PASS"]


def has_commit_bound_evidence(t):
    return any(ev.get("commit") for ev in t["evidence"])


def compute(base, reports, effective, reg):
    """Per-task rows and accepted progress. Every row says WHY it has or lacks credit."""
    tasks, warnings = [], []
    task_state = {}
    for ws_id, (_, doc) in reports.items():
        for t in doc["tasks"]:
            task_state[t["task_id"]] = (doc, t)
    gates = base.get("gates", [])
    for bt in base["tasks"]:
        row = {"task_id": bt["id"], "workstream_id": bt["workstream_id"], "milestone_id": bt.get("milestone_id"),
               "phase": bt.get("phase"), "weight": bt.get("weight"), "execution": None, "git_sync": None,
               "readiness": None, "acceptance": "NOT_RUN", "evidence_verified": False, "credit": False,
               "blocked_by": gates_for(bt, gates), "credit_reason": ""}
        st = task_state.get(bt["id"])
        ap = effective.get(bt["id"])
        if not st:
            row["credit_reason"] = "no current report from the owning workstream"
            warnings.append(f"{bt['id']}: not reported by {bt['workstream_id']} (no credit)")
        else:
            doc, t = st
            row.update(execution=t["execution"], git_sync=t["git_sync"], readiness=t["readiness"])
            if ap:
                row["acceptance"] = ap["acceptance"]
                row["evidence_verified"] = bool(has_verifiable_evidence(t, ap["source_commit"]))
            reason = None
            if not base.get("baseline_approved"):
                reason = "baseline is a DRAFT (not approved by an authorized approver)"
            elif bt.get("weight") is None:
                reason = "baseline weight not approved"
            elif not ap:
                reason = "no central approval recorded"
            elif t["execution"] != "COMPLETE":
                reason = f"task is reported {t['execution']} (reopened or unfinished); credit requires COMPLETE"
            elif has_commit_bound_evidence(t) and not any(ev.get("commit") == ap["source_commit"] for ev in t["evidence"]):
                row["acceptance"] = "STALE_APPROVAL"
                row["evidence_verified"] = False
                reason = (f"approval {ap['approval_id']} is bound to {ap['source_commit'][:7]} but the report's evidence "
                          f"is bound to a different commit; re-review required")
                warnings.append(f"{bt['id']}: {reason}")
            elif ap["acceptance"] != "PASS":
                reason = f"acceptance is {ap['acceptance']}"
            elif ap["review_status"] != "APPROVED":
                reason = f"review is {ap['review_status']}"
            elif not row["evidence_verified"]:
                reason = "no evidence bound to the approved commit with ci_run or report_sha256 and result PASS"
                warnings.append(f"{bt['id']}: PASS lacks verifiable evidence; no credit")
            elif bt.get("requires_physical") and "physical" not in {ev["type"] for ev in t["evidence"]}:
                reason = "physical gate cannot be satisfied by software or simulation evidence"
                warnings.append(f"{bt['id']}: {reason}; no credit")
            elif row["blocked_by"]:
                reason = "blocked by open gate(s): " + ", ".join(row["blocked_by"])
            if reason:
                row["credit_reason"] = reason
            else:
                row["credit"] = True
                row["credit_reason"] = (f"weight {bt['weight']} x approval {ap['approval_id']} (PASS, APPROVED) "
                                        f"on commit {ap['source_commit'][:7]} with PASS evidence")
        if not row["credit_reason"]:
            row["credit_reason"] = "unknown"
        tasks.append(row)
    weights = [r["weight"] for r in tasks]
    if not tasks or any(w is None for w in weights):
        prog = {"accepted_progress_pct": None, "basis": "no approved baseline weights"}
    else:
        total = sum(weights)
        credited = sum(r["weight"] for r in tasks if r["credit"])
        prog = {"accepted_progress_pct": round(100 * credited / total, 2) if total else None,
                "basis": f"{credited}/{total} weight (WAIVED, FAIL, stale, gated or missing earn no credit)"}
    return sorted(tasks, key=lambda r: r["task_id"]), prog, warnings


def rollup(tasks, key):
    """Group tasks by a field; accepted weight is credited weight only. Unmapped tasks are shown, not hidden."""
    groups = {}
    for t in tasks:
        k = t.get(key) or "UNMAPPED"
        g = groups.setdefault(k, {"tasks": 0, "complete": 0, "credited": 0, "weight": 0, "accepted_weight": 0,
                                  "weighted": True})
        g["tasks"] += 1
        g["complete"] += t["execution"] == "COMPLETE"
        g["credited"] += bool(t["credit"])
        if t["weight"] is None:
            g["weighted"] = False
        else:
            g["weight"] += t["weight"]
            g["accepted_weight"] += t["weight"] if t["credit"] else 0
    return {k: groups[k] for k in sorted(groups)}


def measures(tasks, gates):
    """Four SEPARATE measures. They are never blended into one percentage."""
    n = len(tasks)
    open_release = sorted(g["gate_id"] for g in gates if g["status"] == "OPEN" and "RELEASE" in g["blocking_effect"])
    return {
        "execution_complete": {"tasks_complete": sum(t["execution"] == "COMPLETE" for t in tasks), "tasks_total": n,
                               "note": "reported by repos; not acceptance"},
        "evidence_coverage": {"tasks_with_verified_evidence": sum(t["evidence_verified"] for t in tasks), "tasks_total": n},
        "release_readiness": {"state": "NOT_READY" if (open_release or any(not t["credit"] for t in tasks)) else "READY",
                              "open_release_gates": open_release,
                              "uncredited_tasks": sum(not t["credit"] for t in tasks)},
    }


def evidence_health(tasks, workstreams, warnings):
    h = []
    for t in tasks:
        if t["execution"] and not t["evidence_verified"]:
            h.append(f"{t['task_id']}: no verified evidence")
    for w in workstreams:
        if w["source_state"] in ("STALE", "INVALID"):
            h.append(f"{w['id']}: source {w['source_state']}")
    h += [x for x in warnings if "different commit" in x]
    return sorted(set(h))


def render(c):
    pct = c["progress"]["accepted_progress_pct"]
    m = c["measures"]
    L = ["<!-- GENERATED by tools/consolidate_status.py. Do not edit by hand. -->", "",
         "# Consolidated Program Status (generated)", "",
         "## Summary", "",
         f"- Baseline version: {c['baseline_version']} ({'APPROVED' if c['baseline_approved'] else 'DRAFT, not approved'})",
         f"- Accepted progress: {'N/A' if pct is None else str(pct) + '%'} ({c['progress']['basis']})",
         f"- Execution reported complete: {m['execution_complete']['tasks_complete']}/{m['execution_complete']['tasks_total']} tasks (repo-reported; not acceptance)",
         f"- Evidence coverage: {m['evidence_coverage']['tasks_with_verified_evidence']}/{m['evidence_coverage']['tasks_total']} tasks with verified evidence",
         f"- Release readiness: {m['release_readiness']['state']} (open release gates: "
         f"{', '.join(m['release_readiness']['open_release_gates']) or 'none'}; uncredited tasks: {m['release_readiness']['uncredited_tasks']})",
         "- Schedule and effort: NOT TRACKED here (separate from progress; no dates or actuals approved)",
         "", "## Workstreams", "",
         "| Workstream | Repo | Source state | Tasks reported | Commit |", "|---|---|---|---|---|"]
    for w in c["workstreams"]:
        L.append(f"| {w['id']} | {w['repo'] or 'UNVERIFIED'} | {w['source_state']} | {w['tasks_reported']} | {w['commit'][:7]} |")
    for title, key in (("Rollup by phase (P0-P8)", "by_phase"), ("Rollup by workstream", "by_workstream"),
                       ("Rollup by milestone", "by_milestone")):
        L += ["", f"## {title}", "", "| Group | Tasks | Execution complete | Credited | Weight | Accepted weight |",
              "|---|---|---|---|---|---|"]
        for k, g in c[key].items():
            L.append(f"| {k} | {g['tasks']} | {g['complete']} | {g['credited']} | "
                     f"{g['weight'] if g['weighted'] else 'N/A'} | {g['accepted_weight'] if g['weighted'] else 'N/A'} |")
    L += ["", "## Tasks", ""]
    if c["tasks"]:
        L += ["| Task | Workstream | Weight | Execution | Acceptance | Credit | Why |", "|---|---|---|---|---|---|---|"]
        for t in c["tasks"]:
            L.append(f"| {t['task_id']} | {t['workstream_id']} | {t['weight']} | {t['execution'] or '-'} | "
                     f"{t['acceptance']} | {'yes' if t['credit'] else 'no'} | {t['credit_reason']} |")
    else:
        L.append("No approved baseline tasks yet (task IDs and weights pending, see D-007).")
    L += ["", "## Gates", ""]
    if c["gates"]:
        L += ["| Gate | Status | Blocks | Scope | Owner |", "|---|---|---|---|---|"]
        for g in c["gates"]:
            sc = ", ".join(g["scope"].get("milestone_ids", []) + g["scope"].get("task_ids", []))
            L.append(f"| {g['gate_id']} | {g['status']} | {', '.join(g['blocking_effect'])} | {sc} | {g.get('owner', '-')} |")
    else:
        L.append("No gates recorded.")
    if c["evidence_health"]:
        L += ["", "## Evidence health", ""] + [f"- {x}" for x in c["evidence_health"]]
    for title, key in (("Validation errors", "errors"), ("Warnings", "warnings")):
        if c[key]:
            L += ["", f"## {title}", ""] + [f"- {x}" for x in c[key]]
    return "\n".join(L) + "\n"


# ---- append-only history -------------------------------------------------------------------------

def snapshot_hash(rec):
    return sha256_text(canonical({k: v for k, v in rec.items() if k != "snapshot_hash"}))


def list_history(hdir):
    d = hdir / "snapshots"
    return sorted(d.glob("S*.json")) if d.exists() else []


def verify_history(hdir):
    """Check the hash chain. Returns list of problems."""
    prev, probs = None, []
    for p in list_history(hdir):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("snapshot_hash") != snapshot_hash(rec):
            probs.append(f"{p.name}: snapshot_hash mismatch (edited after writing)")
        if rec.get("prev_hash") != prev:
            probs.append(f"{p.name}: prev_hash does not match previous snapshot (chain broken)")
        prev = rec.get("snapshot_hash")
    return probs


def write_history(root, c, base, cfg, meta, ok_required, reasons, now, script_path):
    """Append a snapshot (all required sources OK, no errors) or a failure record. Never overwrites."""
    hdir = root / HISTORY
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    if not ok_required:
        fdir = hdir / "failures"
        fdir.mkdir(parents=True, exist_ok=True)
        n = len(list(fdir.glob("F*.json"))) + 1
        rec = {"failure_id": f"F{n:04d}", "recorded_at": ts, "baseline_version": base["baseline_version"],
               "reasons": sorted(reasons)}
        (fdir / f"F{n:04d}.json").write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return f"failed reconciliation recorded as {rec['failure_id']} (no snapshot written)"
    prior = list_history(hdir)
    prev = json.loads(prior[-1].read_text(encoding="utf-8")) if prior else None
    body = {
        "baseline_version": base["baseline_version"], "baseline_sha256": baseline_hash(base),
        "consolidator_sha256": hashlib.sha256(Path(script_path).read_bytes()).hexdigest(),
        "schema_sha256": hashlib.sha256((root / "schema" / "status.schema.json").read_bytes()).hexdigest()
        if (root / "schema" / "status.schema.json").exists() else None,
        "sources": [{"workstream_id": w["id"], "repo": w["repo"], "report_source_commit": w["commit"],
                     "fetched_commit": meta.get(w["id"], {}).get("resolved_commit")}
                    for w in c["workstreams"] if w["id"] in {s["workstream_id"] for s in cfg["sources"]}],
        "accepted": [{"task_id": t["task_id"], "weight": t["weight"]} for t in c["tasks"] if t["credit"]],
        "gates": [{"gate_id": g["gate_id"], "status": g["status"]} for g in c["gates"]],
        "progress": c["progress"], "measures": c["measures"],
    }
    if prev and all(prev.get(k) == v for k, v in body.items()):
        return f"unchanged since {prior[-1].stem}; no snapshot written"
    seq = len(prior) + 1
    rec = {"snapshot_id": f"S{seq:04d}", "seq": seq, "recorded_at": ts,
           "prev_hash": prev["snapshot_hash"] if prev else None, **body}
    rec["snapshot_hash"] = snapshot_hash(rec)
    (hdir / "snapshots").mkdir(parents=True, exist_ok=True)
    out = hdir / "snapshots" / f"S{seq:04d}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return f"snapshot {rec['snapshot_id']} appended"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="kritva-program repo root")
    ap.add_argument("--sources-dir", help="read status JSON files from this directory instead of fetching")
    ap.add_argument("--fetch", action="store_true", help="fetch via `gh api` per sources.json (pinned commit)")
    ap.add_argument("--strict", action="store_true", help="missing/stale sources are failures")
    ap.add_argument("--check", action="store_true", help="fail if committed outputs differ; write nothing")
    ap.add_argument("--now", help="ISO time for freshness checks (default: current UTC)")
    ap.add_argument("--snapshot", action="store_true", help="append a snapshot (or failure record) under v2/history")
    ap.add_argument("--verify-history", action="store_true", help="verify the snapshot hash chain and exit")
    a = ap.parse_args()
    root = Path(a.root)
    if a.verify_history:
        probs = verify_history(root / HISTORY)
        for x in probs:
            print(f"ERROR: {x}", file=sys.stderr)
        return 5 if probs else 0
    if bool(a.sources_dir) == bool(a.fetch):
        ap.error("choose exactly one of --sources-dir or --fetch")
    if a.snapshot and a.check:
        ap.error("--snapshot and --check cannot be combined")

    reg = {w["id"]: w for w in load_json(root / TRACK / "workstreams.json")["workstreams"]}
    base = load_json(root / TRACK / "baseline.json")
    ledger = load_json(root / TRACK / "approvals.json")
    cfg = load_json(root / TRACK / "sources.json")
    now = parse_ts(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    base_tasks = {t["id"]: t for t in base["tasks"]}
    if len(base_tasks) != len(base["tasks"]):
        raise SystemExit("config/IO error: duplicate task ids in baseline.json")

    meta = {}
    if a.fetch:
        found, fetch_problems, meta = fetch_sources(cfg)
    else:
        found, fetch_problems = read_dir(a.sources_dir), []
    errors, warnings, stale_or_missing = [], list(fetch_problems), bool(fetch_problems)
    if not base_tasks:
        warnings.append("baseline has no tasks: task IDs in reports are unvalidated and progress is N/A")

    authorized = set(ledger.get("authorized_approvers", []))
    errors += [f"baseline.json: {x}" for x in validate_baseline(base, authorized, root)]
    aerrs, effective = validate_approvals(ledger, base_tasks, base["baseline_version"])
    errors += [f"approvals.json: {x}" for x in aerrs]

    reports, out_ws, claimed = {}, [], {}
    for ws_id in sorted(reg):
        w = reg[ws_id]
        if w.get("closed_release") and not w.get("closed_ids"):
            warnings.append(f"{ws_id}: closed-release guard inactive ({w['closed_release']} task ID UNVERIFIED)")
        for cid in w.get("closed_ids", []):
            if not any(b.get("milestone_id") == cid and b["workstream_id"] == ws_id for b in base["tasks"]):
                warnings.append(f"{ws_id}: closed-milestone guard for {cid} inactive (no baseline tasks seeded)")
        entry = {"id": ws_id, "repo": w.get("repo"), "source_state": "UNVERIFIED", "commit": "-" * 7, "tasks_reported": 0}
        if ws_id in found:
            origin, doc = found[ws_id]
            errs = validate_report(doc, reg, base_tasks)
            if errs:
                errors += [f"{origin}: {x}" for x in errs]
                entry["source_state"] = "INVALID"
            else:
                age = (now - parse_ts(doc["updated_at"])).days
                entry.update(repo=doc["repo"], commit=doc["source"]["commit"], tasks_reported=len(doc["tasks"]))
                if age > cfg.get("freshness_days", 14):
                    entry["source_state"] = "STALE"
                    warnings.append(f"{ws_id}: status is {age} days old")
                    stale_or_missing = True
                else:
                    entry["source_state"] = "OK"
                    reports[ws_id] = (origin, doc)
                for t in doc["tasks"]:
                    if t["task_id"] in claimed:
                        errors.append(f"{origin}: task {t['task_id']} also reported by {claimed[t['task_id']]}")
                    claimed[t["task_id"]] = ws_id
        else:
            warnings.append(f"{ws_id}: no status source (UNVERIFIED)")
            stale_or_missing = True
        out_ws.append(entry)
    errors += [f"source for unknown workstream {u!r}" for u in sorted(set(found) - set(reg))]

    tasks, prog, cwarn = compute(base, reports, effective, reg)
    warnings += cwarn
    gates = base.get("gates", [])
    c = {"baseline_version": base["baseline_version"], "baseline_approved": bool(base.get("baseline_approved")),
         "progress": prog, "measures": measures(tasks, gates), "workstreams": out_ws, "tasks": tasks,
         "by_phase": rollup(tasks, "phase"), "by_workstream": rollup(tasks, "workstream_id"),
         "by_milestone": rollup(tasks, "milestone_id"), "gates": gates,
         "evidence_health": evidence_health(tasks, out_ws, warnings),
         "errors": sorted(errors), "warnings": sorted(warnings)}
    targets = {root / TRACK / "consolidated_status.json": json.dumps(c, indent=2, sort_keys=True) + "\n",
               root / TRACK / "STATUS_VIEW.md": render(c)}

    if a.check:
        drift = [str(p) for p, txt in targets.items() if not p.exists() or p.read_text(encoding="utf-8") != txt]
        if drift:
            print("generated output out of date: " + ", ".join(drift), file=sys.stderr)
            return 4
    else:
        for p, txt in targets.items():
            p.write_text(txt, encoding="utf-8")
    for x in c["errors"]:
        print(f"ERROR: {x}", file=sys.stderr)
    for x in c["warnings"]:
        print(f"WARN: {x}", file=sys.stderr)
    if a.snapshot:
        required = {s["workstream_id"] for s in cfg["sources"]}
        not_ok = sorted(w["id"] for w in out_ws if w["id"] in required and w["source_state"] != "OK")
        reasons = errors + [f"required source {x} not OK" for x in not_ok] + list(fetch_problems)
        print("HISTORY: " + write_history(root, c, base, cfg, meta, not (errors or not_ok), reasons, now, __file__),
              file=sys.stderr)
    if errors:
        return 1
    return 3 if (a.strict and stale_or_missing) else 0


if __name__ == "__main__":
    sys.exit(main())
