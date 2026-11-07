"""Tests for tools/plan_register.py: the seven-repository plan register summary (D-109, display only)."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import plan_register  # noqa: E402

REGISTER = ROOT / plan_register.FILE


def row(rid, ms="M0", repo="Program", pt="3", lo="2", hi="4", parent="", credit="0", typ="PLANNING_TASK", state="APPROVED_PLAN", counted="true"):
    return (f"| {typ} | {rid} | {repo} | {ms} | title | {parent} | {pt} | {lo} | {hi} | {state} | NOT_STARTED | {credit} | {counted} | x |")


def table(rows, total):
    return "\n".join(rows) + f"\n| Counted planning register | {total[0]} | {total[1]} | {total[2]} | {total[3]} |\n"


class SyntheticTests(unittest.TestCase):
    def check(self, rows, total):
        text = table(rows, total)
        return plan_register.validate(plan_register.parse(text), text)

    def test_valid(self):
        self.assertEqual(self.check([row("A-1"), row("A-2", pt="5", lo="4", hi="6")], (2, 8, 6, 10)), [])

    def test_zero_weight_rejected(self):
        self.assertTrue(any("non-zero" in e for e in self.check([row("A-1", pt="0", lo="0", hi="0")], (1, 0, 0, 0))))

    def test_range_rejected(self):
        self.assertTrue(any("low <=" in e for e in self.check([row("A-1", pt="5", lo="6", hi="7")], (1, 5, 6, 7))))

    def test_credit_rejected(self):
        self.assertTrue(any("credit 0" in e for e in self.check([row("A-1", credit="1")], (1, 3, 2, 4))))

    def test_duplicate_id_rejected(self):
        self.assertTrue(any("duplicate" in e for e in self.check([row("A-1"), row("A-1")], (2, 6, 4, 8))))

    def test_total_mismatch_rejected(self):
        self.assertTrue(any("stated totals" in e for e in self.check([row("A-1")], (1, 9, 2, 4))))

    def test_child_needs_retired_parent(self):
        self.assertTrue(any("not a retired parent" in e for e in self.check([row("A-1", parent="P-1")], (1, 3, 2, 4))))

    def test_retired_parent_carries_no_weight(self):
        bad = row("P-1", typ="RETIRED_PARENT", state="DECOMPOSED_REPLACED", counted="false")
        self.assertTrue(any("retired parent" in e for e in self.check([bad], (0, 0, 0, 0))))

    def test_bad_column_count_raises(self):
        with self.assertRaises(ValueError):
            plan_register.parse("| PLANNING_TASK | only | three |")

    def test_absent_register_is_not_an_error(self):
        self.assertEqual(plan_register.load("/nonexistent-root"), (None, None, []))


@unittest.skipUnless(REGISTER.exists(), "register not present")
class RegisterTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.text, self.errs = plan_register.load(ROOT)

    def test_register_validates(self):
        self.assertEqual(self.errs, [])

    def test_counts_and_totals(self):
        planned = [r for r in self.rows if r["record_type"] == "PLANNING_TASK"]
        retired = [r for r in self.rows if r["record_type"] == "RETIRED_PARENT"]
        self.assertEqual(len(planned), 59)
        self.assertEqual(len(retired), 14)
        self.assertEqual((sum(int(r["weight_point"]) for r in planned), sum(int(r["low"]) for r in planned), sum(int(r["high"]) for r in planned)), (275, 213, 338))

    def test_summary_matches_baseline_split(self):
        base = {"by_milestone": {"V2-M1-SENSE-001": {"weight": 5, "accepted_weight": 5, "weighted": True},
                                 "V2-M2-SENSE-001": {"weight": 19, "accepted_weight": 14, "weighted": True},
                                 "KOS-I2": {"weight": 18, "accepted_weight": 18, "weighted": True}}}
        s = plan_register.summary(self.rows, base)
        self.assertEqual((s["v2_baseline_weight"], s["v2_accepted_weight"]), (24, 19))
        self.assertEqual(s["point"], 275)
        self.assertEqual(s["by_milestone"]["M2"]["baseline"], 19)
        self.assertEqual(sum(v["point"] for v in s["by_repo"].values()), 275)

    def test_view_lines_state_no_credit(self):
        base = {"by_milestone": {"V2-M1-SENSE-001": {"weight": 5, "accepted_weight": 5, "weighted": True}}}
        c = {"by_milestone": base["by_milestone"], "plan_register": plan_register.summary(self.rows, base)}
        text = "\n".join(plan_register.view_lines(c))
        self.assertIn("no credit", text)
        self.assertIn("not the baseline", text)


class Titles(unittest.TestCase):
    def test_register_declares_m4_as_developer_experience(self):
        text = (ROOT / plan_register.FILE).read_text(encoding="utf-8")
        t = plan_register.titles(text)
        self.assertEqual(sorted(t), [f"M{i}" for i in range(9)])
        self.assertIn("DEVELOPER EXPERIENCE", t["M4"])
        self.assertNotIn("BOOKING", " ".join(t.values()))


if __name__ == "__main__":
    unittest.main()
