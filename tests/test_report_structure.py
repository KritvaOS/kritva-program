"""Report structure (D-021): separate measures, honest phase/gate/evidence wording, 17-row effort registry."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from support import ROOT, SHA, make_root, run, write_sources  # noqa: E402
import effort  # noqa: E402


def rng(lo, b, hi):
    return {"low": lo, "base": b, "high": hi, "basis": "OWNER_ESTIMATE"}


class EffortSchema(unittest.TestCase):
    def doc(self, **w):
        ws = {"workstream_id": "CORE", "completed": rng(18, 20, 24), "remaining": rng(0, 2, 3), "capability": rng(90, 95, 100),
              "confidence": "H", "assumptions": ["a"], "source_refs": ["r"], "owner_notes": ""}
        ws.update(w)
        return {"schema_version": "1.0", "estimate_version": 1, "reporting_cutoff": "2026-10-13", "unit": "person_month",
                "approval": {"status": "DRAFT", "approver": None, "approved_at": None, "commit": None, "content_sha256": None},
                "workstreams": [ws]}

    def test_capability_rules(self):
        self.assertEqual(effort.validate(self.doc(), {"CORE"}, {"Dinesh"}), [])
        self.assertTrue(effort.validate(self.doc(capability=rng(90, 95, 101)), {"CORE"}, {"Dinesh"}))
        self.assertTrue(effort.validate(self.doc(capability=rng(96, 95, 100)), {"CORE"}, {"Dinesh"}))

    def test_program_planning_total_must_add_up(self):
        d = self.doc()
        d["program_planning"] = {"completed": 70, "remaining": 175, "total": 245, "horizon_months": "10-12", "basis": "OWNER_ESTIMATE"}
        self.assertEqual(effort.validate(d, {"CORE"}, {"Dinesh"}), [])
        d["program_planning"]["total"] = 250
        self.assertTrue(effort.validate(d, {"CORE"}, {"Dinesh"}))


class BaseMethod(EffortSchema):
    def test_midpoint_label_must_be_true(self):
        ok = self.doc(completed=rng(10, 12, 14), remaining=rng(2, 3, 4), capability=rng(50, 60, 70), base_method="RANGE_MIDPOINT")
        self.assertEqual(effort.validate(ok, {"CORE"}, {"Dinesh"}), [])
        bad = self.doc(completed=rng(10, 11, 14), remaining=rng(2, 3, 4), capability=rng(50, 60, 70), base_method="RANGE_MIDPOINT")
        self.assertTrue(any("midpoint" in e for e in effort.validate(bad, {"CORE"}, {"Dinesh"})))
        agreed = self.doc(completed=rng(10, 11, 14), remaining=rng(2, 3, 4), capability=rng(50, 60, 70), base_method="AGREED_BASE")
        self.assertEqual(effort.validate(agreed, {"CORE"}, {"Dinesh"}), [])
        self.assertTrue(effort.validate(self.doc(base_method="GUESS"), {"CORE"}, {"Dinesh"}))


class RealRepoState(unittest.TestCase):
    """The committed estimate file and registry must agree and stay valid."""

    def test_committed_estimates_cover_the_agreed_17_rows_and_validate(self):
        reg = {w["id"] for w in json.loads((ROOT / "v2/tracking/workstreams.json").read_text())["workstreams"]}
        doc = json.loads((ROOT / effort.FILE).read_text())
        self.assertEqual(effort.validate(doc, reg, {"Dinesh"}), [])
        self.assertEqual(len(doc["workstreams"]), 17)
        for w in ("DEVICE_ENDPOINT", "NEXUS_EDGE", "CI_DEV_INFRA", "ELECTRICAL_POWER", "ACTUATION_CONTROLS", "MANUFACTURING_FLEET"):
            self.assertIn(w, reg)
        self.assertIn(doc["approval"]["status"], ("DRAFT", "APPROVED"))  # approval is the owner's explicit step; a hash mismatch is caught by validate()
        for w in doc["workstreams"]:
            c, r = w["completed"], w["remaining"]
            self.assertTrue(c["low"] <= c["base"] <= c["high"] and r["low"] <= r["base"] <= r["high"])


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
            self.assertIn("## Three separate measures (never blended)", view)
            self.assertIn("Accepted engineering progress", view)
            self.assertIn("Program phase (P0-P8)", view)
            self.assertIn("NOT program phase progress", view)  # tasks have no approved phase mapping
            self.assertIn("NOT BASELINED", view)
            self.assertIn("Inspected source commit", view)
            self.assertIsNotNone(c["program_status"])

    def test_two_effort_totals_are_labelled_and_reconciled(self):
        d = tempfile.TemporaryDirectory()
        r = make_root(d.name, real=False)
        e = json.loads((ROOT / effort.FILE).read_text())
        (r / effort.FILE).write_text(json.dumps(e))
        write_sources(r)
        p = run(r, "--sources-dir", str(r / "sources"))
        with d:
            self.assertEqual(p.returncode, 0, p.stderr)
            view = (r / "v2/tracking/STATUS_VIEW.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text()
            self.assertIn("Program-level rounded planning reference", view)
            self.assertIn("Sum of workstream point estimates", view)
            self.assertIn("Variance, workstream sum minus planning reference", view)
            self.assertIn("Capability % definition", view)
            self.assertIn("agreed range", view)
            self.assertIn("Registered workstreams: 20; with agreed estimates: 17", view)
            self.assertIn("NOT PLANNED yet", view)

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
