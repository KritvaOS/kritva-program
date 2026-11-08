#!/usr/bin/env python3
"""Publish each capability repository's slice of the program status as a pinned snapshot (D-120).

  publish_repo_progress.py                      dry run: print one summary line per repository
  publish_repo_progress.py --repos-root DIR     [--only FOLDER] write into DIR/<repo>/ : status/program_snapshot.json,
                                                status/STATUS.md, scripts/progress_report.py and
                                                .github/workflows/progress-check.yml

Numbers come from v2/tracking/consolidated_status.json through the same helpers that draw the
repository table in STATUS_VIEW.md (tools/dashboard.py), so a repository's bar can never disagree with
the program view it was taken from. Nothing here feeds credit, the baseline or approvals. The files
written into a repository are a derived snapshot: they change only through a pull request there.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dashboard as _db  # noqa: E402

TEMPLATES = Path(__file__).resolve().parent / "repo-templates"
VIEW = "https://github.com/KritvaOS/kritva-program/blob/main/v2/tracking/STATUS_VIEW.md"
# program repository key -> (GitHub repository, folder name, workstream id in by_workstream)
REPOS = {
    "Core": ("KritvaOS/kritva-core", "kritva-core", "CORE"),
    "Community": ("KritvaOS/kritvaos-community", "kritvaos-community", "COMMUNITY"),
    "Sense": ("KritvaOS/kritva-sense", "kritva-sense", "SENSE"),
    "Mind": ("KritvaOS/kritva-mind", "kritva-mind", "MIND"),
    "Motion": ("KritvaOS/kritva-motion", "kritva-motion", "MOTION"),
    "Skill": ("KritvaOS/kritva-skill", "kritva-skill", "SKILL"),
}
_NOTE_KEY = {"Core": r"CORE", "Community": r"COMMUNITY|KOS-I\d", "Sense": r"SENSE", "Mind": r"MIND",
             "Motion": r"MOTION", "Skill": r"SKILL", "Program": r"KRP"}


def _titles(c):
    return {f"M{i}": name.title() if name.isupper() else name
            for i, (_p, name) in enumerate(c.get("phase_sequence") or [])}


def _notes(c, key):
    rx = re.compile(_NOTE_KEY[key])
    return [x for x in c.get("evidence_health") or [] if rx.search(x.split(":", 1)[0])]


def _milestone_of(t):
    m = re.match(r"^V2-(M\d+)-", t.get("milestone_id") or "")
    return m.group(1) if m else "Foundation"


def _tasks(c, key, ws):
    """Task rows for one repository: baselined tasks (with their execution state and credit) and planned, not yet baselined."""
    out = []
    for t in c.get("tasks") or []:
        if ws and t.get("workstream_id") == ws:
            out.append({"id": t["task_id"], "title": t.get("title") or "", "weight": t["weight"], "milestone": _milestone_of(t),
                        "kind": "baselined", "execution": t.get("execution") or "NOT_REPORTED", "accepted": bool(t.get("credit"))})
    for t in c["plan_register"].get("tasks") or []:
        if t.get("repo") == key:
            out.append({"id": t["id"], "title": t.get("title") or "", "weight": t["weight"], "milestone": t["milestone"],
                        "kind": "planned", "execution": t.get("status") or "NOT_STARTED", "accepted": False})
    return out


def build(c, key):
    """One repository's snapshot. Raises ValueError when the program data it needs is missing."""
    reg = c.get("plan_register")
    if not reg or key not in reg["by_repo"]:
        raise ValueError(f"the plan register has no repository {key!r}")
    v = reg["by_repo"][key]
    f = _db._foundation_by_repo(c).get(key, [0, 0, 0, 0])
    ws = REPOS.get(key, (None, None, None))[2]
    w = (c.get("by_workstream") or {}).get(ws, {}) if ws else {}
    ms = {m: {"accepted": x["accepted"], "baseline": x["baseline"], "point": x["point"], "rows": x["rows"]}
          for m, x in (reg.get("matrix") or {}).get(key, {}).items()}
    return {
        "schema_version": 2,
        "repo": key,
        "repository": REPOS[key][0] if key in REPOS else None,
        "program": {"baseline_version": c["baseline_version"], "baseline_approved": bool(c["baseline_approved"]),
                    "generated_at": c["generated_at"], "view": VIEW,
                    "release_state": (c.get("measures") or {}).get("release_readiness", {}).get("state", "UNKNOWN")},
        "foundation": {"accepted_weight": f[0], "weight": f[1], "accepted_tasks": f[2], "tasks": f[3]},
        "baseline_tasks": {"accepted_tasks": v.get("accepted_tasks", 0), "baseline_tasks": v.get("baseline_tasks", 0), "rows": v["rows"]},
        "milestones": ms,
        "titles": _titles(c),
        "execution": {"complete": w.get("complete", 0), "tasks": w.get("tasks", 0)},
        "evidence_notes": _notes(c, key),
        "tasks": _tasks(c, key, ws),
    }


def build_all(c):
    return {k: build(c, k) for k in (c.get("plan_register") or {}).get("by_repo", {})}


def summary(snaps):
    """Per repository: accepted weight, total weight, as the repository table in STATUS_VIEW.md computes them."""
    out = {}
    for k, s in snaps.items():
        ms = s["milestones"]
        acc = s["foundation"]["accepted_weight"] + sum(x["accepted"] for x in ms.values())
        tot = s["foundation"]["weight"] + sum(x["baseline"] + x["point"] for x in ms.values())
        out[k] = (acc, tot)
    return out


def write(snaps, repos_root, template_dir=TEMPLATES, only=None):
    import importlib.util
    spec = importlib.util.spec_from_file_location("progress_report", template_dir / "progress_report.py")
    pr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pr)
    done = []
    for k, (_repo, folder, _ws) in REPOS.items():
        if only and folder not in only:
            continue
        root = Path(repos_root) / folder
        if not root.is_dir():
            raise SystemExit(f"publish_repo_progress: {root} is not a directory")
        snap = snaps[k]
        problems = pr.validate(snap)
        if problems:
            raise SystemExit(f"publish_repo_progress: {k}: " + "; ".join(problems))
        (root / "status").mkdir(exist_ok=True)
        (root / "scripts").mkdir(exist_ok=True)
        (root / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
        (root / "status" / "program_snapshot.json").write_text(json.dumps(snap, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root / "status" / "STATUS.md").write_text(pr.render(snap), encoding="utf-8")
        shutil.copyfile(template_dir / "progress_report.py", root / "scripts" / "progress_report.py")
        (root / "scripts" / "progress_report.py").chmod(0o755)
        shutil.copyfile(template_dir / "progress-check.yml", root / ".github" / "workflows" / "progress-check.yml")
        done.append(folder)
    return done


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="kritva-program checkout")
    ap.add_argument("--repos-root", help="folder that holds the repository checkouts; omit for a dry run")
    ap.add_argument("--only", action="append", metavar="FOLDER", help="write only this repository folder (repeatable)")
    a = ap.parse_args(argv)
    c = json.loads((Path(a.root) / "v2/tracking/consolidated_status.json").read_text(encoding="utf-8"))
    snaps = build_all(c)
    for k, (acc, tot) in summary(snaps).items():
        print(f"{k:10s} {acc:g} / {tot:g} weight")
    if a.repos_root:
        for folder in write(snaps, a.repos_root, only=a.only):
            print(f"wrote {folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
