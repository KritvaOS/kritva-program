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

    def run_check(self, inv=None, base=None, appr=None, sources_dir=None):
        return cpi.check(self.inv if inv is None else inv, self.base if base is None else base,
                         self.appr if appr is None else appr, self.ws, sources_dir)

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
        for g in inv["groups"][2:5]:
            for t in g["tasks"]:
                t["alias_kind"] = "rename"
        self.assertTrue(any("alias_kind=split" in p for p in self.run_check(inv)))

    def test_wrong_classification_is_rejected(self):
        inv = copy.deepcopy(self.inv)
        inv["classification"] = "BASELINE"
        self.assertTrue(any("PLANNING_ONLY" in p for p in self.run_check(inv)))

    def has(self, inv, text, **kw):
        probs = self.run_check(inv, **kw)
        self.assertTrue(any(text in p for p in probs), probs)

    def mut(self):
        return copy.deepcopy(self.inv)

    def test_all_70_tasks_present_including_parent_group(self):
        n = {g["repository"]: len(g["tasks"]) for g in self.inv["groups"]}
        self.assertEqual(n["KritvaOS/kritva-actuator"], 7)
        self.assertEqual(sum(n.values()), 70)

    def test_registered_group_with_unknown_workstream_is_rejected(self):
        inv = self.mut(); inv["groups"][0]["workstream_id"] = "NOPE"
        self.has(inv, "not in workstreams.json")

    def test_unmapped_group_must_be_proposed(self):
        inv = self.mut(); g = inv["groups"][1]
        g["mapping_status"] = "REGISTERED"
        self.has(inv, "not in workstreams.json")

    def test_proposed_group_with_workstream_id_is_rejected(self):
        inv = self.mut(); inv["groups"][1]["workstream_id"] = "CORE"
        self.has(inv, "workstream_id null")

    def test_proposed_group_with_unknown_proposed_workstream_is_rejected(self):
        inv = self.mut(); inv["groups"][1]["proposed_program_workstreams"] = ["MADE_UP"]
        self.has(inv, "proposed workstream")

    def test_proposed_group_without_label_is_rejected(self):
        inv = self.mut(); del inv["groups"][1]["source_workstream_label"]
        self.has(inv, "source_workstream_label")

    def test_task_level_credit_and_classification_violations(self):
        inv = self.mut(); inv["groups"][0]["tasks"][0]["credit_eligible"] = True
        self.has(inv, "credit_eligible must be false")
        inv = self.mut(); inv["groups"][0]["tasks"][0]["classification"] = "BASELINE"
        self.has(inv, "classification must be PLANNING_ONLY")

    def test_missing_provenance_is_rejected(self):
        inv = self.mut(); del inv["groups"][0]["source"]
        self.has(inv, "source must be an object")
        inv = self.mut(); inv["groups"][0]["source"]["path"] = ""
        self.has(inv, "source.path")

    def test_bad_sha_and_commit_are_rejected(self):
        inv = self.mut(); inv["groups"][0]["source"]["sha256"] = "abc"
        self.has(inv, "sha256")
        inv = self.mut(); inv["groups"][0]["source"]["commit"] = "main"
        self.has(inv, "40-hex")

    def test_bad_repository_name_is_rejected(self):
        inv = self.mut(); inv["groups"][0]["repository"] = "kritva-raas"
        self.has(inv, "KritvaOS/<repo>")

    def test_missing_required_task_field_is_rejected(self):
        inv = self.mut(); del inv["groups"][0]["tasks"][0]["title"]
        self.has(inv, "missing field title")

    def test_bad_recorded_status_is_rejected(self):
        inv = self.mut(); inv["groups"][0]["tasks"][0]["recorded_status"] = "DONE"
        self.has(inv, "recorded_status")

    def test_malformed_alias_kind_is_rejected(self):
        inv = self.mut(); inv["groups"][2]["tasks"][0]["alias_kind"] = "merge"
        self.has(inv, "alias_kind must be rename or split")
        inv = self.mut(); t = inv["groups"][0]["tasks"][0]; t["alias_kind"] = "rename"; t.pop("legacy_alias", None)
        self.has(inv, "without legacy_alias")

    def test_duplicate_task_id_is_rejected(self):
        inv = self.mut(); inv["groups"][2]["tasks"].append(copy.deepcopy(inv["groups"][2]["tasks"][0]))
        self.has(inv, "duplicate")
        inv = self.mut(); inv["groups"][3]["tasks"][0]["task_id"] = inv["groups"][2]["tasks"][0]["task_id"]
        self.has(inv, "more than once")

    def test_alias_collides_with_baseline_and_approval_ids(self):
        base, appr = copy.deepcopy(self.base), copy.deepcopy(self.appr)
        inv = self.mut(); alias = inv["groups"][2]["tasks"][0]["legacy_alias"]
        base["tasks"].append({"id": alias, "workstream_id": "CORE", "weight": 1})
        self.has(inv, "is a baseline task", base=base)
        appr["approvals"].append({"approval_id": "A998", "task_id": alias})
        self.has(inv, "approval record", appr=appr)

    def test_empty_inputs_are_rejected(self):
        self.assertTrue(cpi.check({}, self.base, self.appr, self.ws))
        self.assertTrue(cpi.check({"classification": "PLANNING_ONLY", "inventory_version": 2, "groups": []}, self.base, self.appr, self.ws))
        inv = self.mut(); inv["groups"][0]["tasks"] = []
        self.has(inv, "non-empty")

    def test_verify_sources_detects_tampered_or_missing_task(self):
        import hashlib, tempfile
        inv = self.mut(); g = inv["groups"][0]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / g["source"]["repo"].replace("/", "__") / g["source"]["path"]
            p.parent.mkdir(parents=True)
            body = "\n".join(t["task_id"] for t in g["tasks"][1:])  # first task missing
            p.write_text(body)
            g["source"]["sha256"] = hashlib.sha256(body.encode()).hexdigest()
            self.has(inv, "not found in pinned source", sources_dir=d)
            g["source"]["sha256"] = "0" * 64
            self.has(inv, "sha256 does not match", sources_dir=d)

    def test_inventory_never_affects_progress(self):
        import consolidate_status as cs
        self.assertTrue(hasattr(cs, "main"))
        raw = (T / "consolidated_status.json").read_text(encoding="utf-8")
        ids = {t["task_id"] for g in self.inv["groups"] for t in g["tasks"]}
        self.assertFalse(any(f'"{i}"' in raw for i in ids))


if __name__ == "__main__":
    unittest.main()
