#!/usr/bin/env python3
"""Validate v2/tracking/planning_inventory.json (decisions D-024, D-025). Stdlib only; read-only.

Rules (registration is not credit):
  * schema: required fields and allowed values on the file, every group and every task;
  * every group and every task is PLANNING_ONLY and credit_eligible is false (task-level too);
  * a REGISTERED group names a workstream_id that exists in workstreams.json; a PROPOSED group has
    workstream_id null, a source_workstream_label and proposed_program_workstreams that all exist in workstreams.json;
  * repository names are exact (KritvaOS/<repo>); every group and task traces to a pinned source:
    repo, 40-hex commit, path and 64-hex sha256;
  * no inventory task has a weight, an approval, or a baseline entry under any ID or alias;
  * (repository, workstream_id, task_id) is unique and task_id is unique overall; a legacy alias never collides
    with a canonical ID; one alias may map to several tasks only when every mapping is alias_kind=split;
  * capability mappings (D-030): a task may list `capabilities`; each must be a workstream with kind CAPABILITY and effort_owner false, and the
    group's own workstream must be an execution workstream. A mapping never creates a second task, estimate or credit (task identity stays unique);
  * optional --verify-sources DIR: every task_id must appear in the pinned source file found under DIR (sha256 must match).
Exit 0 ok | 1 problems | 2 usage/IO.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REPO = re.compile(r"^KritvaOS/[A-Za-z0-9._-]+$")
MAPPING = {"REGISTERED", "PROPOSED"}
ALIAS_KINDS = {"rename", "split"}
# recorded_status is a verbatim snapshot of the source file's own label (RaaS uses Accepted / In Review); it is never a program status.
STATUS = {"NOT_RECORDED", "NOT_STARTED", "IN_PROGRESS", "COMPLETE", "BLOCKED", "Accepted", "In Review"}
GROUP_REQUIRED = ("repository", "workstream_id", "mapping_status", "classification", "credit_eligible", "source", "tasks")
TASK_REQUIRED = ("task_id", "title", "recorded_status", "status_authority")


def _source_problems(src, where):
    out = []
    if not isinstance(src, dict):
        return [f"{where}: source must be an object with repo, commit, path, sha256"]
    if not (isinstance(src.get("repo"), str) and REPO.match(src["repo"])):
        out.append(f"{where}: source.repo must look like KritvaOS/<repo>")
    if not (isinstance(src.get("commit"), str) and HEX40.match(src["commit"])):
        out.append(f"{where}: source.commit must be a 40-hex commit")
    if not src.get("path") or not isinstance(src.get("path"), str):
        out.append(f"{where}: source.path is required")
    if not (isinstance(src.get("sha256"), str) and HEX64.match(src["sha256"])):
        out.append(f"{where}: source.sha256 must be 64-hex")
    return out


def check(inv, baseline, approvals, workstreams, sources_dir=None):
    problems = []
    base_ids = {t["id"] for t in baseline.get("tasks", [])}
    approved_ids = {a.get("task_id") for a in approvals.get("approvals", [])}
    ws_ids = {w["id"] for w in workstreams.get("workstreams", [])}
    ws_by = {w["id"]: w for w in workstreams.get("workstreams", [])}
    capability_ids = {i for i, w in ws_by.items() if w.get("kind") == "CAPABILITY"}
    if not isinstance(inv, dict) or not isinstance(inv.get("groups"), list) or not inv["groups"]:
        return ["inventory must be an object with a non-empty groups list"]
    if inv.get("classification") != "PLANNING_ONLY":
        problems.append("top-level classification must be PLANNING_ONLY")
    if not isinstance(inv.get("inventory_version"), int):
        problems.append("inventory_version must be an integer")
    seen, canon, aliases, tids = set(), set(), {}, set()
    for g in inv["groups"]:
        repo = g.get("repository")
        gname = f"{repo}"
        for f in GROUP_REQUIRED:
            if f not in g:
                problems.append(f"group {gname}: missing field {f}")
        if not (isinstance(repo, str) and REPO.match(repo)):
            problems.append(f"group {gname}: repository must look like KritvaOS/<repo>")
        if g.get("classification") != "PLANNING_ONLY":
            problems.append(f"group {gname}: classification must be PLANNING_ONLY")
        if g.get("credit_eligible") is not False:
            problems.append(f"group {gname}: credit_eligible must be false")
        ms, wid = g.get("mapping_status"), g.get("workstream_id")
        if ms not in MAPPING:
            problems.append(f"group {gname}: mapping_status must be one of {sorted(MAPPING)}")
        elif ms == "REGISTERED":
            if wid not in ws_ids:
                problems.append(f"group {gname}: REGISTERED workstream_id {wid!r} is not in workstreams.json")
        else:
            if wid is not None:
                problems.append(f"group {gname}: PROPOSED group must have workstream_id null")
            if not g.get("source_workstream_label"):
                problems.append(f"group {gname}: PROPOSED group needs source_workstream_label")
            prop = g.get("proposed_program_workstreams")
            if not isinstance(prop, list) or not prop:
                problems.append(f"group {gname}: PROPOSED group needs proposed_program_workstreams")
            else:
                for w in prop:
                    if w not in ws_ids:
                        problems.append(f"group {gname}: proposed workstream {w!r} is not in workstreams.json")
        if wid in capability_ids:
            problems.append(f"group {gname}: execution owner {wid!r} is a CAPABILITY; capabilities cannot own tasks (D-030)")
        problems += _source_problems(g.get("source"), f"group {gname}")
        if not isinstance(g.get("tasks"), list) or not g.get("tasks"):
            problems.append(f"group {gname}: tasks must be a non-empty list")
            continue
        src_text = None
        if sources_dir and isinstance(g.get("source"), dict) and g["source"].get("path"):
            sp = Path(sources_dir) / g["source"].get("repo", "").replace("/", "__") / g["source"]["path"]
            if sp.is_file():
                raw = sp.read_bytes()
                if hashlib.sha256(raw).hexdigest() != g["source"].get("sha256"):
                    problems.append(f"group {gname}: pinned source sha256 does not match {sp}")
                src_text = raw.decode("utf-8", "replace")
            else:
                problems.append(f"group {gname}: pinned source file not found for verification: {sp}")
        for t in g["tasks"]:
            tid = t.get("task_id")
            for f in TASK_REQUIRED:
                if not t.get(f):
                    problems.append(f"{tid or '?'}: missing field {f}")
            key = (repo, wid, tid)
            if key in seen:
                problems.append(f"{tid}: duplicate in {gname}")
            if tid in tids:
                problems.append(f"{tid}: task_id is used more than once across the inventory")
            seen.add(key)
            tids.add(tid)
            canon.add(tid)
            if t.get("recorded_status") not in STATUS:
                problems.append(f"{tid}: recorded_status must be one of {sorted(STATUS)}")
            if t.get("legacy_alias"):
                if t.get("alias_kind") not in ALIAS_KINDS:
                    problems.append(f"{tid}: alias_kind must be rename or split when legacy_alias is set")
                aliases.setdefault(t["legacy_alias"], []).append((tid, t.get("alias_kind")))
            elif t.get("alias_kind"):
                problems.append(f"{tid}: alias_kind set without legacy_alias")
            caps = t.get("capabilities", [])
            if not isinstance(caps, list) or len(set(caps)) != len(caps):
                problems.append(f"{tid}: capabilities must be a list without duplicates")
            else:
                for c in caps:
                    if c not in capability_ids:
                        problems.append(f"{tid}: capability {c!r} is not a CAPABILITY in workstreams.json")
                    elif ws_by[c].get("effort_owner") is not False:
                        problems.append(f"{tid}: capability {c!r} must have effort_owner false")
            if "weight" in t:
                problems.append(f"{tid}: inventory tasks must not carry a weight")
            if "credit_eligible" in t and t["credit_eligible"] is not False:
                problems.append(f"{tid}: credit_eligible must be false")
            if "classification" in t and t["classification"] != "PLANNING_ONLY":
                problems.append(f"{tid}: classification must be PLANNING_ONLY")
            for ident in (tid, t.get("legacy_alias")):
                if ident and ident in base_ids:
                    problems.append(f"{tid}: {ident} is a baseline task; remove it from the inventory")
                if ident and ident in approved_ids:
                    problems.append(f"{tid}: {ident} has an approval record; inventory entries cannot be approved")
            if src_text is not None and tid and tid not in src_text:
                problems.append(f"{tid}: not found in pinned source {g['source'].get('path')}")
    for al, owners in aliases.items():
        if al in canon:
            problems.append(f"alias {al} collides with a canonical task ID")
        if len(owners) > 1 and any(kind != "split" for _, kind in owners):
            problems.append(f"alias {al} maps to more than one task without alias_kind=split: {[o for o, _ in owners]}")
    return problems


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    sources_dir = None
    if "--verify-sources" in argv:
        i = argv.index("--verify-sources")
        sources_dir = argv[i + 1]
        args = [a for a in args if a != sources_dir]
    root = Path(args[0] if args else ".")
    t = root / "v2/tracking"
    try:
        load = lambda n: json.loads((t / n).read_text(encoding="utf-8"))
        problems = check(load("planning_inventory.json"), load("baseline.json"),
                         load("approvals.json"), load("workstreams.json"), sources_dir)
    except (OSError, ValueError, KeyError, IndexError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    for p in problems:
        print(f"PROBLEM: {p}", file=sys.stderr)
    print("planning inventory ok" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
