"""Credit-gating regression tests for tools/consolidate_status.py.

Run: python3 -m unittest discover -s tests -p "test_*.py"
Each case builds a scratch repo with an APPROVED baseline (made by the real freeze tool), one source report and
one approval, then asserts whether the task earns credit. Every ineligible case must earn zero.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import GOOD, OTHER, SHA, make_root, row, run, write_sources  # noqa: E402


def case(ev=GOOD, task="I2-001", review="APPROVED", acc="PASS", mutate_base=None, **approval_over):
    with tempfile.TemporaryDirectory() as d:
        r = make_root(d)
        if mutate_base:
            mutate_base(r)
        write_sources(r, task, ev)
        ap = {"approval_id": "A1", "task_id": task, "baseline_version": 1,
              "source_repo": "KritvaOS/kritvaos-community", "source_commit": SHA, "review_status": review,
              "acceptance": acc, "approver": "Dinesh", "approved_at": "2026-10-11T12:00:00Z",
              "evidence_refs": ["x"], "rationale": "r"}
        ap.update(approval_over)
        (r / "v2/tracking/approvals.json").write_text(json.dumps({"authorized_approvers": ["Dinesh"], "approvals": [ap]}))
        p = run(r, "--sources-dir", str(r / "sources"))
        if p.returncode != 0:
            return p.returncode, None
        x = row(r, task)
        return 0, (x["credit"], x["credit_reason"])


class CreditGating(unittest.TestCase):
    def test_valid_pass_earns_credit_with_reason(self):
        rc, (credit, reason) = case()
        self.assertEqual((rc, credit), (0, True))
        self.assertIn("approval A1", reason)

    def test_no_credit_cases(self):
        cases = {
            "evidence result FAIL": dict(ev={**GOOD, "result": "FAIL"}),
            "evidence result null": dict(ev={**GOOD, "result": None}),
            "evidence commit mismatch": dict(ev={**GOOD, "commit": OTHER}),
            "no ci_run or sha": dict(ev={**GOOD, "ci_run": None}),
            "WAIVED": dict(acc="WAIVED"),
            "acceptance FAIL": dict(acc="FAIL"),
            "stale approval (evidence bound to another commit)": dict(source_commit=OTHER),
        }
        for name, kw in cases.items():
            with self.subTest(name):
                rc, (credit, reason) = case(**kw)
                self.assertEqual((rc, credit), (0, False))
                self.assertTrue(reason)

    def test_repo_moving_on_does_not_stale_an_approval(self):
        # report HEAD differs from the approved task commit, but the evidence is still bound to the approved commit
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            write_sources(r)
            s = json.loads((r / "sources/COMMUNITY.json").read_text())
            s["source"]["commit"] = OTHER
            (r / "sources/COMMUNITY.json").write_text(json.dumps(s))
            ev = dict(GOOD)
            s2 = json.loads((r / "sources/COMMUNITY.json").read_text())
            for x in s2["tasks"]:
                if x["task_id"] == "I2-001":
                    x["evidence"] = [ev]
            (r / "sources/COMMUNITY.json").write_text(json.dumps(s2))
            ap = {"approval_id": "A1", "task_id": "I2-001", "baseline_version": 1, "source_repo": "x",
                  "source_commit": SHA, "review_status": "APPROVED", "acceptance": "PASS", "approver": "Dinesh",
                  "approved_at": "2026-10-11T12:00:00Z", "evidence_refs": ["x"]}
            (r / "v2/tracking/approvals.json").write_text(json.dumps({"authorized_approvers": ["Dinesh"], "approvals": [ap]}))
            self.assertEqual(run(r, "--sources-dir", str(r / "sources")).returncode, 0)
            self.assertTrue(row(r, "I2-001")["credit"])

    def test_reopened_task_loses_credit(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            write_sources(r)
            s = json.loads((r / "sources/COMMUNITY.json").read_text())
            for x in s["tasks"]:
                if x["task_id"] == "I2-001":
                    x["execution"] = "IN_PROGRESS"
            (r / "sources/COMMUNITY.json").write_text(json.dumps(s))
            ap = {"approval_id": "A1", "task_id": "I2-001", "baseline_version": 1, "source_repo": "x",
                  "source_commit": SHA, "review_status": "APPROVED", "acceptance": "PASS", "approver": "Dinesh",
                  "approved_at": "2026-10-11T12:00:00Z", "evidence_refs": ["x"]}
            (r / "v2/tracking/approvals.json").write_text(json.dumps({"authorized_approvers": ["Dinesh"], "approvals": [ap]}))
            run(r, "--sources-dir", str(r / "sources"))
            self.assertFalse(row(r, "I2-001")["credit"])

    def test_invalid_approvals_fail_validation(self):
        for name, kw in {"review not approved": dict(review="PENDING"),
                         "unauthorized approver": dict(approver="Eve")}.items():
            with self.subTest(name):
                self.assertEqual(case(**kw)[0], 1)

    def test_open_gate_blocks_credit_even_with_perfect_approval(self):
        rc, (credit, reason) = case(task="I3-001")
        self.assertEqual((rc, credit), (0, False))
        self.assertIn("GATE-KOS-I3-SAFETY", reason)

    def test_closing_gate_requires_evidence_and_authorized_closer(self):
        def close(r, **over):
            p = r / "v2/tracking/baseline.json"
            b = json.loads(p.read_text())
            g = next(x for x in b["gates"] if x["gate_id"] == "GATE-KOS-I3-SAFETY")
            g.update(status="CLOSED", **over)
            p.write_text(json.dumps(b))
        # tampering after approval is itself an error (hash mismatch), so any edit must fail closed
        rc, _ = case(task="I3-001", mutate_base=lambda r: close(r, evidence_commit=SHA, closed_at="2026-10-12T00:00:00Z", closed_by="Dinesh"))
        self.assertEqual(rc, 1)

    def test_draft_baseline_gives_no_credit(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d, approve=False)
            write_sources(r)
            self.assertEqual(run(r, "--sources-dir", str(r / "sources")).returncode, 0)
            x = row(r, "I2-001")
            self.assertFalse(x["credit"])
            self.assertIn("DRAFT", x["credit_reason"])

    def test_baseline_edit_after_approval_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            p = r / "v2/tracking/baseline.json"
            b = json.loads(p.read_text())
            b["tasks"][0]["weight"] += 1
            p.write_text(json.dumps(b, indent=2) + "\n")
            write_sources(r)
            q = run(r, "--sources-dir", str(r / "sources"))
            self.assertEqual(q.returncode, 1)
            self.assertIn("baseline_sha256", q.stderr)

    def test_freeze_refuses_unauthorized_approver_and_overwrite(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d, approve=False)
            base = [sys.executable, str(r / "tools/freeze_baseline.py"), "--root", str(r), "--proposal",
                    str(r / "v2/tracking/baseline_v1_proposal.json"), "--approve", "--commit", SHA, "--reason", "t"]
            self.assertEqual(subprocess.run(base + ["--approver", "Eve"], capture_output=True).returncode, 1)
            self.assertEqual(subprocess.run(base + ["--approver", "Dinesh"], capture_output=True).returncode, 0)
            frozen = r / "v2/tracking/baselines"
            v1 = (frozen / "baseline_v1.json").read_text()
            # a second freeze makes v2 and leaves v1 untouched; an existing version is never overwritten
            self.assertEqual(subprocess.run(base + ["--approver", "Dinesh"], capture_output=True).returncode, 0)
            self.assertEqual((frozen / "baseline_v1.json").read_text(), v1)
            self.assertTrue((frozen / "baseline_v2.json").exists())
            (frozen / "baseline_v3.json").write_text("{}")
            self.assertNotEqual(subprocess.run(base + ["--approver", "Dinesh"], capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
