"""Credit-gating regression tests for tools/consolidate_status.py.

Run: python3 -m unittest tests/test_credit_gating.py
Each case builds a scratch copy of the repo with weighted tasks, one source
report, and one approval, then asserts whether task I2-001 earns credit.
"""
import copy, datetime, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA, OTHER = "a" * 40, "b" * 40
GOOD = {"type": "software", "uri": "u", "description": "d", "commit": SHA,
        "ci_run": "https://example.invalid/run/1", "report_sha256": None, "result": "PASS"}


def run_case(ev, review="APPROVED", acc="PASS", **approval_over):
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        for sub in ("tools", "schema", "v2", "examples"):
            shutil.copytree(ROOT / sub, r / sub)
        base = json.loads((r / "v2/tracking/baseline.json").read_text())
        for t in base["tasks"]:
            t["weight"] = 1
        base["baseline_approved"] = True
        (r / "v2/tracking/baseline.json").write_text(json.dumps(base))
        src = json.loads((r / "examples/sources/COMMUNITY.example.json").read_text())
        src["source"]["commit"] = SHA
        src["updated_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for t in src["tasks"]:
            if t["task_id"] == "I2-001":
                t["evidence"] = [copy.deepcopy(ev)]
        (r / "sources").mkdir()
        (r / "sources/COMMUNITY.json").write_text(json.dumps(src))
        ap = {"approval_id": "A1", "task_id": "I2-001", "baseline_version": 0,
              "source_repo": "KritvaOS/kritvaos-community", "source_commit": SHA,
              "review_status": review, "acceptance": acc, "approver": "Dinesh",
              "approved_at": "2026-10-11T12:00:00Z", "evidence_refs": ["x"], "rationale": "r"}
        ap.update(approval_over)
        (r / "v2/tracking/approvals.json").write_text(json.dumps(
            {"authorized_approvers": ["Dinesh"], "approvals": [ap]}))
        p = subprocess.run([sys.executable, str(r / "tools/consolidate_status.py"),
                            "--root", str(r), "--sources-dir", str(r / "sources")],
                           capture_output=True, text=True)
        if p.returncode != 0:
            return p.returncode, None
        c = json.loads((r / "v2/tracking/consolidated_status.json").read_text())
        return 0, next(x["credit"] for x in c["tasks"] if x["task_id"] == "I2-001")


class CreditGating(unittest.TestCase):
    def test_valid_pass_earns_credit(self):
        self.assertEqual(run_case(GOOD), (0, True))

    def test_no_credit_cases(self):
        cases = {
            "evidence result FAIL": dict(ev={**GOOD, "result": "FAIL"}),
            "evidence result null": dict(ev={**GOOD, "result": None}),
            "evidence commit mismatch": dict(ev={**GOOD, "commit": OTHER}),
            "no ci_run or sha": dict(ev={**GOOD, "ci_run": None}),
            "WAIVED": dict(ev=GOOD, acc="WAIVED"),
            "acceptance FAIL": dict(ev=GOOD, acc="FAIL"),
            "stale approval": dict(ev=GOOD, source_commit=OTHER),
        }
        for name, kw in cases.items():
            with self.subTest(name):
                self.assertEqual(run_case(**kw), (0, False))

    def test_invalid_approvals_fail_validation(self):
        for name, kw in {"review not approved": dict(ev=GOOD, review="PENDING"),
                         "unauthorized approver": dict(ev=GOOD, approver="Eve")}.items():
            with self.subTest(name):
                rc, _ = run_case(**kw)
                self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
