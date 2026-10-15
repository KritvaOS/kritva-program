#!/usr/bin/env python3
"""Owner-approved effort estimates (person-months), kept SEPARATE from evidence-credited progress (D-020).

File: v2/tracking/effort_estimates.json. Effort is an owner estimate, never evidence:
  * nothing here is read by the credit computation (compute() in consolidate_status.py never sees it);
  * missing data is NOT_ESTIMATED, never zero;
  * each estimate is low/base/high; total = completed + remaining, derived per bound, never stored;
  * completed effort carries a provenance (RECORDED_ACTUAL | RECONSTRUCTED_ACTUAL | OWNER_ESTIMATE);
    commits, closed milestones and CI runs show that work happened, not how many person-months it took;
  * an APPROVED file needs an authorized approver, a time, a 40-hex commit and a content hash.

CLI (owner-run; dry run unless --approve):
  python3 tools/effort.py --root . --check
  python3 tools/effort.py --root . --approve --approver Dinesh --commit <40hex> [--at <UTC time>]
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path

FILE = "v2/tracking/effort_estimates.json"
SHA = re.compile(r"^[0-9a-f]{40}$")
COMPLETED_BASIS = {"RECORDED_ACTUAL", "RECONSTRUCTED_ACTUAL", "OWNER_ESTIMATE"}
REMAINING_BASIS = {"OWNER_ESTIMATE"}
CONFIDENCE = {"H", "M", "L"}
TOP = {"schema_version", "estimate_version", "reporting_cutoff", "unit", "approval", "crosswalk", "workstreams", "_note"}
APPROVAL = {"status", "approver", "approved_at", "commit", "content_sha256"}
WS_KEYS = {"workstream_id", "completed", "remaining", "confidence", "assumptions", "source_refs", "owner_notes"}
CROSS_KEYS = {"legacy_name", "status", "maps_to", "rationale"}


def content_hash(doc):
    """SHA-256 over the file without its approval block, so approving does not change what was approved."""
    body = {k: v for k, v in doc.items() if k != "approval"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0


def _range(r, name, allowed, errs):
    """Return (low, base, high) or None when the estimate is absent (NOT_ESTIMATED)."""
    if r is None:
        return None
    if not isinstance(r, dict) or set(r) != {"low", "base", "high", "basis"}:
        errs.append(f"{name}: must be null or {{low, base, high, basis}}")
        return None
    if not all(_num(r[k]) for k in ("low", "base", "high")):
        errs.append(f"{name}: low/base/high must be finite non-negative numbers")
        return None
    if not r["low"] <= r["base"] <= r["high"]:
        errs.append(f"{name}: need low <= base <= high")
        return None
    if r["basis"] not in allowed:
        errs.append(f"{name}: basis must be one of {sorted(allowed)}")
        return None
    return r["low"], r["base"], r["high"]


def validate(doc, registry_ids, authorized):
    errs = []
    if not isinstance(doc, dict):
        return ["not a JSON object"]
    errs += [f"unknown key {k!r}" for k in sorted(set(doc) - TOP)]
    if doc.get("schema_version") != "1.0":
        errs.append("schema_version must be '1.0'")
    if doc.get("unit") != "person_month":
        errs.append("unit must be 'person_month'")
    if not isinstance(doc.get("estimate_version"), int) or isinstance(doc.get("estimate_version"), bool) or doc["estimate_version"] < 1:
        errs.append("estimate_version must be an integer >= 1")
    if not isinstance(doc.get("reporting_cutoff"), str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", doc.get("reporting_cutoff", "")):
        errs.append("reporting_cutoff must be YYYY-MM-DD")

    ap = doc.get("approval")
    if not isinstance(ap, dict) or set(ap) != APPROVAL or ap.get("status") not in ("DRAFT", "APPROVED"):
        errs.append("approval must hold exactly status (DRAFT|APPROVED), approver, approved_at, commit, content_sha256")
    elif ap["status"] == "DRAFT":
        if any(ap[k] is not None for k in ("approver", "approved_at", "commit", "content_sha256")):
            errs.append("a DRAFT approval block must have null approver, approved_at, commit and content_sha256")
    else:
        if ap["approver"] not in authorized:
            errs.append(f"approval: approver {ap['approver']!r} is not an authorized approver")
        if not isinstance(ap["approved_at"], str) or not ap["approved_at"]:
            errs.append("approval: approved_at is required")
        if not isinstance(ap["commit"], str) or not SHA.match(ap["commit"]):
            errs.append("approval: commit must be a 40-hex SHA")
        if ap["content_sha256"] != content_hash(doc):
            errs.append("approval: content_sha256 does not match the file (edited after approval; create a new estimate_version)")

    seen = set()
    for i, w in enumerate(doc.get("workstreams") or []):
        tag = f"workstreams[{i}]"
        if not isinstance(w, dict) or "workstream_id" not in w:
            errs.append(f"{tag}: needs workstream_id")
            continue
        wid = w["workstream_id"]
        tag = f"workstream {wid}"
        errs += [f"{tag}: unknown key {k!r}" for k in sorted(set(w) - WS_KEYS)]
        if wid not in registry_ids:
            errs.append(f"{tag}: not in workstreams.json")
        if wid in seen:
            errs.append(f"{tag}: duplicate")
        seen.add(wid)
        comp = _range(w.get("completed"), f"{tag} completed", COMPLETED_BASIS, errs)
        rem = _range(w.get("remaining"), f"{tag} remaining", REMAINING_BASIS, errs)
        if comp or rem:
            if w.get("confidence") not in CONFIDENCE:
                errs.append(f"{tag}: confidence must be H, M or L when effort is given")
            reconstructed = (w.get("completed") or {}).get("basis") in ("RECONSTRUCTED_ACTUAL", "OWNER_ESTIMATE")
            if w.get("confidence") in ("M", "L") or reconstructed:
                if not w.get("assumptions") or not w.get("source_refs"):
                    errs.append(f"{tag}: assumptions and source_refs are required for M/L confidence or non-recorded completed effort")
        for k in ("assumptions", "source_refs"):
            if k in w and not (isinstance(w[k], list) and all(isinstance(x, str) and x for x in w[k])):
                errs.append(f"{tag}: {k} must be a list of non-empty strings")

    names = set()
    for i, c in enumerate(doc.get("crosswalk") or []):
        tag = f"crosswalk[{i}]"
        if not isinstance(c, dict) or not c.get("legacy_name"):
            errs.append(f"{tag}: needs legacy_name")
            continue
        errs += [f"{tag}: unknown key {k!r}" for k in sorted(set(c) - CROSS_KEYS)]
        if c["legacy_name"] in names:
            errs.append(f"{tag}: duplicate legacy_name {c['legacy_name']!r}")
        names.add(c["legacy_name"])
        if c.get("status") not in ("UNDECIDED", "MAPPED"):
            errs.append(f"{tag}: status must be UNDECIDED or MAPPED")
        elif c["status"] == "MAPPED":
            mt = c.get("maps_to") or []
            ok = bool(mt) and all(isinstance(m, dict) and set(m) == {"workstream_id", "share"} and m["workstream_id"] in registry_ids
                                  and _num(m["share"]) for m in mt)
            if not ok or abs(sum(m["share"] for m in mt) - 1.0) > 1e-9:
                errs.append(f"{tag}: MAPPED needs workstream_ids from the registry with shares summing to 1")
            if not c.get("rationale"):
                errs.append(f"{tag}: MAPPED needs a rationale")
    return errs


def _fmt(t):
    return f"{t[1]:g} ({t[0]:g}-{t[2]:g})"


def summary(doc, registry, by_workstream):
    """Display data only. `registry` is {id: name-bearing dict}; by_workstream is the evidence rollup."""
    est = {w["workstream_id"]: w for w in (doc.get("workstreams") or [])}
    rows, sums = [], {"completed": [0, 0, 0], "remaining": [0, 0, 0], "total": [0, 0, 0]}
    counted = 0
    for wid in sorted(registry):
        w = est.get(wid, {})
        c, r = w.get("completed"), w.get("remaining")
        ct = (c["low"], c["base"], c["high"]) if c else None
        rt = (r["low"], r["base"], r["high"]) if r else None
        tt = tuple(a + b for a, b in zip(ct, rt)) if ct and rt else None
        g = by_workstream.get(wid)
        prog = (f"{g['accepted_weight']}/{g['weight']} weight" if g and g.get("weighted") else "Not baselined")
        rows.append({"workstream_id": wid, "completed": ct, "completed_basis": (c or {}).get("basis"), "remaining": rt,
                     "total": tt, "confidence": w.get("confidence") if (ct or rt) else None, "evidence_progress": prog})
        for key, t in (("completed", ct), ("remaining", rt), ("total", tt)):
            if t:
                sums[key] = [x + y for x, y in zip(sums[key], t)]
        counted += 1 if tt else 0
    cw = doc.get("crosswalk") or []
    return {"estimate_version": doc.get("estimate_version"), "status": doc["approval"]["status"],
            "reporting_cutoff": doc.get("reporting_cutoff"), "unit": "person_month", "rows": rows,
            "workstreams_fully_estimated": counted, "workstreams_total": len(registry),
            "sums": {k: tuple(v) for k, v in sums.items()},
            "crosswalk_undecided": sorted(c["legacy_name"] for c in cw if c.get("status") == "UNDECIDED")}


def render_lines(s):
    L = ["", "## Effort accounting (owner estimates in person-months; NOT evidence and never part of accepted progress)", ""]
    L.append(f"- Estimate version {s['estimate_version']}, cutoff {s['reporting_cutoff']}: "
             f"{'APPROVED by the owner' if s['status'] == 'APPROVED' else 'DRAFT, not owner-approved'}")
    L.append(f"- Workstreams with completed and remaining estimated: {s['workstreams_fully_estimated']}/{s['workstreams_total']}; "
             "all others show NOT_ESTIMATED (never zero)")
    L.append("- Format: base (low-high). Total = completed + remaining per bound. Completed effort is not capability complete: "
             "see Evidence-credited progress, which comes only from the approved baseline")
    if s["crosswalk_undecided"]:
        L.append(f"- Legacy workstream names awaiting an owner mapping: {', '.join(s['crosswalk_undecided'])}")
    L += ["", "| Workstream | Completed PM | Basis | Remaining PM | Total PM | Confidence | Evidence-credited progress |",
          "|---|---|---|---|---|---|---|"]
    for r in s["rows"]:
        f = lambda t: _fmt(t) if t else "NOT_ESTIMATED"
        L.append(f"| {r['workstream_id']} | {f(r['completed'])} | {r['completed_basis'] or '-'} | {f(r['remaining'])} | "
                 f"{f(r['total'])} | {r['confidence'] or '-'} | {r['evidence_progress']} |")
    sm = s["sums"]
    if s["workstreams_fully_estimated"]:
        L.append(f"| **Sum of estimated rows** | {_fmt(sm['completed'])} | | {_fmt(sm['remaining'])} | {_fmt(sm['total'])} | | |")
        L += ["", "Sums add the stated bounds and ignore correlated risk; they cover estimated workstreams only."]
    return L


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--check", action="store_true", help="validate only")
    ap.add_argument("--approve", action="store_true")
    ap.add_argument("--approver")
    ap.add_argument("--commit")
    ap.add_argument("--at", help="approval time (UTC, default now)")
    a = ap.parse_args()
    root = Path(a.root)
    doc = json.loads((root / FILE).read_text(encoding="utf-8"))
    reg = {w["id"] for w in json.loads((root / "v2/tracking/workstreams.json").read_text())["workstreams"]}
    authorized = set(json.loads((root / "v2/tracking/approvals.json").read_text()).get("authorized_approvers", []))
    errs = validate(doc, reg, authorized)
    if a.approve:
        if doc["approval"]["status"] == "APPROVED":
            errs.append("already APPROVED: create a new estimate_version instead of re-approving")
        if a.approver not in authorized:
            errs.append(f"approver {a.approver!r} is not authorized")
        if not (a.commit and SHA.match(a.commit)):
            errs.append("--commit must be a 40-hex SHA")
    for e in errs:
        print(f"ERROR: {e}", file=sys.stderr)
    if errs:
        return 1
    if a.approve:
        doc["approval"] = {"status": "APPROVED", "approver": a.approver,
                           "approved_at": a.at or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                           "commit": a.commit, "content_sha256": content_hash(doc)}
        (root / FILE).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(f"APPROVED estimate_version {doc['estimate_version']} by {a.approver}")
    else:
        print("OK (no changes written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
