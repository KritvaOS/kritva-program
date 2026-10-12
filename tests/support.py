"""Shared helpers: build a scratch copy of the repo with an APPROVED baseline (via the real freeze tool)."""
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


def make_root(d, approve=True):
    r = Path(d)
    for sub in ("tools", "schema", "v2", "examples"):
        shutil.copytree(ROOT / sub, r / sub)
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
