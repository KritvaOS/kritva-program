#!/usr/bin/env python3
"""Sweep open pull requests through the PR acceptance gate and, where it is clear, approve them (D-046).

  pr_check.py all                          every repository in the list, every open PR
  pr_check.py all --repos a,b,c            the list given here (the Makefile passes its REPOS array); default: every manifest repo
  pr_check.py --repo kritva-sense          every open PR of one repository
  pr_check.py --repo kritva-sense --pr 7   one PR
  --no-approve                             report only; never submit a review
  --manifest PATH                          default v2/planning/repo-pipeline.json

What it does with each PR (it never merges, never edits a PR and never requests changes):
  REJECT        a mechanical rule failed. Left alone; the reason is printed.
  NEEDS_HUMAN   a judgement or an approval from someone else remains. Left alone; the reason is printed.
  CLEAR         every rule except the required approvals passes and the signed-in `gh` user holds a required role. An approving review is
                submitted as that user, pinned to the head SHA that was evaluated, and the PR is evaluated again.
  APPROVE       every rule passes and every required approval is on the current head (after the review above, or already there).
The signed-in `gh` user is the approver. GitHub does not count an author approving their own PR, so those stay NEEDS_HUMAN.
Drafts are never approved. Exit 1 if any PR is REJECT, 2 if a repository or PR could not be read, otherwise 0.
Stdlib only.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr_gate as G  # noqa: E402

DEFAULT_MANIFEST = Path(__file__).resolve().parents[2] / "v2/planning/repo-pipeline.json"
BODY = "Approved by the kritva-program PR acceptance gate (D-046): every mechanical rule passed on this head. Merging is a separate owner action."


def evaluate(manifest, gate, number, run=G.sh):
    commits, files, read, pr = G.remote_inputs(gate["github_repo"], number, run=run)
    return G.static_rules(gate, commits, files, read) + G.remote_rules(gate, manifest, pr), pr


def role_logins(manifest, role):
    people = manifest.get("people", {})
    return {people[h]["github_login"] for h in manifest["roles"][role]["holders"] if h in people}


def classify(manifest, gate, results, pr, me):
    """-> (state, note). State is REJECT, NEEDS_HUMAN, CLEAR or APPROVE."""
    v = G.verdict(results)
    if v in ("REJECT", "APPROVE"):
        return v, ""
    rest = [r for r in results if r["rule"] != "R07"]
    if G.verdict(rest) != "APPROVE":
        return "NEEDS_HUMAN", "a rule other than the approvals needs a person"
    mine = [role for role in gate["required_approvals"] if me in role_logins(manifest, role)]
    if not mine:
        return "NEEDS_HUMAN", f"{me or 'the signed-in user'} holds none of the required roles"
    if pr["author"] == me:
        return "NEEDS_HUMAN", f"{me} authored this PR and GitHub does not count self-approval"
    if any(x["login"] == me and x["state"] == "APPROVED" and x["commit"] == pr["head_sha"] for x in pr["reviews"]):
        return "NEEDS_HUMAN", "already approved by the signed-in user; other roles are outstanding"
    return "CLEAR", ", ".join(mine)


def approve(gate, number, head, run=G.sh):
    run("gh", "api", "-X", "POST", f"repos/{gate['github_repo']}/pulls/{number}/reviews",
        "-f", "event=APPROVE", "-f", f"commit_id={head}", "-f", f"body={BODY}")


def first_failure(results):
    for lv in (G.FAIL, G.HUMAN):
        for r in results:
            if r["level"] == lv:
                return f"{r['rule']}: {r['message']}"
    return ""


def sweep(manifest, repos, only_pr, do_approve, run=G.sh, out=print):
    try:
        me = run("gh", "api", "user", "--jq", ".login").strip()
    except RuntimeError:
        me = ""
    rows, errors, reject = [], 0, 0
    for rid in repos:
        gate = G.gate_for(manifest, rid)
        try:
            prs = [{"number": int(only_pr)}] if only_pr else json.loads(run("gh", "pr", "list", "-R", gate["github_repo"], "--state", "open", "--json", "number,isDraft,title"))
        except (RuntimeError, ValueError) as e:
            rows.append((rid, "-", "ERROR", str(e)[:120])); errors += 1; continue
        if not prs:
            rows.append((rid, "-", "no open PR", ""))
        for p in prs:
            n = p["number"]
            try:
                results, pr = evaluate(manifest, gate, n, run)
                state, note = classify(manifest, gate, results, pr, me)
                if p.get("isDraft") and state == "CLEAR":
                    state, note = "NEEDS_HUMAN", "draft PR is not approved"
                detail = note or first_failure(results)
                if state == "CLEAR" and do_approve:
                    approve(gate, n, pr["head_sha"], run)
                    results, pr = evaluate(manifest, gate, n, run)
                    state = G.verdict(results)
                    detail = f"approved as {me} on {pr['head_sha'][:7]}" + ("" if state == "APPROVE" else f"; still {state}: {first_failure(results)}")
                elif state == "CLEAR":
                    detail = f"would approve as {me} (--no-approve): {note}"
                reject += state == "REJECT"
                rows.append((rid, f"#{n}", state, detail))
            except (RuntimeError, KeyError, ValueError) as e:
                rows.append((rid, f"#{n}", "ERROR", str(e)[:120])); errors += 1
    out("| Repository | PR | Result | Detail |\n|---|---|---|---|")
    for r in rows:
        out("| " + " | ".join(str(c).replace("|", "/") for c in r) + " |")
    out("\nReport and approval only: nothing was merged or changed. Merge is an owner action (ship-prs.sh).")
    return 2 if errors else (1 if reject else 0)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", choices=["all"])
    ap.add_argument("--repo"); ap.add_argument("--pr")
    ap.add_argument("--repos", help="comma or space separated repo ids for `all`; each must exist in the manifest")
    ap.add_argument("--no-approve", action="store_true")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    a = ap.parse_args(argv)
    if bool(a.target) == bool(a.repo):
        ap.error("give either `all` or --repo REPO")
    if a.pr and not a.repo:
        ap.error("--pr needs --repo")
    manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    if a.repos and not a.target:
        ap.error("--repos goes with `all`")
    if a.target:
        repos = a.repos.replace(",", " ").split() if a.repos else [r["repo_id"] for r in manifest["repositories"]]
        if not repos:
            ap.error("the repository list is empty")
        known = {r["repo_id"] for r in manifest["repositories"]}
        unknown = [r for r in repos if r not in known]
        if unknown:
            ap.error(f"not in the manifest: {', '.join(unknown)}")
    else:
        repos = [a.repo]
    return sweep(manifest, repos, a.pr, not a.no_approve)


if __name__ == "__main__":
    sys.exit(main())
