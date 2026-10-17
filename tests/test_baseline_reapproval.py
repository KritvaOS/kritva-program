"""D-027: a new baseline version is frozen by RE-APPROVING (superseding) tasks, not by editing the append-only ledger.

Only an effective approval must be bound to the current baseline version; a superseded one keeps its own version.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import SHA, make_root, row, run, write_sources  # noqa: E402

URL = "https://github.com/KritvaOS/kritvaos-community/actions/runs/1"
TRACK = "v2/tracking/"


def tool(r, name, *args):
    return subprocess.run([sys.executable, str(r / "tools" / name), "--root", str(r), *args], capture_output=True, text=True)


def write_map(r):
    rows = [{"task_id": "I2-001", "workstream_id": "COMMUNITY", "mode": "OWN", "review_flags": [],
             "evidence": {"commit": SHA, "ci_run": 1, "result": "PASS", "url": URL}}]
    (r / TRACK / "evidence_map_proposal.json").write_text(json.dumps({"rows": rows, "unmapped": []}))


def ledger(r):
    return json.loads((r / TRACK / "approvals.json").read_text())["approvals"]


def freeze_v2(r):
    """Add one task to the baseline and freeze it as v2 with the real freeze tool."""
    p = r / TRACK / "baseline.json"
    base = json.loads(p.read_text())
    base["tasks"].append({"id": "I2-NEW", "workstream_id": "COMMUNITY", "milestone_id": "KOS-I2", "title": "New",
                          "weight": None, "requires_physical": False, "phase": None})
    p.write_text(json.dumps(base))
    weights = {t["id"]: {"weight": t["weight"] or 2, "rationale": t.get("weight_rationale") or "test"} for t in base["tasks"]}
    (r / TRACK / "w2.json").write_text(json.dumps({"weights": weights}))
    out = tool(r, "freeze_baseline.py", "--proposal", str(r / TRACK / "w2.json"), "--approve", "--approver", "Dinesh",
               "--commit", SHA, "--reason", "test v2")
    assert out.returncode == 0, out.stderr


class ReapprovalOnNewBaseline(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.r = make_root(self._d.name)
        write_map(self.r)
        out = tool(self.r, "record_approvals.py", "--tasks", "I2-001", "--approver", "Dinesh", "--reason", "v1", "--approve")
        self.assertEqual(out.returncode, 0, out.stderr)
        freeze_v2(self.r)

    def tearDown(self):
        self._d.cleanup()

    def test_unrenewed_v1_approval_is_rejected_on_v2(self):
        write_sources(self.r, "I2-001")
        p = run(self.r, "--sources-dir", str(self.r / "sources"))
        self.assertEqual(p.returncode, 1)
        self.assertIn("baseline_version 1 != current 2", p.stderr + p.stdout)

    def test_reapproval_supersedes_and_restores_credit(self):
        out = tool(self.r, "record_approvals.py", "--tasks", "I2-001")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("supersedes A001", out.stdout)
        out = tool(self.r, "record_approvals.py", "--tasks", "I2-001", "--approver", "Dinesh", "--reason", "re-approve v2", "--approve")
        self.assertEqual(out.returncode, 0, out.stderr)
        led = ledger(self.r)
        self.assertEqual([(x["approval_id"], x["baseline_version"], x.get("supersedes")) for x in led],
                         [("A001", 1, None), ("A002", 2, "A001")])
        write_sources(self.r, "I2-001")
        p = run(self.r, "--sources-dir", str(self.r / "sources"))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(row(self.r, "I2-001")["credit"])

    def test_cannot_reapprove_twice_on_the_same_baseline(self):
        args = ("--tasks", "I2-001", "--approver", "Dinesh", "--reason", "x", "--approve")
        self.assertEqual(tool(self.r, "record_approvals.py", *args).returncode, 0)
        out = tool(self.r, "record_approvals.py", *args)
        self.assertEqual(out.returncode, 1)
        self.assertIn("already approved PASS", out.stderr)
        self.assertEqual(len(ledger(self.r)), 2)


if __name__ == "__main__":
    unittest.main()
