"""Gate closure ledger: closing lifts the gate block (and nothing else), refusals, re-opening, tool behaviour."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import GOOD, SHA, make_root, row, run, write_sources  # noqa: E402

GATE = "GATE-KOS-I3-SAFETY"
ARGS = ["--gates", GATE, "--closer", "Dinesh", "--evidence-commit", SHA, "--reviewer-name", "Dinesh",
        "--reviewer-role", "owner", "--findings", "none provided to Claude", "--limitations", "not independently verified",
        "--reason", "owner says review done"]


def tool(r, *args):
    return subprocess.run([sys.executable, str(r / "tools/record_gate_closure.py"), "--root", str(r), *args],
                          capture_output=True, text=True)


def approved_i3(r):
    write_sources(r, "I3-001", GOOD)
    ap = {"approval_id": "A1", "task_id": "I3-001", "baseline_version": 1, "source_repo": "KritvaOS/kritvaos-community",
          "source_commit": SHA, "review_status": "APPROVED", "acceptance": "PASS", "approver": "Dinesh",
          "approved_at": "2026-10-11T12:00:00Z", "evidence_refs": ["x"], "rationale": "r"}
    (r / "v2/tracking/approvals.json").write_text(json.dumps({"authorized_approvers": ["Dinesh"], "approvals": [ap]}))


def ledger(r):
    return json.loads((r / "v2/tracking/gate_closures.json").read_text())["closures"]


def consolidate(r):
    return run(r, "--sources-dir", str(r / "sources"))


class GateClosures(unittest.TestCase):
    def test_open_gate_blocks_then_closure_lifts_it_and_reopening_blocks_again(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            approved_i3(r)
            self.assertEqual(consolidate(r).returncode, 0)
            self.assertFalse(row(r, "I3-001")["credit"])
            self.assertIn(GATE, row(r, "I3-001")["credit_reason"])
            self.assertEqual(tool(r, *ARGS).returncode, 1 if False else 0)  # dry run
            self.assertFalse((r / "v2/tracking/gate_closures.json").exists())
            p = tool(r, *ARGS, "--approve")
            self.assertEqual(p.returncode, 0, p.stderr)
            rec = ledger(r)[0]
            self.assertEqual((rec["disposition"], rec["evidence_commit"], rec["closed_by"]), ("CLOSED", SHA, "Dinesh"))
            self.assertEqual(rec["scope_reviewed"]["milestone_ids"], ["KOS-I3"])
            self.assertEqual(consolidate(r).returncode, 0)
            x = row(r, "I3-001")
            self.assertTrue(x["credit"], x["credit_reason"])
            view = (r / "v2/tracking/STATUS_VIEW.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text()
            self.assertIn("C001", view)
            # the other safety gate is untouched: I4 tasks stay blocked
            gates = {g["gate_id"]: g["status"] for g in json.loads((r / "v2/tracking/consolidated_status.json").read_text())["gates"]}
            self.assertEqual((gates[GATE], gates["GATE-KOS-I4-SAFETY"]), ("CLOSED", "OPEN"))
            # re-open
            p = tool(r, "--gates", GATE, "--closer", "Dinesh", "--reviewer-name", "Dinesh", "--reviewer-role", "owner",
                     "--findings", "found an issue", "--limitations", "none", "--reason", "defect found", "--reopen", "--approve")
            self.assertEqual(p.returncode, 0, p.stderr)
            consolidate(r)
            self.assertFalse(row(r, "I3-001")["credit"])

    def test_closure_does_not_create_credit_without_an_approval(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            write_sources(r, "I3-001", GOOD)
            self.assertEqual(tool(r, *ARGS, "--approve").returncode, 0)
            consolidate(r)
            self.assertFalse(row(r, "I3-001")["credit"])
            self.assertIn("no central approval", row(r, "I3-001")["credit_reason"])

    def test_tool_refusals(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            self.assertEqual(tool(r, "--gates", "GATE-NOPE", "--evidence-commit", SHA).returncode, 1)
            self.assertEqual(tool(r, "--gates", GATE, "--evidence-commit", "abc").returncode, 1)  # short sha
            bad = [a for a in ARGS]
            bad[bad.index("Dinesh")] = "Eve"
            self.assertEqual(tool(r, *bad, "--approve").returncode, 1)  # unauthorized closer
            no_findings = ARGS[:ARGS.index("--findings")] + ARGS[ARGS.index("--limitations"):]
            self.assertEqual(tool(r, *no_findings, "--approve").returncode, 1)  # findings required
            self.assertEqual(tool(r, "--gates", GATE, "--reopen").returncode, 1)  # not closed yet
            self.assertFalse((r / "v2/tracking/gate_closures.json").exists())
            self.assertEqual(tool(r, *ARGS, "--approve").returncode, 0)
            self.assertEqual(tool(r, *ARGS, "--approve").returncode, 1)  # already closed
            self.assertEqual(len(ledger(r)), 1)

    def test_hand_edited_bad_records_are_validation_errors(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            approved_i3(r)
            base = {"closure_id": "C001", "gate_id": GATE, "disposition": "CLOSED", "evidence_commit": SHA,
                    "closed_at": "2026-10-13T00:00:00Z", "closed_by": "Dinesh",
                    "reviewer": {"name": "D", "role": "owner"}, "scope_reviewed": {"milestone_ids": ["KOS-I3"], "task_ids": []},
                    "findings": "f", "limitations": "l", "rationale": "r"}
            cases = {"unauthorized": dict(base, closed_by="Eve"), "no commit": dict(base, evidence_commit=None),
                     "narrow scope": dict(base, scope_reviewed={"milestone_ids": [], "task_ids": []}),
                     "blank findings": dict(base, findings=" "), "unknown gate": dict(base, gate_id="GATE-X"),
                     "no reviewer role": dict(base, reviewer={"name": "D", "role": ""}),
                     "extra key": dict(base, sneaky=1)}
            for label, rec in cases.items():
                (r / "v2/tracking/gate_closures.json").write_text(json.dumps({"closures": [rec]}))
                p = consolidate(r)
                self.assertEqual(p.returncode, 1, label)
                self.assertFalse(row(r, "I3-001")["credit"], label)


if __name__ == "__main__":
    unittest.main()
