#!/usr/bin/env python3
"""Freeze an approved baseline version (D-015). Run by the OWNER; Claude/Codex only prepare the proposal.

  Dry run (default):  python3 tools/freeze_baseline.py --proposal v2/tracking/baseline_v1_proposal.json
  Approve and freeze: python3 tools/freeze_baseline.py --proposal ... --approver Dinesh \\
                          --commit "$(git rev-parse HEAD)" --reason "<why>" --approve

What --approve does (and refuses to do):
  * requires --approver to be in approvals.json authorized_approvers and --commit to be a 40-hex SHA;
  * requires every baseline task to get a positive integer weight and a rationale from the proposal;
  * writes v2/tracking/baselines/baseline_v<N>.json (immutable: refuses to overwrite) and makes
    v2/tracking/baseline.json identical to it, with an `approval` block holding the approver, UTC time,
    canonical commit and the SHA-256 of the baseline data;
  * preserves the previous version as baselines/baseline_v<old>.json and appends the reason to
    baselines/CHANGELOG.json.
The consolidator re-checks the hash and the frozen copy on every run, so editing baseline.json afterwards
is reported as an error until a new baseline_version is frozen.
Stdlib only. Never commits or pushes.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import consolidate_status as cs  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--proposal", required=True, help="JSON with weights[task_id] = {weight, rationale}")
    ap.add_argument("--approve", action="store_true")
    ap.add_argument("--approver")
    ap.add_argument("--commit", help="40-hex kritva-program commit this approval is anchored to")
    ap.add_argument("--reason")
    ap.add_argument("--at", help="ISO-8601 UTC approval time (default: now)")
    a = ap.parse_args()
    root = Path(a.root)
    track = root / cs.TRACK
    base = json.loads((track / "baseline.json").read_text(encoding="utf-8"))
    ledger = json.loads((track / "approvals.json").read_text(encoding="utf-8"))
    prop = json.loads(Path(a.proposal).read_text(encoding="utf-8"))["weights"]
    errs = []
    ids = [t["id"] for t in base["tasks"]]
    if set(prop) != set(ids):
        errs.append(f"proposal must cover exactly the baseline tasks (missing {sorted(set(ids) - set(prop))}, "
                    f"extra {sorted(set(prop) - set(ids))})")
    for tid, w in prop.items():
        if not isinstance(w.get("weight"), int) or isinstance(w.get("weight"), bool) or w["weight"] <= 0:
            errs.append(f"{tid}: weight must be a positive integer")
        if not str(w.get("rationale", "")).strip():
            errs.append(f"{tid}: rationale required")
    new = json.loads(json.dumps(base))
    old_version = base["baseline_version"]
    new["baseline_version"] = old_version + 1
    new["baseline_approved"] = True
    new.pop("approval", None)
    for t in new["tasks"]:
        if t["id"] in prop:
            t["weight"] = prop[t["id"]]["weight"]
            t["weight_rationale"] = prop[t["id"]]["rationale"]
    total = sum(t.get("weight") or 0 for t in new["tasks"])
    print(f"proposed baseline v{new['baseline_version']}: {len(ids)} tasks, total weight {total}")
    h = cs.baseline_hash(new)
    print(f"baseline data sha256 (before approval record): {h}")
    if not a.approve:
        for e in errs:
            print(f"ERROR: {e}", file=sys.stderr)
        print("dry run only; nothing written")
        return 1 if errs else 0
    if a.approver not in ledger.get("authorized_approvers", []):
        errs.append(f"--approver {a.approver!r} is not an authorized approver")
    if not a.commit or not re.fullmatch(r"[0-9a-f]{40}", a.commit):
        errs.append("--commit must be a 40-hex SHA")
    if not (a.reason or "").strip():
        errs.append("--reason is required")
    frozen_dir = track / "baselines"
    target = frozen_dir / f"baseline_v{new['baseline_version']}.json"
    if target.exists():
        errs.append(f"{target.name} already exists; frozen versions are immutable")
    if errs:
        for e in errs:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    at = a.at or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new["approval"] = {"approver": a.approver, "approved_at": at, "canonical_commit": a.commit,
                       "baseline_sha256": cs.baseline_hash(new), "reason": a.reason}
    frozen_dir.mkdir(parents=True, exist_ok=True)
    prev = frozen_dir / f"baseline_v{old_version}.json"
    if not prev.exists():
        prev.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    text = json.dumps(new, indent=2) + "\n"
    target.write_text(text, encoding="utf-8")
    (track / "baseline.json").write_text(text, encoding="utf-8")
    log = frozen_dir / "CHANGELOG.json"
    entries = json.loads(log.read_text(encoding="utf-8")) if log.exists() else []
    entries.append({"from_version": old_version, "to_version": new["baseline_version"], "approver": a.approver,
                    "approved_at": at, "canonical_commit": a.commit, "reason": a.reason,
                    "baseline_sha256": new["approval"]["baseline_sha256"]})
    log.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(f"frozen baseline v{new['baseline_version']} by {a.approver}; run tools/consolidate_status.py next")
    return 0


if __name__ == "__main__":
    sys.exit(main())
