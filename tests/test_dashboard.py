#!/usr/bin/env python3
"""Tests for tools/dashboard.py (display only)."""
import copy, re, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import dashboard as D  # noqa: E402

PHASES = [[f"P{i}", n] for i, n in enumerate(
    ["FOUNDATION", "STUDIO", "BUILD & ARTIFACT", "CONTROL PLANE", "BOOKING & COMMERCIAL", "EXECUTION",
     "LAB & ROBOT", "LIVE & RESULTS", "PRODUCTION"])]


def doc():
    return {"generated_at": "2026-10-17T10:00:00Z",
            "progress": {"accepted_progress_pct": 50.0, "basis": "10/20 weight (x)"},
            "by_workstream": {"A": {"accepted_weight": 10, "weight": 12, "credited": 2, "tasks": 3},
                              "B": {"accepted_weight": 0, "weight": 8, "credited": 0, "tasks": 2}},
            "effort": {"program_planning": {"completed": 70, "remaining": 175, "total": 245, "horizon_months": "10-12"}},
            "readiness": {"report_due": "2026-11-14", "target_date": "2026-11-15", "repos": [
                {"repo": "o/a", "readiness": "READY", "blocking": [], "attested": ["branch_protection"]},
                {"repo": "o/b", "readiness": "NOT_READY", "blocking": ["contract_pin"], "attested": []}]}}


class T(unittest.TestCase):
    def text(self, c, phases=PHASES):
        return "\n".join(D.render_lines(c, phases))

    def test_phase_names_come_from_the_plan(self):
        self.assertEqual(D.phase_names(ROOT), PHASES)

    def test_phase_names_empty_when_missing(self):
        self.assertEqual(D.phase_names(ROOT / "nope"), [])

    def test_clean_data_reconciles(self):
        self.assertEqual(D.check(doc()), [])

    def test_workstream_mismatch_is_reported_and_chart_withheld(self):
        c = doc(); c["by_workstream"]["A"]["accepted_weight"] = 9
        self.assertTrue(D.check(c))
        t = self.text(c)
        self.assertIn("NOT_VERIFIED", t)
        self.assertNotIn("xychart-beta", t)

    def test_effort_mismatch_withholds_effort(self):
        c = doc(); c["effort"]["program_planning"]["total"] = 999
        t = self.text(c)
        self.assertIn("NOT_VERIFIED", t)
        self.assertNotIn("~70 PM done", t)

    def test_missing_inputs_are_not_verified_not_silent(self):
        c = doc(); c.pop("effort"); c.pop("readiness"); c["by_workstream"] = {}
        t = self.text(c, [])
        self.assertGreaterEqual(t.count("NOT_VERIFIED"), 4)

    def test_every_progress_figure_shows_numerator_and_denominator(self):
        t = self.text(doc())
        self.assertIn("10/12 = 83.3%", t)
        self.assertIn("0/8 = 0.0%", t)
        self.assertIn("10/20 weight", t)

    def test_gantt_has_only_recorded_dates_and_no_durations(self):
        t = self.text(doc())
        g = t[t.index("gantt"):]
        g = g[:g.index("```")]
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", g)
        self.assertEqual(sorted(set(dates)), ["2026-10-17", "2026-11-14", "2026-11-15"])
        self.assertEqual(g.count(":milestone"), 3)
        self.assertNotIn("P0", g)

    def test_phase_sequence_has_no_dates(self):
        t = self.text(doc())
        s = t[t.index("### Phase sequence"):]
        s = s[:s.index("Order only")]
        self.assertFalse(re.search(r"\d{4}-\d{2}-\d{2}|%|\bdays?\b", s))
        self.assertIn("P8", s)

    def test_mermaid_fences_are_balanced(self):
        t = self.text(doc())
        self.assertEqual(t.count("```") % 2, 0)

    def test_no_blended_health_figure(self):
        t = self.text(doc()).lower()
        self.assertNotIn("overall health", t)
        self.assertIn("never combined", t)

    def test_committed_view_has_the_dashboard(self):
        v = (ROOT / "v2" / "tracking" / "STATUS_VIEW.md").read_text(encoding="utf-8")
        self.assertIn("## At a glance", v)
        self.assertEqual(v.count("```") % 2, 0)


if __name__ == "__main__":
    unittest.main()
