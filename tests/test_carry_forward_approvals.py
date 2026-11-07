"""Test tools/carry_forward_approvals.py: a new baseline version leaves approvals stale; carrying them forward restores credit."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import GOOD, SHA, make_root, row, run, write_sources  # noqa: E402


def tool(r, *args):
    return subprocess.run([sys.executable, str(r / "tools/carry_forward_approvals.py"), "--root", str(r), *args],
                          capture_output=True, text=True)


def ledger(r):
    return json.loads((r / "v2/tracking/approvals.json").read_text())["approvals"]


def setup(d, version):
    r = make_root(d)
    base = json.loads((r / "v2/tracking/baseline.json").read_text())
    base["baseline_version"] = version
    (r / "v2/tracking/baseline.json").write_text(json.dumps(base))
    ap = {"approval_id": "A1", "task_id": "I2-001", "baseline_version": 1, "source_repo": "KritvaOS/kritvaos-community",
          "source_commit": SHA, "review_status": "APPROVED", "acceptance": "PASS", "approver": "Dinesh",
          "approved_at": "2026-10-11T12:00:00Z", "evidence_refs": ["x"], "rationale": "r"}
    (r / "v2/tracking/approvals.json").write_text(json.dumps({"authorized_approvers": ["Dinesh"], "approvals": [ap]}))
    return r


class CarryForward(unittest.TestCase):
    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            r = setup(d, 2)
            p = tool(r)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("dry run", p.stdout)
            self.assertEqual(len(ledger(r)), 1)

    def test_approve_appends_superseding_record_and_keeps_old(self):
        with tempfile.TemporaryDirectory() as d:
            r = setup(d, 2)
            p = tool(r, "--approver", "Dinesh", "--reason", "carry forward", "--at", "2026-11-08T00:00:00Z", "--approve")
            self.assertEqual(p.returncode, 0, p.stderr)
            led = ledger(r)
            self.assertEqual(len(led), 2)
            self.assertEqual((led[0]["approval_id"], led[0]["baseline_version"]), ("A1", 1))
            new = led[1]
            self.assertEqual((new["task_id"], new["baseline_version"], new["supersedes"], new["source_commit"]), ("I2-001", 2, "A1", SHA))
            self.assertEqual(tool(r).stdout.count("->"), 0)  # nothing left to carry

    def test_refuses_unauthorized_approver_and_missing_reason(self):
        with tempfile.TemporaryDirectory() as d:
            r = setup(d, 2)
            self.assertEqual(tool(r, "--approver", "Eve", "--reason", "x", "--approve").returncode, 1)
            self.assertEqual(tool(r, "--approver", "Dinesh", "--approve").returncode, 1)
            self.assertEqual(len(ledger(r)), 1)


if __name__ == "__main__":
    unittest.main()
