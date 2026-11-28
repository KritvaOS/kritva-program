"""End-to-end tests for sources.json "currency_rule" (D-164): the age rule (default) and the commit-gap rule."""
import datetime
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import GOOD, SHA, fresh_ts, make_root, row, run, write_sources  # noqa: E402


def old_ts(days):
    return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def build(d, rule=None, affected=None, manifest=True, age_days=30, basis="task_scopes"):
    r = make_root(d)
    write_sources(r, "I2-001", GOOD)
    s = json.loads((r / "sources/COMMUNITY.json").read_text())
    s["updated_at"] = old_ts(age_days)
    (r / "sources/COMMUNITY.json").write_text(json.dumps(s))
    cfgp = r / "v2/tracking/sources.json"
    cfg = json.loads(cfgp.read_text())
    if rule:
        cfg["currency_rule"] = rule
    cfgp.write_text(json.dumps(cfg))
    ap = {"approval_id": "A1", "task_id": "I2-001", "baseline_version": 1, "source_repo": "KritvaOS/kritvaos-community",
          "source_commit": SHA, "review_status": "APPROVED", "acceptance": "PASS", "approver": "Dinesh",
          "approved_at": "2026-10-11T12:00:00Z", "evidence_refs": ["x"], "rationale": "r"}
    (r / "v2/tracking/approvals.json").write_text(json.dumps({"authorized_approvers": ["Dinesh"], "approvals": [ap]}))
    if manifest:
        entry = {"repo": "KritvaOS/kritvaos-community", "state": "FETCHED", "fetched_at": fresh_ts(), "report_source_commit": SHA,
                 "impact": {"basis": basis, "affected": {t: {"state": "AFFECTED"} for t in (affected or [])}}}
        (r / "sources/MANIFEST.json").write_text(json.dumps({"warn_hours": 24, "stale_hours": 72, "sources": {"COMMUNITY": entry}}))
    return r


def result(r):
    p = run(r, "--sources-dir", str(r / "sources"))
    return p, (row(r, "I2-001") if p.returncode == 0 else None)


class CurrencyRule(unittest.TestCase):
    def test_age_rule_is_the_default_and_expires_an_old_report(self):
        with tempfile.TemporaryDirectory() as d:
            p, x = result(build(d))
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertFalse(x["credit"])

    def test_commit_gap_keeps_credit_for_an_old_report_with_nothing_affected(self):
        with tempfile.TemporaryDirectory() as d:
            r = build(d, rule="commit-gap")
            p, x = result(r)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertTrue(x["credit"], x["credit_reason"])
            c = json.loads((r / "v2/tracking/consolidated_status.json").read_text())
            self.assertEqual(c["currency_rule"], "commit-gap")
            self.assertNotIn("is 30 days old", p.stderr)

    def test_commit_gap_withholds_credit_for_an_affected_task(self):
        with tempfile.TemporaryDirectory() as d:
            p, x = result(build(d, rule="commit-gap", affected=["I2-001"]))
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertFalse(x["credit"])
            self.assertIn("changed since the report", p.stderr)

    def test_commit_gap_fails_closed_without_a_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            p, x = result(build(d, rule="commit-gap", manifest=False))
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertFalse(x["credit"])
            self.assertIn("no fetched manifest entry", p.stderr)

    def test_commit_gap_fails_closed_without_impact_data(self):
        with tempfile.TemporaryDirectory() as d:
            p, x = result(build(d, rule="commit-gap", basis="UNAVAILABLE"))
            self.assertFalse(x["credit"])
            self.assertIn("no impact data", p.stderr)

    def test_age_warning_is_advisory_only(self):
        with tempfile.TemporaryDirectory() as d:
            p, x = result(build(d, rule="commit-gap", age_days=90))
            self.assertTrue(x["credit"], x["credit_reason"])
            self.assertIn("90 days old (advisory only", p.stderr)

    def test_unknown_rule_is_a_config_error(self):
        with tempfile.TemporaryDirectory() as d:
            p, _ = result(build(d, rule="whenever"))
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("currency_rule", p.stderr)

    def test_commit_gap_with_fetch_is_a_config_error(self):
        with tempfile.TemporaryDirectory() as d:
            r = build(d, rule="commit-gap")
            import subprocess
            p = subprocess.run([sys.executable, str(r / "tools/consolidate_status.py"), "--root", str(r), "--fetch"],
                               capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("needs --sources-dir", p.stderr)


if __name__ == "__main__":
    unittest.main()
