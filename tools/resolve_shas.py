#!/usr/bin/env python3
"""Resolve the short SHAs in an engineering repo's planning records to full commits (evidence candidates).

Run it LOCALLY inside (or pointing at) a checkout, where git has the history:
  python3 tools/resolve_shas.py --repo ~/workarea/kritvaOS/kritvaos-community --out community_candidates.json
  python3 tools/resolve_shas.py --repo ~/workarea/kritvaOS/kritva-core --tag kritva-core-r1.0 --ci \\
      --out core_candidates.json

For every Markdown line under planning/ that names EXACTLY ONE task ID and quotes a short SHA in backticks or
parentheses, it records: the full 40-hex commit (git rev-parse), whether it is an ancestor of origin/main,
and the commit subject. Lines naming several tasks or a range are not attributed to any task; their commits
are listed separately under milestone_level_commits. Tags are peeled to the commit they point at. With --ci it also lists workflow runs
for each commit (needs the `gh` CLI; never required).

This only produces CANDIDATES. A planning note that quotes a SHA is not evidence: a candidate becomes
evidence only when it has a passing CI run or retained report for that exact commit, the task's criteria
mapping is reviewed, and the owner approves it in approvals.json. Unresolvable or ambiguous SHAs are listed
so the tasks stay at zero credit rather than being guessed.
Stdlib only. Read-only on the repo. Exit 0 always unless the repo is unusable (2).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TASK = re.compile(r"(KF-CORE-R\d+-[A-Z0-9-]*\d{3}|\bI\d-\d{3}\b)")
SHORT = re.compile(r"(?<![0-9a-zA-Z])([0-9a-f]{7,12})(?![0-9a-zA-Z])")


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return (r.returncode, r.stdout.strip(), r.stderr.strip())


def resolve(repo, short):
    rc, out, err = git(repo, "rev-parse", "--verify", "--quiet", f"{short}^{{commit}}")
    if rc == 0 and re.fullmatch(r"[0-9a-f]{40}", out):
        return "OK", out
    return ("AMBIGUOUS" if "ambiguous" in err.lower() else "UNRESOLVED"), None


def is_ancestor(repo, full):
    rc, _, _ = git(repo, "merge-base", "--is-ancestor", full, "origin/main")
    return rc == 0


def subject(repo, full):
    return git(repo, "log", "-1", "--format=%s", full)[1]


def ci_runs(full, slug):
    try:
        r = subprocess.run(["gh", "run", "list", "--commit", full, "--limit", "20", "--json",
                            "databaseId,workflowName,conclusion,status,url"] + (["--repo", slug] if slug else []),
                           capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    return json.loads(r.stdout or "[]")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--planning", default="planning", help="folder under the repo to scan")
    ap.add_argument("--tag", action="append", default=[], help="tag to peel to its commit (repeatable)")
    ap.add_argument("--slug", help="owner/name for gh (default: gh infers from the checkout)")
    ap.add_argument("--ci", action="store_true", help="also list CI runs per commit (needs gh)")
    ap.add_argument("--out", help="write JSON here (default: stdout)")
    a = ap.parse_args()
    repo = Path(a.repo).expanduser()
    rc, head, _ = git(repo, "rev-parse", "HEAD")
    if rc != 0:
        print(f"ERROR: {repo} is not a usable git checkout", file=sys.stderr)
        return 2
    tasks, unresolved, seen, milestone_level = {}, [], {}, {}
    for md in sorted((repo / a.planning).rglob("*.md")):
        for n, line in enumerate(md.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            ids = set(TASK.findall(line))
            if not ids:
                continue
            for short in set(SHORT.findall(line)):
                quoted = f"`{short}`" in line or f"({short}" in line or f"`{short}" in line
                if not quoted and not (re.search(r"[0-9]", short) and re.search(r"[a-f]", short)):
                    continue  # skip plain numbers / words that merely look like hex unless quoted
                state, full = seen.setdefault(short, resolve(repo, short))
                loc = f"{md.relative_to(repo)}:{n}"
                if len(ids) != 1 or re.search(r"\bI\d-\d{3}\.\.|R\d+-\d{3}\.\.", line):
                    # a line naming several tasks (or a range) cannot attribute a commit to one task
                    if state == "OK":
                        milestone_level.setdefault(full, {"short": short, "subject": subject(repo, full),
                                                          "sources": []})["sources"].append(loc)
                    continue
                for tid in sorted(ids):
                    if state == "OK":
                        tasks.setdefault(tid, []).append({
                            "short": short, "full": full, "source": loc, "subject": subject(repo, full),
                            "ancestor_of_origin_main": is_ancestor(repo, full)})
                    else:
                        unresolved.append({"task": tid, "short": short, "state": state, "source": loc})
    for tid, items in tasks.items():
        uniq = {i["full"]: i for i in items}
        tasks[tid] = list(uniq.values())
    tags = {}
    for t in a.tag:
        rc, out, _ = git(repo, "rev-parse", "--verify", "--quiet", f"refs/tags/{t}^{{commit}}")
        tags[t] = out if rc == 0 else None
    if a.ci:
        for items in tasks.values():
            for i in items:
                i["ci_runs"] = ci_runs(i["full"], a.slug)
    doc = {"repo_head": head, "note": "CANDIDATES ONLY. Not evidence until reviewed and approved centrally.",
           "tasks": dict(sorted(tasks.items())), "unresolved_or_ambiguous": unresolved, "tags": tags,
           "milestone_level_commits": milestone_level}
    text = json.dumps(doc, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"{len(tasks)} tasks with resolved SHAs, {len(unresolved)} unresolved/ambiguous; wrote {a.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
