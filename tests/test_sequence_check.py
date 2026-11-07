"""Tests for tools/sequence_check.py: a milestone may not start while a milestone it depends on is not closed (D-112)."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sequence_check as S  # noqa: E402


def make_root(waivers=None):
    d = Path(tempfile.mkdtemp())
    (d / "v2/planning").mkdir(parents=True)
    ms = [{"id": "V2-M0", "depends_on": []}, {"id": "V2-M1", "depends_on": ["V2-M0"]}, {"id": "V2-M2", "depends_on": ["V2-M1"]},
          {"id": "V2-M6", "depends_on": ["V2-M2"]}]
    (d / S.MILESTONES).write_text(json.dumps({"milestones": ms}))
    if waivers is not None:
        (d / S.WAIVERS).write_text(json.dumps({"waivers": waivers}))
    return d


def data(closed=(), accepted=None, tasks=()):
    ms = [{"id": f"V2-M{i}", "closed": f"V2-M{i}" in closed, "target_date": None if i == 6 else "2026-12-01"} for i in (0, 1, 2, 6)]
    bm = {f"V2-{m}-X-001": {"weighted": True, "accepted_weight": w} for m, w in (accepted or {}).items()}
    return {"v2_plan": {"milestones": ms}, "by_milestone": bm,
            "plan_register": {"tasks": [{"milestone": m, "status": st} for m, st in tasks]}}


class Sequence(unittest.TestCase):
    def tearDown(self):
        pass

    def test_nothing_started_is_ok(self):
        rows, errs = S.check(make_root(), data())
        self.assertEqual(errs, [])
        self.assertTrue(all(r["status"] == "OK" for r in rows))

    def test_started_with_open_predecessor_is_a_violation(self):
        rows, errs = S.check(make_root(), data(accepted={"M1": 5}))
        self.assertEqual({r["milestone"]: r["status"] for r in rows}["M1"], "VIOLATION")
        self.assertEqual(len(errs), 1)
        self.assertIn("M1 has started while M0 is not closed", errs[0])

    def test_closed_predecessor_allows_start(self):
        _, errs = S.check(make_root(), data(closed={"V2-M0"}, accepted={"M1": 5}))
        self.assertEqual(errs, [])

    def test_in_progress_plan_task_counts_as_started(self):
        _, errs = S.check(make_root(), data(tasks=[("M2", "IN_PROGRESS")]))
        self.assertEqual(len(errs), 1)
        _, errs = S.check(make_root(), data(tasks=[("M2", "NOT_STARTED"), ("M2", "BLOCKED (PD-015)")]))
        self.assertEqual(errs, [])

    def test_waiver_covers_existing_pair_only(self):
        w = [{"milestone": "V2-M1", "predecessor": "V2-M0", "decision": "D-112", "reason": "r"}]
        rows, errs = S.check(make_root(w), data(accepted={"M1": 5}))
        self.assertEqual(errs, [])
        self.assertEqual({r["milestone"]: r["status"] for r in rows}["M1"], "WAIVED")
        self.assertEqual({r["milestone"]: r["waiver"] for r in rows}["M1"], ["D-112"])
        _, errs = S.check(make_root(w), data(accepted={"M1": 5, "M2": 3}))  # M2 after M1 is not waived
        self.assertEqual(len(errs), 1)
        self.assertIn("M2", errs[0])

    def test_incomplete_waiver_is_an_error(self):
        _, errs = S.check(make_root([{"milestone": "V2-M1", "predecessor": "V2-M0"}]), data())
        self.assertTrue(any("needs milestone, predecessor, decision and reason" in e for e in errs))

    def test_hold_milestone_is_not_checked(self):
        rows, _ = S.check(make_root(), data())
        self.assertNotIn("M6", [r["milestone"] for r in rows])

    def test_missing_plan_data_returns_nothing(self):
        self.assertEqual(S.check(make_root(), {}), ([], []))


class Committed(unittest.TestCase):
    def test_committed_sequence_has_no_unwaived_violation(self):
        c = json.loads((ROOT / "v2/tracking/consolidated_status.json").read_text())
        self.assertTrue(c["sequence"])
        self.assertEqual([r for r in c["sequence"] if r["status"] == "VIOLATION"], [])
        self.assertEqual([e for e in c["errors"] if e.startswith("sequence:")], [])

    def test_every_waiver_names_a_decision_in_the_log(self):
        w = json.loads((ROOT / S.WAIVERS).read_text())["waivers"]
        log = (ROOT / "v2/DECISIONS.md").read_text(encoding="utf-8")
        for x in w:
            self.assertIn(f"| {x['decision']} |", log)


if __name__ == "__main__":
    unittest.main()
