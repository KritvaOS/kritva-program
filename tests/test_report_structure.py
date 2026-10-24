"""Report structure (D-021): separate measures, honest phase/gate/evidence wording, no effort estimates."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from support import ROOT, SHA, make_root, run, write_sources  # noqa: E402


class Rendering(unittest.TestCase):
    def build(self):
        d = tempfile.TemporaryDirectory()
        r = make_root(d.name)
        write_sources(r)
        p = run(r, "--sources-dir", str(r / "sources"))
        self.assertEqual(p.returncode, 0, p.stderr)
        return d, r, (r / "v2/tracking/STATUS_VIEW.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text(), json.loads((r / "v2/tracking/consolidated_status.json").read_text())

    def test_three_measures_and_phase_caveat(self):
        d, r, view, c = self.build()
        with d:
            self.assertIn("## Measures (never blended)", view)
            self.assertIn("Accepted engineering progress", view)
            self.assertIn("Program phase (P0-P8)", view)
            self.assertIn("NOT program phase progress", view)  # tasks have no approved phase mapping
            self.assertIn("NOT BASELINED", view)
            self.assertIn("Inspected source commit", view)
            self.assertIsNotNone(c["program_status"])


    def test_gates_show_frozen_and_effective_state(self):
        d, r, view, c = self.build()
        with d:
            self.assertIn("Frozen baseline state", view)
            for g in c["gates"]:
                self.assertEqual(g["frozen_status"], "OPEN")  # a scratch repo has no closures
                self.assertEqual(g["status"], "OPEN")

    def test_evidence_health_explains_reason(self):
        d, r, view, c = self.build()
        with d:
            states = {t["evidence_state"] for t in c["tasks"]}
            self.assertTrue(states <= {"NO_REPORT", "NO_EVIDENCE_REPORTED", "REPORTED_AWAITING_APPROVAL", "BOUND_TO_OTHER_COMMIT",
                                       "NOT_VERIFIABLE", "RUN_NOT_VERIFIED", "VERIFIED"})
            self.assertNotIn("no verified evidence", view)
            self.assertTrue(any("no current report" in x or "reports no commit-bound" in x for x in c["evidence_health"]))


if __name__ == "__main__":
    unittest.main()


class SourceFreshness(unittest.TestCase):
    def test_section_rendered_from_manifest_and_absent_without(self):
        import tempfile
        from support import make_root, run, write_sources
        with tempfile.TemporaryDirectory() as t:
            r = make_root(t + "/kp")
            write_sources(r)
            run(r, "--sources-dir", str(r / "sources"), "--now", "2026-10-15T12:00:00Z")
            self.assertNotIn("## Source freshness", (r / "v2/tracking/STATUS_VIEW.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text())
            m = {"warn_hours": 24, "stale_hours": 72, "sources": {
                "COMMUNITY": {"repo": "KritvaOS/kritvaos-community", "state": "FETCHED", "fetched_at": "2026-10-15T00:00:00Z",
                              "fetched_head": "e" * 40, "report_source_commit": "d" * 40, "relation": "AHEAD",
                              "ahead_by": 1, "status_only": True, "gap_kind": "STATUS_ONLY"},
                "CORE": {"repo": "KritvaOS/kritva-core", "state": "FETCH_FAILED"}}}
            (r / "sources/MANIFEST.json").write_text(json.dumps(m))
            p = run(r, "--sources-dir", str(r / "sources"), "--now", "2026-10-15T12:00:00Z")
            v = (r / "v2/tracking/STATUS_VIEW.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text()
            self.assertIn("## Source freshness", v)
            self.assertIn("| COMMUNITY | FRESH |", v)
            self.assertIn("STATUS_ONLY", v)
            self.assertIn("| CORE | FETCH_FAILED |", v)
            self.assertEqual(run(r, "--sources-dir", str(r / "sources"), "--check").returncode, 0, p.stderr)
