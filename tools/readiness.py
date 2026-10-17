#!/usr/bin/env python3
"""Per-repo readiness checklist for the return to private (D-037, D-038). Display only; never read by compute().

Data: v2/tracking/repo_readiness.json. Each repo carries the same fixed checks. A check status is one of:
  PASS      verified by Claude from git at the repo's checked_head (evidence says how)
  ATTESTED  stated by the owner; not verified by Claude
  OPEN      work remains, or there is no record
  FAIL      a verified problem
  DECISION  an owner decision is needed
  NA        does not apply to this repo
A repo's readiness is derived, never asserted: READY only when every check is PASS, ATTESTED or NA; otherwise
NOT_READY with the blocking checks listed. `owner_signoff` stays DECISION until Dinesh authorises the visibility change
(D-037), so no repo can read READY before that record exists. Recommended state is advice; the owner switches visibility.
Stdlib only. validate() returns (errors, warnings); warnings flag a committed source copy that changed since the check.
"""
import json
import re

FILE = "v2/tracking/repo_readiness.json"
STATUSES = ("PASS", "ATTESTED", "OPEN", "FAIL", "DECISION", "NA")
READY_OK = {"PASS", "ATTESTED", "NA"}
CHECKS = (
    ("milestone_sync", "Milestone alignment: program view of this repo matches the repo and the baseline or inventory"),
    ("status_report", "Schema 2.0 status report committed in the repo"),
    ("history_secret_scan", "History-aware secret scan of all refs"),
    ("secret_scan_ci", "Blocking secret scan in CI"),
    ("commit_message_check", "CI rejects AI session trailers in new commits"),
    ("license", "LICENSE file"),
    ("security_policy", "SECURITY.md"),
    ("codeowners", "CODEOWNERS"),
    ("agents_md", "AGENTS.md"),
    ("branch_protection", "Main-branch protection and required checks"),
    ("branch_hygiene", "No stale or unintended branches"),
    ("security_disposition", "Every security finding has a recorded disposition"),
    ("contract_pin", "Pinned engineering-contract SHA (Core pilot)"),
    ("owner_signoff", "Owner authorises the visibility change (D-037)"),
)
CHECK_IDS = [c[0] for c in CHECKS]
STATES = {"PRIVATE", "PUBLIC"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def validate(doc, registry, source_hashes=None):
    """registry: {workstream_id: entry}. source_hashes: {workstream_id: sha256 of the committed source copy} or None."""
    errs, warns = [], []
    if not isinstance(doc, dict) or not isinstance(doc.get("repos"), list) or not doc["repos"]:
        return ["repos must be a non-empty list"], []
    for k in ("target_date", "report_due", "checked_at", "basis"):
        if not doc.get(k):
            errs.append(f"missing {k}")
    seen = set()
    for r in doc["repos"]:
        name = r.get("repo")
        if not (isinstance(name, str) and re.match(r"^KritvaOS/[A-Za-z0-9._-]+$", name)):
            errs.append(f"repo name must look like KritvaOS/<repo>: {name!r}")
            continue
        if name in seen:
            errs.append(f"{name}: duplicate repo")
        seen.add(name)
        if not HEX40.match(str(r.get("checked_head", ""))):
            errs.append(f"{name}: checked_head must be a 40-hex commit")
        for ws in r.get("workstream_ids", []):
            if ws not in registry:
                errs.append(f"{name}: workstream {ws!r} is not in workstreams.json")
            elif registry[ws].get("repo") not in (None, name):
                errs.append(f"{name}: workstream {ws!r} belongs to {registry[ws]['repo']!r}")
        vis = r.get("visibility_now") or {}
        if vis.get("state") not in STATES or not vis.get("basis"):
            errs.append(f"{name}: visibility_now needs state PRIVATE|PUBLIC and a basis")
        rec = r.get("recommended") or {}
        if rec.get("state") not in STATES or not rec.get("rationale") or not rec.get("owner_action"):
            errs.append(f"{name}: recommended needs state PRIVATE|PUBLIC, rationale and owner_action")
        got = {}
        for c in r.get("checks", []):
            cid = c.get("id")
            if cid not in CHECK_IDS:
                errs.append(f"{name}: unknown check {cid!r}")
            elif cid in got:
                errs.append(f"{name}: duplicate check {cid}")
            got[cid] = c
            if c.get("status") not in STATUSES:
                errs.append(f"{name}/{cid}: status must be one of {list(STATUSES)}")
            if not c.get("detail"):
                errs.append(f"{name}/{cid}: detail is required")
            if c.get("status") == "PASS" and not c.get("evidence"):
                errs.append(f"{name}/{cid}: PASS needs evidence (what was checked, at which commit)")
        for cid in CHECK_IDS:
            if cid not in got:
                errs.append(f"{name}: missing check {cid}")
        if got.get("owner_signoff", {}).get("status") in READY_OK and not got["owner_signoff"].get("evidence"):
            errs.append(f"{name}/owner_signoff: a recorded sign-off needs evidence (decision ID)")
        pc = r.get("program_copy")
        if pc is not None:
            ws, sha = pc.get("workstream_id"), pc.get("sha256")
            if ws not in registry or not HEX64.match(str(sha)):
                errs.append(f"{name}: program_copy needs a registry workstream_id and a 64-hex sha256")
            elif source_hashes is not None and ws in source_hashes and source_hashes[ws] != sha:
                warns.append(f"{name}: the committed source copy for {ws} changed since the readiness check; re-check milestone_sync")
    return errs, warns


def readiness(r):
    blocking = [c["id"] for c in r["checks"] if c["status"] not in READY_OK]
    return ("READY" if not blocking else "NOT_READY"), blocking


def summary(doc):
    out = []
    for r in doc["repos"]:
        state, blocking = readiness(r)
        out.append({"repo": r["repo"], "visibility_now": r["visibility_now"]["state"], "recommended": r["recommended"]["state"],
                    "checked_head": r["checked_head"], "readiness": state, "blocking": blocking,
                    "attested": [c["id"] for c in r["checks"] if c["status"] == "ATTESTED"]})
    return {"target_date": doc["target_date"], "report_due": doc["report_due"], "checked_at": doc["checked_at"], "repos": out}


MARK = {"PASS": "[x]", "NA": "[x]", "ATTESTED": "[ ]", "OPEN": "[ ]", "FAIL": "[ ]", "DECISION": "[ ]"}


def render_lines(doc):
    names = dict(CHECKS)
    L = ["", "## Repo readiness for the return to private", "",
         f"Target: {doc['target_date']} (D-037); readiness report due {doc['report_due']}. Checked {doc['checked_at']}. {doc['basis']}", "",
         "Readiness is derived from the checks below: READY only when every check is PASS, ATTESTED (owner-stated, not verified) or NA. "
         "The recommended state is advice; the owner switches visibility.", "",
         "| Repo | Visibility now | Recommended | Checked head | Readiness | Blocking checks | Attested, not verified |", "|---|---|---|---|---|---|---|"]
    for r in doc["repos"]:
        st, bl = readiness(r)
        L.append(f"| {r['repo']} | {r['visibility_now']['state']} | **{r['recommended']['state']}** | {r['checked_head'][:7]} | {st} | "
                 f"{len(bl)}: {', '.join(bl) if bl else '-'} | "
                 f"{', '.join(c['id'] for c in r['checks'] if c['status'] == 'ATTESTED') or '-'} |")
    for r in doc["repos"]:
        st, bl = readiness(r)
        L += ["", f"### {r['repo']}", "",
              f"- Visibility now: {r['visibility_now']['state']} ({r['visibility_now']['basis']})",
              f"- Recommended: **{r['recommended']['state']}**. {r['recommended']['rationale']} Owner action: {r['recommended']['owner_action']}",
              f"- Checked head: {r['checked_head']}; workstreams: {', '.join(r.get('workstream_ids') or []) or 'none'}; readiness {st}", ""]
        for c in r["checks"]:
            ev = f" Evidence: {c['evidence']}" if c.get("evidence") else ""
            L.append(f"- {MARK[c['status']]} **{c['status']}** {c['id']} ({names[c['id']]}): {c['detail']}{ev}")
    return L
