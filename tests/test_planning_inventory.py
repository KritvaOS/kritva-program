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

    def proposed(self):
        """The parent actuator group converted back to the PROPOSED shape (still supported for unapproved mappings)."""
        inv = self.mut(); g = inv["groups"][1]
        g["mapping_status"], g["workstream_id"] = "PROPOSED", None
        g["proposed_program_workstreams"] = g.pop("rollup_targets")
        return inv

    def test_all_108_tasks_present_including_parent_group(self):
        n = {g["repository"]: len(g["tasks"]) for g in self.inv["groups"] if g["workstream_id"] != "RAAS"}
        self.assertEqual(n["KritvaOS/kritva-actuator"], 7)
        raas = {g["increment"]: len(g["tasks"]) for g in self.inv["groups"] if g["workstream_id"] == "RAAS"}
        self.assertEqual(raas, {"B-INC-001 SECURE FOUNDATION": 29, "B-INC-002 IDENTITY ORGANIZATION": 14,
                                "B-INC-003 PROJECTS PLATFORM CATALOG": 11,
                                "B-INC-004 AUDIT TRANSACTIONS IDEMPOTENCY": 13})
        self.assertEqual(sum(n.values()) + sum(raas.values()), 108)

    def test_registered_group_with_unknown_workstream_is_rejected(self):
        inv = self.mut(); inv["groups"][0]["workstream_id"] = "NOPE"
        self.has(inv, "not in workstreams.json")

    def test_unmapped_group_must_be_proposed(self):
        inv = self.proposed(); self.assertEqual(self.run_check(inv), [])
        inv["groups"][1]["mapping_status"] = "REGISTERED"
        self.has(inv, "not in workstreams.json")

    def test_proposed_group_with_workstream_id_is_rejected(self):
        inv = self.proposed(); inv["groups"][1]["workstream_id"] = "CORE"
        self.has(inv, "workstream_id null")

    def test_proposed_group_with_unknown_proposed_workstream_is_rejected(self):
        inv = self.proposed(); inv["groups"][1]["proposed_program_workstreams"] = ["MADE_UP"]
        self.has(inv, "proposed workstream")

    def test_proposed_group_without_label_is_rejected(self):
        inv = self.proposed(); del inv["groups"][1]["source_workstream_label"]
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

    # B-INC-002..004 extraction (D-038): shared tasks and source completeness.
    def raas_group(self, inv, prefix):
        return next(g for g in inv["groups"] if g.get("increment", "").startswith(prefix))

    def test_shared_tasks_are_one_task_that_names_the_other_increment(self):
        g2 = self.raas_group(self.inv, "B-INC-002")
        shared = {t["task_id"]: t for t in g2["tasks"] if "also_in_increments" in t}
        self.assertEqual(sorted(shared), ["KR-BE-1-044", "KR-BE-1-045"])
        for t in shared.values():
            self.assertEqual([a["increment"] for a in t["also_in_increments"]], ["B-INC-003 PROJECTS PLATFORM CATALOG"])
        ids = [t["task_id"] for g in self.inv["groups"] for t in g["tasks"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_shared_task_naming_an_unknown_or_own_increment_is_rejected(self):
        inv = self.mut(); t = self.raas_group(inv, "B-INC-002")["tasks"][-1]
        t["also_in_increments"][0]["increment"] = "B-INC-009 NOPE"
        self.has(inv, "not another increment group")
        inv = self.mut(); t = self.raas_group(inv, "B-INC-002")["tasks"][-1]
        t["also_in_increments"][0]["increment"] = "B-INC-002 IDENTITY ORGANIZATION"
        self.has(inv, "not another increment group")

    def test_shared_task_listed_in_both_increments_is_rejected(self):
        inv = self.mut(); t = self.raas_group(inv, "B-INC-002")["tasks"][-1]
        self.raas_group(inv, "B-INC-003")["tasks"].append(copy.deepcopy(t))
        self.has(inv, "one task, in the first increment only")

    def test_malformed_also_in_increments_is_rejected(self):
        inv = self.mut(); t = self.raas_group(inv, "B-INC-002")["tasks"][-1]
        t["also_in_increments"] = [{"increment": "B-INC-003 PROJECTS PLATFORM CATALOG"}]
        self.has(inv, "needs increment and title")
        inv = self.mut(); t = self.raas_group(inv, "B-INC-002")["tasks"][-1]
        t["also_in_increments"] = "B-INC-003"
        self.has(inv, "must be a list")

    def verify_dir(self, inv, bodies):
        """Write TASKS.md bodies for the three new RaaS groups into a temp sources dir and repin their sha256."""
        import hashlib, tempfile
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        for prefix, body in bodies.items():
            g = self.raas_group(inv, prefix)
            p = Path(d.name) / g["source"]["repo"].replace("/", "__") / g["source"]["path"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body)
            g["source"]["sha256"] = hashlib.sha256(body.encode()).hexdigest()
        return d.name

    def body_for(self, inv, prefix, extra="", status=None):
        g = self.raas_group(inv, prefix)
        out = "# T\n\n## 3. Tasks\n\n"
        for t in g["tasks"]:
            out += f"### {t['task_id']} — {t['title']}\n\n"
            if status and t["task_id"] == status[0]:
                out += f"- **Status:** {status[1]}\n"
        return out + extra

    def all_bodies(self, inv, **over):
        shared = {t["task_id"]: a for g in inv["groups"] for t in g["tasks"] for a in t.get("also_in_increments", [])}
        b = {}
        for prefix in ("B-INC-001", "B-INC-002", "B-INC-003", "B-INC-004"):
            b[prefix] = self.body_for(inv, prefix, **over.get(prefix, {}))
        b["B-INC-003"] += "".join(f"### {tid} — {a['title']}\n\n" for tid, a in shared.items())
        return b

    def test_verify_sources_accepts_complete_extraction_with_shared_tasks(self):
        inv = self.mut()
        every = self.all_bodies(inv)
        d = self.verify_dir(inv, {k: every[k] for k in ("B-INC-002", "B-INC-003", "B-INC-004")})
        probs = self.run_check(inv, sources_dir=d)  # other groups' sources are absent here; only extraction rules matter
        self.assertEqual([p for p in probs if "not extracted" in p or "differs from the source" in p], [])
        self.assertEqual([p for p in probs if "sha256 does not match" in p or "not found in pinned source" in p], [])

    def test_verify_sources_flags_an_unextracted_source_task(self):
        inv = self.mut()
        bodies = {"B-INC-004": self.all_bodies(inv)["B-INC-004"] + "### KR-BE-1-099 — Surprise\n\n"}
        d = self.verify_dir(inv, bodies)
        self.has(inv, "source task KR-BE-1-099 is not extracted", sources_dir=d)

    def test_verify_sources_flags_a_status_that_drifted_from_the_source(self):
        inv = self.mut()
        tid = self.raas_group(inv, "B-INC-004")["tasks"][0]["task_id"]
        bodies = {"B-INC-004": self.body_for(inv, "B-INC-004", status=(tid, "Accepted on 2026-11-01."))}
        d = self.verify_dir(inv, bodies)
        self.has(inv, f"{tid}: recorded_status 'NOT_RECORDED' differs from the source status 'Accepted'", sources_dir=d)

    def test_inventory_never_affects_progress(self):
        import consolidate_status as cs
        self.assertTrue(hasattr(cs, "main"))
        raw = (T / "consolidated_status.json").read_text(encoding="utf-8")
        ids = {t["task_id"] for g in self.inv["groups"] for t in g["tasks"]}
        self.assertFalse(any(f'"{i}"' in raw for i in ids))


    def test_capability_mapping_is_allowed_and_never_a_second_owner(self):
        inv = self.mut(); inv["groups"][0]["tasks"][0]["capabilities"] = ["CONTROL_PLANE"]
        self.assertEqual(self.run_check(inv), [])
        # counted once: identity set is unchanged by mapping
        ids = [t["task_id"] for g in inv["groups"] for t in g["tasks"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unknown_or_execution_workstream_as_capability_is_rejected(self):
        inv = self.mut(); inv["groups"][0]["tasks"][0]["capabilities"] = ["NOPE"]
        self.has(inv, "not a CAPABILITY")
        inv = self.mut(); inv["groups"][0]["tasks"][0]["capabilities"] = ["RAAS"]
        self.has(inv, "not a CAPABILITY")

    def test_duplicate_capability_is_rejected(self):
        inv = self.mut(); inv["groups"][0]["tasks"][0]["capabilities"] = ["CONTROL_PLANE", "CONTROL_PLANE"]
        self.has(inv, "without duplicates")

    def test_capability_cannot_own_tasks_or_hold_effort(self):
        inv = self.mut(); inv["groups"][0]["workstream_id"] = "CONTROL_PLANE"
        self.has(inv, "capabilities cannot own tasks")
        ws = copy.deepcopy(self.ws)
        for w in ws["workstreams"]:
            if w["id"] == "CONTROL_PLANE": w["effort_owner"] = True
        inv = self.mut(); inv["groups"][0]["tasks"][0]["capabilities"] = ["CONTROL_PLANE"]
        probs = cpi.check(inv, self.base, self.appr, ws)
        self.assertTrue(any("effort_owner false" in p for p in probs), probs)

    def test_effort_baseline_has_no_control_plane_estimate(self):
        e = LOAD("effort_estimates.json")
        self.assertIn("RAAS", [w["workstream_id"] for w in e["workstreams"]])
        self.assertNotIn("CONTROL_PLANE", [w["workstream_id"] for w in e["workstreams"]])


    # D-034: the five actuator repos are registered execution workstreams with no effort of their own.
    def test_actuator_workstreams_are_registered_without_effort(self):
        ws = {w["id"]: w for w in self.ws["workstreams"]}
        for wid in ("ACT_INT", "ACT_EMB", "ACT_S", "ACT_M", "ACT_L"):
            self.assertEqual(ws[wid]["kind"], "EXECUTION_WORKSTREAM")
            self.assertIs(ws[wid]["effort_owner"], False)
            self.assertTrue(ws[wid]["rolls_up_to"])
        self.assertEqual(ws["ACT_EMB"]["rolls_up_to"], ["ACTUATION_CONTROLS", "ELECTRICAL_POWER"])
        groups = {g["workstream_id"]: g for g in self.inv["groups"]}
        self.assertTrue({"ACT_INT", "ACT_EMB", "ACT_S", "ACT_M", "ACT_L"} <= set(groups))
        self.assertTrue(all(g["mapping_status"] == "REGISTERED" for g in self.inv["groups"]))

    def reg_problems(self, mutate):
        ws = copy.deepcopy(self.ws); mutate({w["id"]: w for w in ws["workstreams"]}, ws)
        return cpi.check(self.inv, self.base, self.appr, ws)

    def test_child_with_effort_ownership_is_rejected(self):
        p = self.reg_problems(lambda m, w: m["ACT_S"].update(effort_owner=True))
        self.assertTrue(any("effort_owner false" in x for x in p), p)

    def test_rollup_target_must_exist_and_bear_effort(self):
        p = self.reg_problems(lambda m, w: m["ACT_S"].update(rolls_up_to=["NOPE"]))
        self.assertTrue(any("not in workstreams.json" in x for x in p), p)
        p = self.reg_problems(lambda m, w: m["ACT_S"].update(rolls_up_to=["CONTROL_PLANE"]))
        self.assertTrue(any("effort-bearing" in x for x in p), p)
        p = self.reg_problems(lambda m, w: m["ACT_S"].update(rolls_up_to=["ACT_M"]))
        self.assertTrue(any("effort-bearing" in x for x in p), p)

    def test_duplicate_workstream_or_repo_is_rejected(self):
        p = self.reg_problems(lambda m, w: w["workstreams"].append(dict(m["ACT_S"])))
        self.assertTrue(any("duplicate workstream id" in x for x in p), p)
        p = self.reg_problems(lambda m, w: m["ACT_M"].update(repo=m["ACT_S"]["repo"]))
        self.assertTrue(any("share one repo" in x for x in p), p)

    def test_group_rollup_must_match_registry(self):
        inv = self.mut()
        g = next(x for x in inv["groups"] if x["workstream_id"] == "ACT_EMB"); g["rollup_targets"] = ["MECHANICAL"]
        self.has(inv, "rollup_targets must equal")

    def test_estimates_for_a_rolled_up_workstream_are_rejected(self):
        import effort
        e = LOAD("effort_estimates.json")
        reg = {w["id"] for w in self.ws["workstreams"]}
        rolled = {w["id"] for w in self.ws["workstreams"] if w.get("rolls_up_to")}
        self.assertEqual(effort.validate(e, reg, set(self.appr["authorized_approvers"]), rolled), [])
        e2 = copy.deepcopy(e); e2["workstreams"].append(dict(e2["workstreams"][0], workstream_id="ACT_S"))
        errs = effort.validate(e2, reg, set(self.appr["authorized_approvers"]), rolled)
        self.assertTrue(any("cannot carry its own effort" in x for x in errs), errs)

    def test_registration_changes_neither_total_effort_nor_progress(self):
        c = LOAD("consolidated_status.json")
        rows = c["effort"]["rows"]
        self.assertFalse({"ACT_INT", "ACT_EMB", "ACT_S", "ACT_M", "ACT_L"} & {r["workstream_id"] for r in rows})
        self.assertEqual(len(rows), 20)  # the pre-registration registry size; roll-up children add no rows
        self.assertEqual(c["effort"]["sums"]["total"], [203.5, 250.5, 295])
        self.assertEqual(c["effort"]["sums"]["completed"], [57.5, 71.5, 86])


if __name__ == "__main__":
    unittest.main()
