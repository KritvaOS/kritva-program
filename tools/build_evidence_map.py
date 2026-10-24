#!/usr/bin/env python3
"""Build a PROPOSED per-task evidence map from resolver candidates and explicit human choices.

  python3 tools/build_evidence_map.py --choices v2/tracking/evidence_choices.json \\
      --candidates COMMUNITY=community_candidates.json --candidates CORE=core_candidates.json \\
      --baseline v2/tracking/baseline.json --out v2/tracking/evidence_map_proposal.json

The choices file says, per workstream, which evidence mode each task uses:
  OWN        the task's own commit has a successful run of the named workflow (checked against candidates)
  RERUN      a re-run of a run on the task's own commit (run id supplied by the owner, checked for commit only)
  MILESTONE  one later commit with a passing run vouches for the tree as of that commit ("accepted as of X").
             Needs --against <that commit> in the resolver output: the commit must descend from the task
             commit and must not have deleted the task's files.
Nothing is guessed: a task without a valid choice is listed under "unmapped" and keeps zero credit.
This file is a PROPOSAL. It grants no credit. Credit needs the repo's status.json to cite the same
commit and run, plus a central PASS approval for that commit. Stdlib only. Exit 0 ok, 1 problems found, 2 usage/IO.
"""
import argparse
import json
import sys
from pathlib import Path


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def pick_item(items, commit):
    for i in items:
        if i["full"].startswith(commit):
            return i
    return None


def build(choices, cands, base):
    rows, unmapped, problems = [], [], []
    for bt in base["tasks"]:
        tid, ws = bt["id"], bt["workstream_id"]
        ch = choices.get(ws)
        if ch is None:
            unmapped.append({"task_id": tid, "reason": f"no choices for workstream {ws}"}); continue
        c = dict(ch.get("default") or {})
        c.update((ch.get("tasks") or {}).get(tid, {}))
        items = (cands.get(ws) or {}).get("tasks", {}).get(tid, [])
        if not c or not items:
            unmapped.append({"task_id": tid, "reason": "no choice" if not c else "no resolved task commit"}); continue
        # the commit that finished the task (needed when several commits mention it)
        tc = c.get("task_commit") or (items[0]["full"] if len(items) == 1 else None)
        item = pick_item(items, tc) if tc else None
        if item is None:
            unmapped.append({"task_id": tid, "reason": "several candidate commits; set task_commit in choices",
                             "candidates": [i["full"] for i in items]}); continue
        mode, flags, run, commit = c.get("mode"), [], None, None
        if mode == "OWN":
            wf = c.get("workflow")
            ok = [r for r in item.get("ci_runs") or [] if r.get("workflowName") == wf and r.get("conclusion") == "success"
                  and r.get("headSha") == item["full"]]
            if not ok:
                unmapped.append({"task_id": tid, "reason": f"no successful {wf!r} run on the task commit"}); continue
            run, commit = ok[0], item["full"]
        elif mode == "RERUN":
            run, commit = {"databaseId": c["ci_run"], "url": c.get("url"), "workflowName": c.get("workflow")}, item["full"]
            flags.append("RERUN_ATTEMPT_REPORTED_BY_OWNER_NOT_CHECKED")
        elif mode == "MILESTONE":
            commit = c["commit"]
            rel = (item.get("against") or {}).get(commit)
            if rel is None:
                unmapped.append({"task_id": tid, "reason": "resolver was not run with --against " + commit}); continue
            if rel["state"] != "DESCENDANT":
                unmapped.append({"task_id": tid, "reason": f"evidence commit is {rel['state']}"}); continue
            if rel["task_files_deleted"]:
                unmapped.append({"task_id": tid, "reason": "evidence commit deleted task files",
                                 "files": rel["task_files_deleted"]}); continue
            run = {"databaseId": c["ci_run"], "url": c.get("url"), "workflowName": c.get("workflow")}
            if rel["task_files_changed"]:
                flags.append("TASK_FILES_CHANGED_AFTER_TASK_COMMIT")  # expected for docs refined later; tree at evidence commit was tested
            flags.append("MILESTONE_LEVEL_ACCEPTED_AS_OF_COMMIT")
        else:
            problems.append(f"{tid}: unknown mode {mode!r}"); continue
        rows.append({"task_id": tid, "workstream_id": ws, "task_commit": item["full"], "task_subject": item["subject"],
                     "mode": mode,
                     "evidence": {"commit": commit, "ci_run": run["databaseId"], "result": "PASS",
                                  "kind": "CI_RUN", "url": run.get("url"), "workflow": run.get("workflowName")},
                     "task_files_changed_after": (item.get("against") or {}).get(commit, {}).get("task_files_changed"),
                     "review_flags": flags})
    return {"_note": "PROPOSAL ONLY. Grants no credit. Approval is Dinesh's decision in approvals.json.",
            "rows": rows, "unmapped": unmapped}, problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--choices", required=True)
    ap.add_argument("--candidates", action="append", required=True, metavar="WS=FILE")
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        cands = {}
        for spec in a.candidates:
            ws, _, f = spec.partition("=")
            cands[ws] = load(f)
        doc, problems = build(load(a.choices), cands, load(a.baseline))
    except (OSError, ValueError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    text = json.dumps(doc, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    print(f"{len(doc['rows'])} tasks mapped, {len(doc['unmapped'])} unmapped"
          + (f"; {len(problems)} problems" if problems else ""), file=sys.stderr)
    for u in doc["unmapped"]:
        print(f"  unmapped {u['task_id']}: {u['reason']}", file=sys.stderr)
    for p in problems:
        print("  PROBLEM", p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
