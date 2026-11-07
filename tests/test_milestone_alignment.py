#!/usr/bin/env python3
"""Tests for the milestone alignment report in tools/consolidate_status.py (MA-3; D-093, D-094, D-095)."""
import copy, json, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import consolidate_status as CS  # noqa: E402
import planning as P  # noqa: E402


def pdata():
    return P.load(ROOT)


def base_and_rollup(extra_ms=(), extra_tasks=()):
    hist = [("KF-CORE-R10", "CORE"), ("KOS-I3", "COMMUNITY"), ("KOS-I4", "COMMUNITY"), ("KRP-ENG", "CI_DEV_INFRA")]
    ms = [{"id": "KOS-I2", "workstream_id": "COMMUNITY"}, {"id": "V2-M1-SENSE-001", "workstream_id": "SENSE"}] + \
         [{"id": i, "workstream_id": w} for i, w in hist] + list(extra_ms)
    tasks = [{"id": "T1", "milestone_id": "KOS-I2", "workstream_id": "COMMUNITY"},
             {"id": "T2", "milestone_id": "V2-M1-SENSE-001", "workstream_id": "SENSE"}] + list(extra_tasks)
    by = {m["id"]: {"tasks": 1, "complete": 1, "credited": 1, "weight": 4, "accepted_weight": 4, "weighted": True} for m in ms}
    return {"milestones": ms, "tasks": tasks}, by


class Alignment(unittest.TestCase):
    def run_al(self, base, by, pd=None):
        return CS.milestone_alignment(base, pd or pdata(), by)

    def test_clean_join(self):
        base, by = base_and_rollup()
        rows, errs, warns = self.run_al(base, by)
        self.assertEqual((errs, warns), ([], []))
        r = {x["milestone"]: x for x in rows}
        self.assertEqual(r["KOS-I2"]["class"], "PRE_V2")
        self.assertEqual(r["KOS-I2"]["program_milestone"], "-")
        self.assertEqual(r["V2-M1-SENSE-001"]["class"], "V2_REPO")
        self.assertEqual(r["V2-M1-SENSE-001"]["program_milestone"], "V2-M1")
        self.assertEqual(r["V2-M1-SENSE-001"]["closure"], "none")

    def test_planned_repo_milestones_have_zero_tasks_and_no_warning(self):
        base, by = base_and_rollup()
        rows, errs, warns = self.run_al(base, by)
        planned = [x for x in rows if x["class"] == "V2_REPO" and x["milestone"] != "V2-M1-SENSE-001"]
        self.assertEqual(len(planned), len(pdata()["milestones"]["repo_milestones"]) - 1)
        self.assertTrue(all(x["tasks"] == 0 and x["credited"] == 0 and x["class"] == "V2_REPO" for x in planned))
        self.assertEqual(warns, [])

    def test_unknown_v2_baseline_milestone_is_error(self):
        base, by = base_and_rollup(extra_ms=[{"id": "V2-M9-SENSE-009", "workstream_id": "SENSE"}])
        rows, errs, _ = self.run_al(base, by)
        self.assertTrue(any("V2-M9-SENSE-009" in e and "repo_milestones" in e for e in errs))
        self.assertEqual({x["milestone"]: x for x in rows}["V2-M9-SENSE-009"]["class"], "UNKNOWN")

    def test_unclassified_historical_milestone_is_warning(self):
        base, by = base_and_rollup(extra_ms=[{"id": "OLD-X1", "workstream_id": "CORE"}])
        rows, errs, warns = self.run_al(base, by)
        self.assertEqual(errs, [])
        self.assertTrue(any("OLD-X1" in w and "UNCLASSIFIED" in w for w in warns))
        self.assertEqual({x["milestone"]: x for x in rows}["OLD-X1"]["class"], "UNCLASSIFIED")

    def test_historical_key_not_in_baseline_is_warning(self):
        base, by = base_and_rollup()
        base["milestones"] = [m for m in base["milestones"] if m["id"] != "KOS-I2"]
        base["tasks"] = [t for t in base["tasks"] if t["milestone_id"] != "KOS-I2"]
        _, errs, warns = self.run_al(base, by)
        self.assertEqual(errs, [])
        self.assertTrue(any("KOS-I2" in w and "not a baseline milestone" in w for w in warns))

    def test_task_workstream_mismatch_is_error(self):
        base, by = base_and_rollup(extra_tasks=[{"id": "T3", "milestone_id": "KOS-I2", "workstream_id": "CORE"}])
        _, errs, _ = self.run_al(base, by)
        self.assertTrue(any("T3" in e and "does not match milestone KOS-I2" in e for e in errs))

    def test_task_with_unknown_milestone_is_error(self):
        base, by = base_and_rollup(extra_tasks=[{"id": "T4", "milestone_id": "NOPE", "workstream_id": "CORE"}])
        _, errs, _ = self.run_al(base, by)
        self.assertTrue(any("T4" in e and "NOPE" in e for e in errs))

    def test_milestone_workstream_must_match_repo_workstream(self):
        base, by = base_and_rollup()
        base["milestones"][1]["workstream_id"] = "CORE"
        base["tasks"][1]["workstream_id"] = "CORE"
        _, errs, _ = self.run_al(base, by)
        self.assertTrue(any("V2-M1-SENSE-001" in e and "does not match repo SENSE" in e for e in errs))

    def test_does_not_mutate_inputs_and_is_deterministic(self):
        base, by = base_and_rollup()
        pd = pdata()
        b0, y0, p0 = copy.deepcopy(base), copy.deepcopy(by), copy.deepcopy(pd)
        a = CS.milestone_alignment(base, pd, by)
        b = CS.milestone_alignment(base, pd, by)
        self.assertEqual(a, b)
        self.assertEqual((base, by, pd), (b0, y0, p0))


class Committed(unittest.TestCase):
    def setUp(self):
        self.c = json.loads((ROOT / "v2/tracking/consolidated_status.json").read_text())
        self.detail = (ROOT / "v2/tracking/STATUS_DETAIL.md").read_text()

    def test_historical_rows_carry_baseline_weights(self):
        r = {x["milestone"]: x for x in self.c["milestone_alignment"]}
        got = {k: (r[k]["class"], r[k]["tasks"], r[k]["weight"]) for k in ("KF-CORE-R10", "KOS-I2", "KOS-I3", "KOS-I4", "KRP-ENG")}
        self.assertEqual(got, {"KF-CORE-R10": ("PRE_V2", 9, 30), "KOS-I2": ("PRE_V2", 6, 18), "KOS-I3": ("PRE_V2", 7, 23),
                               "KOS-I4": ("PRE_V2", 8, 30), "KRP-ENG": ("PRE_V2", 1, 3)})

    def _v2_repo_weight(self, suffix):
        return sum(x["weight"] or 0 for x in self.c["milestone_alignment"]
                   if x["class"] == "V2_REPO" and x["tasks"] and x["milestone"].endswith(suffix))

    def test_sense_v2_milestones_hold_52_weight(self):
        """49 from the earlier baselines plus KOS-SENSE-M0-001 at weight 3 (baseline v11, D-117)."""
        self.assertEqual(self._v2_repo_weight("-SENSE-001"), 52)

    def test_motion_v2_milestones_hold_13_weight(self):
        """Baseline v9 (D-100): KOS-MOTION-001 and KOS-MOTION-002 at weight 5 each; baseline v11 (D-117) adds KOS-MOTION-M0-001 at 3."""
        self.assertEqual(self._v2_repo_weight("-MOTION-001"), 13)

    def test_motion_lifecycle_milestone_holds_8_weight(self):
        """Baseline v10 (D-108): KOS-MOTION-003 at weight 8 under V2-M2-MOTION-002."""
        self.assertEqual(self._v2_repo_weight("-MOTION-002"), 8)

    def test_every_repo_milestone_appears_once(self):
        ids = [x["milestone"] for x in self.c["milestone_alignment"]]
        self.assertEqual(len(ids), len(set(ids)))
        for r in pdata()["milestones"]["repo_milestones"]:
            self.assertIn(r["id"], ids)

    def test_section_has_no_percentage(self):
        sec = self.detail.split("## Milestone alignment")[1].split("\n## ")[0]
        self.assertNotIn("%", sec)

    def test_alignment_adds_no_credit(self):
        self.assertEqual(sum(x["credited"] for x in self.c["milestone_alignment"]),
                         sum(g["credited"] for g in self.c["by_milestone"].values()))


class Cli(unittest.TestCase):
    def test_check_passes(self):
        p = subprocess.run([sys.executable, "tools/consolidate_status.py", "--sources-dir", "sources", "--check"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main()
