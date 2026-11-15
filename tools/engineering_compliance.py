#!/usr/bin/env python3
"""Engineering contract compliance report across the seven Kritva repositories (KRP-ENG-001).

Reads each repository's default branch from GitHub with `gh` and records facts only:
  * the agent instructions file (AGENTS.md or CLAUDE.md) at the repository root;
  * which of the program's enforcement workflows exist under .github/workflows;
  * the required status checks of the active rulesets on the default branch (when readable);
  * for kritva-core, the pinned contract file docs/development/ENGINEERING_CONTRACT.pin.json;
  * the commit checkers (scripts/security/check_commit_format.py and check_commit_messages.py): the SHA-256 of each file's
    body (everything from the first docstring line on, so a local copy may differ in its header block) and whether it equals
    the kritva-program copy, which is the base (drift control, kritva-standard roadmap D-14).
It never changes a repository. It does not judge acceptance: the owner reads the table and approves in approvals.json.

  python3 tools/engineering_compliance.py --write     # writes the JSON and Markdown report (owner machine, needs gh)
  python3 tools/engineering_compliance.py --check     # the committed files parse and cover the seven repositories (CI safe)
Stdlib only. Exit 0 ok | 1 check failed | 2 gh or usage error.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ORG = "KritvaOS"
REPOS = ["kritva-program", "kritva-core", "kritvaos-community", "kritva-sense", "kritva-mind", "kritva-motion", "kritva-skill"]
WORKFLOWS = ["commit-message-check", "secret-scan", "readme-check", "pr-acceptance-gate", "unit-tests"]
AGENT_FILES = ["AGENTS.md", "CLAUDE.md"]
CORE_PIN = "docs/development/ENGINEERING_CONTRACT.pin.json"
JSON_OUT = "v2/tracking/engineering_compliance.json"
MD_OUT = "v2/planning/ENGINEERING_CONTRACT_COMPLIANCE.md"
BASE_REPO = "kritva-program"
CHECKERS = ["scripts/security/check_commit_format.py", "scripts/security/check_commit_messages.py"]


def gh(*args):
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or f"gh {' '.join(args)} failed")
    return p.stdout


def _json(run, *args):
    return json.loads(run(*args))


def _exists(run, repo, path):
    try:
        run("api", f"repos/{ORG}/{repo}/contents/{path}", "--jq", ".sha")
        return True
    except RuntimeError as e:
        if "404" in str(e) or "Not Found" in str(e):
            return False
        raise


def body_sha256(text):
    """SHA-256 of a checker's body: the text from the first line that starts the module docstring, so the leading
    header block (copyright, SPDX, component fields) is ignored. None when there is no docstring line."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith('"""'):
            return hashlib.sha256("".join(lines[i:]).encode("utf-8")).hexdigest()
    return None


def _file_text(run, repo, branch, path):
    """Decoded file text from the default branch, or None when the file does not exist."""
    try:
        raw = run("api", f"repos/{ORG}/{repo}/contents/{path}?ref={branch}", "--jq", ".content")
    except RuntimeError as e:
        if "404" in str(e) or "Not Found" in str(e):
            return None
        raise
    return base64.b64decode(raw).decode("utf-8")


def collect_checkers(run, repo, branch):
    out = {}
    for path in CHECKERS:
        text = _file_text(run, repo, branch, path)
        out[path] = {"present": text is not None, "body_sha256": body_sha256(text) if text is not None else None}
    return out


def mark_drift(report):
    """Add matches_base to every checker entry, comparing with the base repository's body hashes."""
    base = next((r for r in report["repos"] if r["repo"] == BASE_REPO), None)
    for r in report["repos"]:
        for path, c in (r.get("checkers") or {}).items():
            want = ((base or {}).get("checkers") or {}).get(path, {}).get("body_sha256")
            c["matches_base"] = bool(c["present"] and want and c["body_sha256"] == want)


def collect(run=gh, repos=REPOS, now=None, with_checkers=False):
    """Return the report dict. `run(*gh_args)` returns stdout text; tests pass a fake.
    with_checkers also records the commit checker body hashes and the comparison with the base."""
    out = {"generated_at": now or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "org": ORG, "repos": []}
    for repo in repos:
        info = _json(run, "api", f"repos/{ORG}/{repo}", "--jq", "{default_branch: .default_branch, private: .private}")
        branch = info["default_branch"]
        head = run("api", f"repos/{ORG}/{repo}/commits/{branch}", "--jq", ".sha").strip()
        files = _json(run, "api", f"repos/{ORG}/{repo}/contents/.github/workflows?ref={branch}", "--jq", "[.[].name]")
        present = {w: any(f in (f"{w}.yml", f"{w}.yaml") for f in files) for w in WORKFLOWS}
        agents = [a for a in AGENT_FILES if _exists(run, repo, a)]
        required, readable = [], True
        try:
            for rs in _json(run, "api", f"repos/{ORG}/{repo}/rulesets", "--jq", "[.[] | {id, enforcement}]"):
                if rs.get("enforcement") != "active":
                    continue
                det = _json(run, "api", f"repos/{ORG}/{repo}/rulesets/{rs['id']}")
                for rule in det.get("rules", []):
                    if rule.get("type") == "required_status_checks":
                        required += [c["context"] for c in rule["parameters"].get("required_status_checks", [])]
        except (RuntimeError, KeyError, ValueError):
            readable = False
        entry = {"repo": repo, "default_branch": branch, "head": head, "agent_files": agents, "workflows": present,
                 "required_checks": sorted(set(required)) if readable else None}
        if repo == "kritva-core":
            entry["contract_pin"] = _exists(run, repo, CORE_PIN)
        if with_checkers:
            entry["checkers"] = collect_checkers(run, repo, branch)
        out["repos"].append(entry)
    if with_checkers:
        mark_drift(out)
    return out


def problems(report, repos=REPOS):
    errs = []
    got = [r["repo"] for r in report.get("repos", [])]
    if got != list(repos):
        errs.append(f"repositories are {got}, expected {list(repos)}")
    for r in report.get("repos", []):
        if len(str(r.get("head", ""))) != 40:
            errs.append(f"{r['repo']}: head is not a 40-hex commit")
        if not set(r.get("workflows", {})) == set(WORKFLOWS):
            errs.append(f"{r['repo']}: workflow list incomplete")
    return errs


def render(report):
    L = ["# Engineering contract compliance report (KRP-ENG-001)", "",
         f"Generated {report['generated_at']} by `tools/engineering_compliance.py` from the default branch of each repository on GitHub. "
         "It records facts only; it is not an acceptance decision. Acceptance is the owner's approval record in `v2/tracking/approvals.json`.", "",
         "| Repository | Default branch head | Agent file | " + " | ".join(WORKFLOWS) + " | Required checks on the default branch |",
         "|---|---|---|" + "---|" * len(WORKFLOWS) + "---|"]
    for r in report["repos"]:
        req = "not readable" if r["required_checks"] is None else (", ".join(r["required_checks"]) or "none")
        L.append(f"| {r['repo']} | `{r['head'][:7]}` | {', '.join(r['agent_files']) or 'MISSING'} | "
                 + " | ".join("yes" if r["workflows"][w] else "no" for w in WORKFLOWS) + f" | {req} |")
    core = next((r for r in report["repos"] if r["repo"] == "kritva-core"), None)
    if core is not None:
        L += ["", f"Core engineering contract pin file `{CORE_PIN}`: {'present' if core.get('contract_pin') else 'MISSING'}."]
    gaps = []
    for r in report["repos"]:
        if not r["agent_files"]:
            gaps.append(f"{r['repo']} has no AGENTS.md or CLAUDE.md")
        for w in ("commit-message-check", "secret-scan"):
            if not r["workflows"][w]:
                gaps.append(f"{r['repo']} has no {w} workflow")
    if any("checkers" in r for r in report["repos"]):
        L += ["", "## Commit checker drift (body hash against the kritva-program copy)", "",
              "| Repository | " + " | ".join(Path(c).name for c in CHECKERS) + " |", "|---|" + "---|" * len(CHECKERS)]
        for r in report["repos"]:
            cells = []
            for c in CHECKERS:
                e = (r.get("checkers") or {}).get(c)
                cells.append("not recorded" if e is None else "missing" if not e["present"]
                             else f"{e['body_sha256'][:12]} {'matches base' if e['matches_base'] else 'DIFFERS'}")
            L.append(f"| {r['repo']} | " + " | ".join(cells) + " |")
        for r in report["repos"]:
            for c, e in (r.get("checkers") or {}).items():
                if e["present"] and not e["matches_base"]:
                    gaps.append(f"{r['repo']} {Path(c).name} differs from the kritva-program copy")
                elif not e["present"] and r["repo"] in ("kritva-program", "kritva-core", "kritvaos-community"):
                    gaps.append(f"{r['repo']} has no {Path(c).name}")
    L += ["", "## Differences to read before approving", ""]
    L += [f"- {g}." for g in gaps] or ["- None in the agent file, commit-message-check and secret-scan checks."]
    L += ["- `no` in the pr-acceptance-gate, unit-tests or readme-check columns is not itself a gap: the owner decisions D-061 and PD-018 require the PR gate in the four capability repositories (Sense, Mind, Motion, Skill) and the program, and the commit standard in Core and Community. Read the column against those decisions.",
          "- A repository's default branch can move after this report; the head commit column says what was read.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root)
    if a.write:
        try:
            rep = collect(with_checkers=True)
        except (RuntimeError, OSError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
        (root / JSON_OUT).write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
        (root / MD_OUT).write_text(render(rep), encoding="utf-8")
        print(f"wrote {JSON_OUT} and {MD_OUT}")
        return 0
    if a.check:
        errs = []
        try:
            rep = json.loads((root / JSON_OUT).read_text(encoding="utf-8"))
            errs = problems(rep)
            if (root / MD_OUT).read_text(encoding="utf-8") != render(rep):
                errs.append(f"{MD_OUT} does not match {JSON_OUT}")
        except (OSError, ValueError, KeyError) as e:
            errs.append(str(e))
        for e in errs:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1 if errs else 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
