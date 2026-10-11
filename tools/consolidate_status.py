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

Exit codes: 0 ok | 1 validation errors | 2 config/IO error |
            3 stale/missing sources (--strict) | 4 --check drift
Stdlib only. Never commits, pushes, or handles tokens.
"""
import argparse
import base64
import datetime as dt
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


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f"config/IO error: {path}: {e}") from None


def parse_ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def fetch_sources(cfg):
    found, problems = {}, []
    for s in cfg["sources"]:
        api = f"repos/{s['repo']}/contents/{cfg['status_path']}?ref={s['ref']}"
        r = subprocess.run(["gh", "api", api], capture_output=True, text=True)
        if r.returncode != 0:
            problems.append(f"{s['workstream_id']}: fetch failed for {s['repo']}@{s['ref']} (UNVERIFIED)")
            continue
        try:
            found[s["workstream_id"]] = (api, json.loads(base64.b64decode(json.loads(r.stdout)["content"])))
        except (KeyError, ValueError) as e:
            problems.append(f"{s['workstream_id']}: unparseable status file ({e})")
    return found, problems


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


def compute(base, reports, effective, reg):
    """Per-task rows and accepted progress. Missing reports and stale approvals earn nothing."""
    tasks, warnings = [], []
    task_state = {}
    for ws_id, (_, doc) in reports.items():
        for t in doc["tasks"]:
            task_state[t["task_id"]] = (doc, t)
    credited = 0
    for bt in base["tasks"]:
        row = {"task_id": bt["id"], "workstream_id": bt["workstream_id"], "weight": bt.get("weight"),
               "execution": None, "git_sync": None, "readiness": None, "acceptance": "NOT_RUN", "credit": False}
        st = task_state.get(bt["id"])
        ap = effective.get(bt["id"])
        if st:
            doc, t = st
            row.update(execution=t["execution"], git_sync=t["git_sync"], readiness=t["readiness"])
            if ap:
                row["acceptance"] = ap["acceptance"]
                if ap["source_commit"] != doc["source"]["commit"]:
                    row["acceptance"] = "STALE_APPROVAL"
                    warnings.append(f"{bt['id']}: approval {ap['approval_id']} is for an older commit; re-review required")
                elif ap["acceptance"] == "PASS":
                    types = {ev["type"] for ev in t["evidence"]}
                    verifiable = [ev for ev in t["evidence"] if ev.get("commit") == ap["source_commit"]
                                  and (ev.get("ci_run") or ev.get("report_sha256"))
                                  and str(ev.get("result") or "").upper() == "PASS"]
                    if not verifiable:
                        warnings.append(f"{bt['id']}: PASS lacks evidence bound to the approved commit with ci_run or report_sha256 and result PASS; no credit")
                    elif bt.get("requires_physical") and "physical" not in types:
                        warnings.append(f"{bt['id']}: physical gate cannot be satisfied by {sorted(types)} evidence; no credit")
                    else:
                        row["credit"] = True
        else:
            warnings.append(f"{bt['id']}: not reported by {bt['workstream_id']} (no credit)")
        tasks.append(row)
    weights = [r["weight"] for r in tasks]
    if not tasks or any(w is None for w in weights):
        prog = {"accepted_progress_pct": None, "basis": "no approved baseline weights"}
    else:
        total = sum(weights)
        credited = sum(r["weight"] for r in tasks if r["credit"])
        prog = {"accepted_progress_pct": round(100 * credited / total, 2) if total else None,
                "basis": f"{credited}/{total} weight (WAIVED, FAIL, stale or missing earn no credit)"}
    return sorted(tasks, key=lambda r: r["task_id"]), prog, warnings


def render(c):
    pct = c["progress"]["accepted_progress_pct"]
    L = ["<!-- GENERATED by tools/consolidate_status.py. Do not edit by hand. -->", "",
         "# Consolidated Program Status (generated)", "",
         f"Baseline version: {c['baseline_version']} | Accepted progress: {'N/A' if pct is None else str(pct) + '%'} "
         f"({c['progress']['basis']})", "",
         "## Workstreams", "",
         "| Workstream | Repo | Source state | Tasks reported | Commit |", "|---|---|---|---|---|"]
    for w in c["workstreams"]:
        L.append(f"| {w['id']} | {w['repo'] or 'UNVERIFIED'} | {w['source_state']} | {w['tasks_reported']} | {w['commit'][:7]} |")
    L += ["", "## Tasks", ""]
    if c["tasks"]:
        L += ["| Task | Workstream | Weight | Execution | Git sync | Readiness | Acceptance | Credit |", "|---|---|---|---|---|---|---|---|"]
        for t in c["tasks"]:
            L.append(f"| {t['task_id']} | {t['workstream_id']} | {t['weight']} | {t['execution'] or '-'} | {t['git_sync'] or '-'} | "
                     f"{t['readiness'] or '-'} | {t['acceptance']} | {'yes' if t['credit'] else 'no'} |")
    else:
        L.append("No approved baseline tasks yet (task IDs and weights pending, see D-007).")
    if c["open_gates"]:
        L += ["", "## Open gates (from baseline)", ""] + [f"- {x}" for x in c["open_gates"]]
    for title, key in (("Validation errors", "errors"), ("Warnings", "warnings")):
        if c[key]:
            L += ["", f"## {title}", ""] + [f"- {x}" for x in c[key]]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="kritva-program repo root")
    ap.add_argument("--sources-dir", help="read status JSON files from this directory instead of fetching")
    ap.add_argument("--fetch", action="store_true", help="fetch via `gh api` per sources.json")
    ap.add_argument("--strict", action="store_true", help="missing/stale sources are failures")
    ap.add_argument("--check", action="store_true", help="fail if committed outputs differ; write nothing")
    ap.add_argument("--now", help="ISO time for freshness checks (default: current UTC)")
    a = ap.parse_args()
    if bool(a.sources_dir) == bool(a.fetch):
        ap.error("choose exactly one of --sources-dir or --fetch")

    root = Path(a.root)
    reg = {w["id"]: w for w in load_json(root / TRACK / "workstreams.json")["workstreams"]}
    base = load_json(root / TRACK / "baseline.json")
    ledger = load_json(root / TRACK / "approvals.json")
    cfg = load_json(root / TRACK / "sources.json")
    now = parse_ts(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    base_tasks = {t["id"]: t for t in base["tasks"]}
    if len(base_tasks) != len(base["tasks"]):
        raise SystemExit("config/IO error: duplicate task ids in baseline.json")

    found, fetch_problems = fetch_sources(cfg) if a.fetch else (read_dir(a.sources_dir), [])
    errors, warnings, stale_or_missing = [], list(fetch_problems), bool(fetch_problems)
    if not base_tasks:
        warnings.append("baseline has no tasks: task IDs in reports are unvalidated and progress is N/A")

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
    c = {"baseline_version": base["baseline_version"], "progress": prog, "workstreams": out_ws, "tasks": tasks,
         "open_gates": sorted(f"{m['id']}: {g}" for m in base["milestones"] for g in m.get("open_gates", [])),
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
    if errors:
        return 1
    return 3 if (a.strict and stale_or_missing) else 0


if __name__ == "__main__":
    sys.exit(main())
