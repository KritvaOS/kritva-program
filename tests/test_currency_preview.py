"""Tests for the report-only commit-gap currency preview in tools/consolidate_status.py (D-164 step 5). No network."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import consolidate_status as cs  # noqa: E402

SHA = "a" * 40


def doc(ws, ids):
    ev = [{"type": "software", "uri": "u", "description": "d", "commit": SHA, "ci_run": "https://x/runs/1", "result": "PASS"}]
    return {"workstream_id": ws, "repo": f"KritvaOS/{ws.lower()}", "source": {"commit": SHA}, "updated_at": "2026-11-28T00:00:00Z",
            "tasks": [{"task_id": i, "execution": "COMPLETE", "git_sync": "COMMITTED", "readiness": "READY", "evidence": ev} for i in ids]}


BASE = {"baseline_approved": True, "gates": [], "tasks": [
    {"id": "A-1", "workstream_id": "CORE", "weight": 2}, {"id": "A-2", "workstream_id": "CORE", "weight": 2},
    {"id": "S-1", "workstream_id": "SENSE", "weight": 2}]}
EFFECTIVE = {t: {"acceptance": "PASS", "review_status": "APPROVED", "source_commit": SHA, "approval_id": f"AP-{t}"}
             for t in ("A-1", "A-2", "S-1")}


def entry(ws, affected=None, basis="task_scopes", commit=SHA, state="FETCHED"):
    imp = {"basis": basis, "affected": {t: {"state": "AFFECTED"} for t in (affected or [])}}
    return {"state": state, "report_source_commit": commit, "impact": imp}


class Preview(unittest.TestCase):
    def all_valid(self):
        return {"CORE": ("core", doc("CORE", ["A-1", "A-2"])), "SENSE": ("sense", doc("SENSE", ["S-1"]))}

    def old(self, reports):
        tasks, prog, _ = cs.compute(BASE, reports, EFFECTIVE, {})
        return tasks, prog

    def preview(self, manifest, old_reports, old_states):
        tasks, prog = self.old(old_reports)
        return cs.currency_preview(BASE, self.all_valid(), manifest, EFFECTIVE, {}, None, False, None, tasks, prog, old_states)

    def test_stale_report_regains_credit_except_affected_task(self):
        av = self.all_valid()
        p = self.preview({"sources": {"CORE": entry("CORE", ["A-1"]), "SENSE": entry("SENSE")}}, {"SENSE": av["SENSE"]},
                         {"CORE": "STALE", "SENSE": "OK"})
        self.assertEqual(p["old_progress"]["accepted_progress_pct"], 33.33)
        self.assertEqual(p["new_progress"]["accepted_progress_pct"], 66.67)
        self.assertEqual(p["gained"], ["A-2"])
        self.assertEqual(p["lost"], [])
        rows = {r["id"]: r for r in p["workstreams"]}
        self.assertEqual((rows["CORE"]["state"], rows["CORE"]["affected"]), ("PARTIAL", ["A-1"]))
        self.assertEqual(rows["SENSE"]["state"], "CURRENT")
        self.assertEqual(rows["CORE"]["old_state"], "STALE")

    def test_fresh_report_with_affected_task_loses_credit(self):
        av = self.all_valid()
        p = self.preview({"sources": {"CORE": entry("CORE", ["A-1", "A-2"]), "SENSE": entry("SENSE")}}, av, {"CORE": "OK", "SENSE": "OK"})
        self.assertEqual(p["lost"], ["A-1", "A-2"])
        self.assertEqual(p["new_progress"]["accepted_progress_pct"], 33.33)

    def test_fails_closed_without_usable_impact_data(self):
        for bad in (entry("CORE", basis="UNAVAILABLE"), entry("CORE", commit="b" * 40), entry("CORE", state="FETCH_FAILED"), None):
            m = {"sources": {"SENSE": entry("SENSE")}}
            if bad is not None:
                m["sources"]["CORE"] = bad
            p = self.preview(m, {}, {"CORE": "STALE", "SENSE": "STALE"})
            rows = {r["id"]: r for r in p["workstreams"]}
            self.assertEqual(rows["CORE"]["state"], "EXCLUDED")
            self.assertEqual(p["new_progress"]["accepted_progress_pct"], 33.33)  # only SENSE earns credit

    def test_missing_manifest_excludes_everything(self):
        p = self.preview({}, {}, {})
        self.assertEqual({r["state"] for r in p["workstreams"]}, {"EXCLUDED"})
        self.assertEqual(p["new_progress"]["accepted_progress_pct"], 0.0)

    def test_inputs_are_not_modified(self):
        av = self.all_valid()
        before = len(av["CORE"][1]["tasks"])
        cs.new_rule_reports(av, {"sources": {"CORE": entry("CORE", ["A-1"])}})
        self.assertEqual(len(av["CORE"][1]["tasks"]), before)

    def test_render_mentions_both_rules(self):
        av = self.all_valid()
        p = self.preview({"sources": {"CORE": entry("CORE", ["A-1"]), "SENSE": entry("SENSE")}}, {"SENSE": av["SENSE"]},
                         {"CORE": "STALE", "SENSE": "OK"})
        text = cs.render_preview(p)
        self.assertIn("14-day rule", text)
        self.assertIn("commit-gap", text)
        self.assertIn("gained credit under commit-gap: A-2", text)


if __name__ == "__main__":
    unittest.main()
