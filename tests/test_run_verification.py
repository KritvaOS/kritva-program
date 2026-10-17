"""CI run verification (--verify-runs, fake `gh`) and evidence-class reporting in tools/consolidate_status.py."""
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import GOOD, OTHER, SHA, make_root, row, run, write_sources  # noqa: E402

REPO = "KritvaOS/kritvaos-community"
RID = "123"
FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
m = json.load(open(os.environ["GH_FAKE"]))
path = sys.argv[2]
if path in m:
    print(json.dumps(m[path])); sys.exit(0)
sys.stderr.write("404 " + path); sys.exit(1)
"""


def ev(desc="KritvaOS CI run 123 PASS"):
    return dict(GOOD, ci_run=RID, description=desc)


def gh_map(head=SHA, conclusion="success", status="completed", jobs=("success",), repo=REPO, name="KritvaOS CI"):
    return {f"repos/{REPO}/actions/runs/{RID}": {"head_sha": head, "conclusion": conclusion, "status": status,
                                               "name": name, "repository": {"full_name": repo}},
            f"repos/{REPO}/actions/runs/{RID}/jobs?per_page=100": {"jobs": [{"name": f"j{i}", "conclusion": c}
                                                                         for i, c in enumerate(jobs)]}}


def setup(r, require=True, approve=True, mode="MILESTONE"):
    cfgp = r / "v2/tracking/sources.json"
    cfg = json.loads(cfgp.read_text())
    cfg["require_run_verification"] = require
    cfgp.write_text(json.dumps(cfg))
    write_sources(r, "I2-001", ev())
    if approve:
        ap = {"approval_id": "A1", "task_id": "I2-001", "baseline_version": 1, "source_repo": REPO,
              "source_commit": SHA, "review_status": "APPROVED", "acceptance": "PASS", "approver": "Dinesh",
              "approved_at": "2026-10-11T12:00:00Z", "evidence_refs": ["x"], "rationale": "r"}
        (r / "v2/tracking/approvals.json").write_text(json.dumps({"authorized_approvers": ["Dinesh"], "approvals": [ap]}))
    (r / "v2/tracking/evidence_map_proposal.json").write_text(json.dumps({"rows": [
        {"task_id": "I2-001", "mode": mode, "task_commit": OTHER, "evidence": {"commit": SHA}}]}))


def go(r, mapping=None, *flags):
    env = dict(os.environ)
    if mapping is not None:
        b = r / "bin"
        b.mkdir(exist_ok=True)
        (b / "gh").write_text(FAKE_GH)
        (b / "gh").chmod((b / "gh").stat().st_mode | stat.S_IEXEC)
        (b / "map.json").write_text(json.dumps(mapping))
        env.update(PATH=f"{b}:{os.environ['PATH']}", GH_FAKE=str(b / "map.json"))
    return subprocess.run([sys.executable, str(r / "tools/consolidate_status.py"), "--root", str(r),
                           "--sources-dir", str(r / "sources"), *flags], capture_output=True, text=True, env=env)


class RunVerification(unittest.TestCase):
    def case(self, mapping, **kw):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            setup(r, **kw)
            p = go(r, mapping, "--verify-runs")
            self.assertEqual(p.returncode, 0, p.stderr)
            x = row(r, "I2-001")
            return x["credit"], x["credit_reason"], x

    def test_verified_run_earns_credit_and_is_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            setup(r)
            self.assertEqual(go(r, gh_map(), "--verify-runs").returncode, 0)
            x = row(r, "I2-001")
            self.assertTrue(x["credit"], x["credit_reason"])
            self.assertIs(x["run_verified"], True)
            rec = json.loads((r / "v2/tracking/run_verification.json").read_text())["runs"][f"{REPO}#{RID}"]
            self.assertEqual((rec["head_sha"], rec["conclusion"], rec["state"]), (SHA, "success", "RETRIEVED"))
            self.assertTrue(rec["retrieved_at"].endswith("Z"))
            # later runs without --verify-runs reuse the recorded facts
            self.assertEqual(go(r).returncode, 0)
            self.assertTrue(row(r, "I2-001")["credit"])

    def test_policy_requires_verification_before_credit(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            setup(r)
            self.assertEqual(go(r).returncode, 0)  # no --verify-runs, no record
            x = row(r, "I2-001")
            self.assertFalse(x["credit"])
            self.assertIn("not verified against GitHub", x["credit_reason"])

    def test_policy_off_keeps_old_behaviour(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            setup(r, require=False)
            self.assertEqual(go(r).returncode, 0)
            self.assertTrue(row(r, "I2-001")["credit"])

    def test_bad_runs_earn_no_credit(self):
        bad = {"wrong head": gh_map(head=OTHER), "failed run": gh_map(conclusion="failure"),
               "still running": gh_map(status="in_progress", conclusion=None),
               "a job failed": gh_map(jobs=("success", "failure")), "no jobs": gh_map(jobs=()),
               "wrong repo": gh_map(repo="Other/repo"), "wrong workflow": gh_map(name="Some Other Workflow")}
        for label, m in bad.items():
            credit, reason, _ = self.case(m)
            self.assertFalse(credit, label)
            self.assertIn("not verified against GitHub", reason, label)

    def test_github_unavailable_means_no_credit_but_keeps_earlier_record(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            setup(r)
            self.assertEqual(go(r, gh_map(), "--verify-runs").returncode, 0)
            first = (r / "v2/tracking/run_verification.json").read_text()
            p = go(r, {}, "--verify-runs")  # every lookup 404s
            self.assertIn("previous record kept", p.stderr)
            self.assertEqual((r / "v2/tracking/run_verification.json").read_text(), first)
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            setup(r)
            go(r, {}, "--verify-runs")
            x = row(r, "I2-001")
            self.assertFalse(x["credit"])
            self.assertIn("not verified against GitHub", x["credit_reason"])

    def test_evidence_class_and_qualification_are_reported(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            setup(r, mode="MILESTONE")
            go(r, gh_map(), "--verify-runs")
            x = row(r, "I2-001")
            self.assertEqual((x["evidence_class"], x["tested_commit"], x["task_commit"]), ("MILESTONE", SHA, OTHER))
            view = (r / "v2/tracking/STATUS_VIEW.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text()
            self.assertIn("Evidence classes of credited tasks: MILESTONE 1", view)
            self.assertIn("Evidence qualification", view)
            self.assertIn("with the CI run confirmed against GitHub", view)
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            setup(r, mode="OWN")
            go(r, gh_map(), "--verify-runs")
            view = (r / "v2/tracking/STATUS_VIEW.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text()
            self.assertIn("OWN 1", view)
            self.assertNotIn("Evidence qualification", view)

    def test_unlisted_class_is_unspecified_not_guessed(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            setup(r)
            (r / "v2/tracking/evidence_map_proposal.json").write_text(json.dumps({"rows": []}))
            go(r, gh_map(), "--verify-runs")
            self.assertEqual(row(r, "I2-001")["evidence_class"], "UNSPECIFIED")

    def test_check_mode_does_not_write_the_record(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            setup(r)
            go(r, gh_map(), "--verify-runs", "--check")
            self.assertFalse((r / "v2/tracking/run_verification.json").exists())


if __name__ == "__main__":
    unittest.main()
