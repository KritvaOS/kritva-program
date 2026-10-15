"""Shared helpers: build a scratch copy of the repo with an APPROVED baseline (via the real freeze tool) and an empty approval ledger."""
import copy
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA, OTHER = "a" * 40, "b" * 40
GOOD = {"type": "software", "uri": "u", "description": "d", "commit": SHA,
        "ci_run": "https://example.invalid/run/1", "report_sha256": None, "result": "PASS"}


def make_root(d, approve=True, real=False):
    """Scratch copy of the repo. By default it is reset to the DRAFT baseline (baselines/baseline_v0.json, preserved by
    the first real freeze) so tests can freeze their own; real=True keeps the repo's actual frozen baseline."""
    r = Path(d)
    for sub in ("tools", "schema", "v2", "examples"):
        shutil.copytree(ROOT / sub, r / sub)
    if real:
        return r
    # run verification is off unless a test turns it on
    cfgp = r / "v2/tracking/sources.json"
    cfg = json.loads(cfgp.read_text())
    cfg.pop("require_run_verification", None)
    cfgp.write_text(json.dumps(cfg))
    (r / "v2/tracking/run_verification.json").unlink(missing_ok=True)
    # effort tests start from an empty DRAFT estimate file, whatever the real (possibly approved) one holds
    (r / "v2/tracking/effort_estimates.json").write_text(json.dumps({
        "schema_version": "1.0", "estimate_version": 1, "reporting_cutoff": "2026-10-13", "unit": "person_month",
        "approval": {"status": "DRAFT", "approver": None, "approved_at": None, "commit": None, "content_sha256": None},
        "crosswalk": [], "workstreams": []}))
    (r / "v2/tracking/gate_closures.json").unlink(missing_ok=True)  # tests start with every gate as frozen (OPEN)
    # tests start from an EMPTY approval ledger, whatever the real one holds
    (r / "v2/tracking/approvals.json").write_text(json.dumps({"authorized_approvers": ["Dinesh"], "approvals": []}))
    bdir, v0 = r / "v2/tracking/baselines", r / "v2/tracking/baselines/baseline_v0.json"
    if v0.exists():
        shutil.copy(v0, r / "v2/tracking/baseline.json")
        shutil.rmtree(bdir)
    if approve:
        p = subprocess.run([sys.executable, str(r / "tools/freeze_baseline.py"), "--root", str(r), "--proposal",
                            str(r / "v2/tracking/baseline_v1_proposal.json"), "--approve", "--approver", "Dinesh",
                            "--commit", SHA, "--reason", "test"], capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
    return r


def fresh_ts():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_sources(r, task_id="I2-001", ev=GOOD, drop_core=True):
    src = json.loads((r / "examples/sources/COMMUNITY.example.json").read_text())
    src["source"]["commit"] = SHA
    src["updated_at"] = fresh_ts()
    for t in src["tasks"]:
        if t["task_id"] == task_id:
            t["evidence"] = [copy.deepcopy(ev)]
            t["execution"] = "COMPLETE"
    (r / "sources").mkdir(exist_ok=True)
    (r / "sources/COMMUNITY.json").write_text(json.dumps(src))


def run(r, *args):
    return subprocess.run([sys.executable, str(r / "tools/consolidate_status.py"), "--root", str(r), *args],
                          capture_output=True, text=True)


def row(r, task_id):
    c = json.loads((r / "v2/tracking/consolidated_status.json").read_text())
    return next(x for x in c["tasks"] if x["task_id"] == task_id)
