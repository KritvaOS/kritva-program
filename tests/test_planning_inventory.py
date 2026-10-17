import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_planning_inventory as cpi  # noqa: E402

T = ROOT / "v2/tracking"
LOAD = lambda n: json.loads((T / n).read_text(encoding="utf-8"))


class PlanningInventoryTests(unittest.TestCase):
    def setUp(self):
        self.inv, self.base = LOAD("planning_inventory.json"), LOAD("baseline.json")
        self.appr, self.ws = LOAD("approvals.json"), LOAD("workstreams.json")

    def run_check(self, inv=None, base=None, appr=None):
        return cpi.check(inv or self.inv, base or self.base, appr or self.appr, self.ws)

    def test_committed_inventory_is_clean(self):
        self.assertEqual(self.run_check(), [])

    # Negative tests: registration must never become credit.
    def test_credit_eligible_true_is_rejected(self):
        inv = copy.deepcopy(self.inv)
        inv["groups"][0]["credit_eligible"] = True
        self.assertTrue(any("credit_eligible" in p for p in self.run_check(inv)))

    def test_weight_on_inventory_task_is_rejected(self):
        inv = copy.deepcopy(self.inv)
        inv["groups"][0]["tasks"][0]["weight"] = 3
        self.assertTrue(any("weight" in p for p in self.run_check(inv)))

    def test_task_that_enters_baseline_must_leave_inventory(self):
        inv, base = copy.deepcopy(self.inv), copy.deepcopy(self.base)
        tid = inv["groups"][0]["tasks"][0]["task_id"]
        base["tasks"].append({"id": tid, "workstream_id": "RAAS", "weight": 2})
        self.assertTrue(any("baseline task" in p for p in self.run_check(inv, base)))

    def test_approval_for_inventory_task_is_rejected(self):
        inv, appr = copy.deepcopy(self.inv), copy.deepcopy(self.appr)
        tid = inv["groups"][0]["tasks"][0]["task_id"]
        appr["approvals"].append({"approval_id": "A999", "task_id": tid})
        self.assertTrue(any("approval record" in p for p in self.run_check(inv, appr=appr)))

    def test_legacy_alias_cannot_reuse_a_canonical_id(self):
        inv = copy.deepcopy(self.inv)
        tasks = inv["groups"][1]["tasks"]
        tasks[0]["legacy_alias"] = tasks[1]["task_id"]
        self.assertTrue(any("collides" in p for p in self.run_check(inv)))

    def test_unmarked_one_to_many_alias_is_rejected(self):
        inv = copy.deepcopy(self.inv)
        for t in inv["groups"][1]["tasks"]:
            t.pop("alias_kind", None)
        self.assertTrue(any("alias_kind=split" in p for p in self.run_check(inv)))

    def test_wrong_classification_is_rejected(self):
        inv = copy.deepcopy(self.inv)
        inv["classification"] = "BASELINE"
        self.assertTrue(any("PLANNING_ONLY" in p for p in self.run_check(inv)))


if __name__ == "__main__":
    unittest.main()
