"""Test tools/record_approvals.py: dry run writes nothing; refusals; recorded approvals earn credit end to end."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import OTHER, SHA, make_root, row, run, write_sources  # noqa: E402

URL = "https://github.com/KritvaOS/kritvaos-community/actions/runs/1"


def write_map(r, commit=SHA, mode="OWN", flags=()):
    rows = [{"task_id": t, "workstream_id": "COMMUNITY", "mode": mode, "review_flags": list(flags),
             "evidence": {"commit": commit, "ci_run": 1, "result": "PASS", "url": URL}}
            for t in ("I2-001", "I2-002")]
    (r / "v2/tracking/evidence_map_proposal.json").write_text(json.dumps({"rows": rows, "unmapped": []}))


def tool(r, *args):
    return subprocess.run([sys.executable, str(r / "tools/record_approvals.py"), "--root", str(r), *args],
                          capture_output=True, text=True)


def ledger(r):
    return json.loads((r / "v2/tracking/approvals.json").read_text())["approvals"]


class RecordApprovals(unittest.TestCase):
    def test_dry_run_writes_nothing_and_approve_earns_credit(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            write_map(r)
            p = tool(r, "--tasks", "I2-001")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("dry run", p.stdout)
            self.assertEqual(ledger(r), [])
            p = tool(r, "--tasks", "I2-001", "--approver", "Dinesh", "--reason", "checked criteria", "--approve")
            self.assertEqual(p.returncode, 0, p.stderr)
            rec = ledger(r)[0]
            self.assertEqual((rec["task_id"], rec["source_commit"], rec["acceptance"], rec["review_status"],
                              rec["baseline_version"], rec["source_repo"]),
                             ("I2-001", SHA, "PASS", "APPROVED", 1, "KritvaOS/kritvaos-community"))
            write_sources(r, "I2-001")
            self.assertEqual(run(r, "--sources-dir", str(r / "sources")).returncode, 0)
            x = row(r, "I2-001")
            self.assertTrue(x["credit"], x["credit_reason"])
            self.assertFalse(row(r, "I2-002")["credit"])

    def test_refusals(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            write_map(r)
            ok = ["--tasks", "I2-001", "--approve", "--reason", "x"]
            self.assertEqual(tool(r, *ok, "--approver", "Eve").returncode, 1)  # unauthorized
            self.assertEqual(tool(r, "--tasks", "I2-001", "--approve", "--approver", "Dinesh").returncode, 1)  # no reason
            self.assertEqual(tool(r, "--tasks", "I9-999").returncode, 1)  # not in the map
            self.assertEqual(ledger(r), [])
            self.assertEqual(tool(r, *ok, "--approver", "Dinesh").returncode, 0)
            self.assertEqual(tool(r, *ok, "--approver", "Dinesh").returncode, 1)  # duplicate PASS on same commit
            self.assertEqual(len(ledger(r)), 1)

    def test_draft_baseline_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d, approve=False)
            write_map(r)
            self.assertEqual(tool(r, "--tasks", "I2-001", "--approve", "--approver", "Dinesh", "--reason", "x").returncode, 1)

    def test_new_commit_supersedes_old_approval_and_prefix_selects(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            write_map(r)
            self.assertEqual(tool(r, "--prefix", "I2-", "--approve", "--approver", "Dinesh", "--reason", "x").returncode, 0)
            self.assertEqual([a["task_id"] for a in ledger(r)], ["I2-001", "I2-002"])
            write_map(r, commit=OTHER)
            p = tool(r, "--tasks", "I2-001", "--approve", "--approver", "Dinesh", "--reason", "re-reviewed")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(ledger(r)[-1]["supersedes"], "A001")
            self.assertEqual(ledger(r)[-1]["approval_id"], "A003")

    def test_flags_are_shown_in_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            write_map(r, mode="MILESTONE", flags=("MILESTONE_LEVEL_ACCEPTED_AS_OF_COMMIT",))
            p = tool(r, "--tasks", "I2-001")
            self.assertIn("MILESTONE_LEVEL_ACCEPTED_AS_OF_COMMIT", p.stdout)


if __name__ == "__main__":
    unittest.main()
