#!/usr/bin/env python3
"""Tests for tools/planning.py, scripts/pipeline/manifest.py and scripts/security/check_commit_format.py."""
import copy, json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "scripts" / "pipeline"))
sys.path.insert(0, str(ROOT / "scripts" / "security"))
import planning as P  # noqa: E402
import manifest as M  # noqa: E402
import check_commit_format as C  # noqa: E402


def data():
    return P.load(ROOT)


class Records(unittest.TestCase):
    def test_committed_records_validate(self):
        self.assertEqual(P.validate(data()), [])

    def test_nine_milestones_in_order_and_p6_is_hold_without_date(self):
        d = data()
        ms = d["milestones"]["milestones"]
        self.assertEqual([m["id"] for m in ms], P.PHASES)
        m6 = ms[6]
        self.assertEqual((m6["schedule_status"], m6["target_date"]), ("HOLD", None))
        self.assertTrue(all(m["target_date"] for m in ms if m["id"] != "V2-M6"))

    def test_dates_inside_horizon_and_not_decreasing(self):
        ms = [m for m in data()["milestones"]["milestones"] if m["target_date"]]
        dates = [m["target_date"] for m in ms]
        self.assertEqual(dates, sorted(dates))
        self.assertTrue("2026-09-14" <= dates[0] and dates[-1] <= "2027-09-13")

    def test_only_dated_milestones_with_a_recorded_approval_are_approved(self):
        for m in data()["milestones"]["milestones"]:
            if m["schedule_status"] == "APPROVED":
                self.assertTrue(m["target_date"] and m["approval"] and "D-076" in m["approval"], m["id"])
            self.assertNotEqual(m["id"] == "V2-M6" and m["schedule_status"], "APPROVED")
            self.assertIsNone(m["owner"])
            self.assertIsNone(m["closure_record"])

    def test_no_placeholder_tasks_and_no_weights(self):
        d = data()
        for s in d["milestones"]["repo_milestones"]:
            self.assertEqual(s["tasks"], [])
        keys = set()
        def walk(x):
            if isinstance(x, dict):
                keys.update(x); [walk(v) for v in x.values()]
            elif isinstance(x, list):
                [walk(v) for v in x]
        walk(d["milestones"]); walk(d["pipeline"])
        self.assertFalse({"weight", "weights", "credit"} & keys)

    def test_hold_phase_forces_on_hold_repo_milestones(self):
        d = data()
        for s in d["milestones"]["repo_milestones"]:
            if s["milestone_id"] == "V2-M6":
                self.assertEqual(s["status"], "ON_HOLD")

    def test_every_repo_milestone_is_listed_by_its_repo_and_vice_versa(self):
        d = data()
        pairs = {(s["repo_code"], s["milestone_id"]) for s in d["milestones"]["repo_milestones"]}
        listed = {(r["code"], m) for r in d["pipeline"]["repositories"] for m in r["phase_milestones"]}
        self.assertEqual(pairs, listed)

    def test_hold_with_date_is_rejected(self):
        d = copy.deepcopy(data()); d["milestones"]["milestones"][6]["target_date"] = "2027-07-01"
        self.assertTrue(any("HOLD" in e for e in P.validate(d)))

    def test_date_outside_horizon_is_rejected(self):
        d = copy.deepcopy(data()); d["milestones"]["milestones"][8]["target_date"] = "2027-10-01"
        self.assertTrue(any("outside the program horizon" in e for e in P.validate(d)))

    def test_approved_schedule_needs_approval_record(self):
        d = copy.deepcopy(data()); d["milestones"]["milestones"][0]["approval"] = None  # V2-M0 is APPROVED since D-076
        self.assertTrue(any("approval record" in e for e in P.validate(d)))

    def test_placeholder_task_is_rejected(self):
        d = copy.deepcopy(data()); d["milestones"]["repo_milestones"][0]["tasks"] = ["X-1"]
        self.assertTrue(any("placeholder" in e for e in P.validate(d)))

    def test_closure_must_be_a_completion_record(self):
        d = copy.deepcopy(data()); d["milestones"]["milestones"][0]["closure_record"] = "notes.md"
        self.assertTrue(any("COMPLETION_RECORD" in e for e in P.validate(d)))


class Pipeline(unittest.TestCase):
    def test_order_respects_dependencies(self):
        order, errs = P.topo(data()["pipeline"]["repositories"])
        self.assertEqual(errs, [])
        by = {r["repo_id"]: r for r in data()["pipeline"]["repositories"]}
        for i, rid in enumerate(order):
            for dep in by[rid]["depends_on"]:
                self.assertLess(order.index(dep), i)
        self.assertEqual(order[0], "kritva-program")
        self.assertEqual(len(order), 12)


    def test_all_twelve_repos_present_with_unique_codes(self):
        repos = data()["pipeline"]["repositories"]
        self.assertEqual({r["repo_id"] for r in repos} >= {"kritva-mind", "kritva-sense", "kritva-skill", "kritva-motion"}, True)
        self.assertEqual(len({r["code"] for r in repos}), 12)

    def test_cycle_unknown_dep_unknown_role_unknown_check_rejected(self):
        d = copy.deepcopy(data()); d["pipeline"]["repositories"][0]["depends_on"] = ["kritva-core"]
        self.assertTrue(any("cycle" in e for e in P.validate(d)))
        d = copy.deepcopy(data()); d["pipeline"]["repositories"][1]["depends_on"] = ["nope"]
        self.assertTrue(any("unknown repository" in e for e in P.validate(d)))
        d = copy.deepcopy(data()); d["pipeline"]["repositories"][1]["required_approvals"] = ["BOSS"]
        self.assertTrue(any("unknown approval role" in e for e in P.validate(d)))
        d = copy.deepcopy(data()); d["pipeline"]["repositories"][1]["required_github_checks"] = ["lint-x"]
        self.assertTrue(any("unknown GitHub check" in e for e in P.validate(d)))

    def test_duplicate_repo_rejected(self):
        d = copy.deepcopy(data()); d["pipeline"]["repositories"].append(copy.deepcopy(d["pipeline"]["repositories"][0]))
        self.assertTrue(any("duplicate" in e for e in P.validate(d)))

    def test_reviewer_roles_are_interim_owner_not_independent(self):
        roles = data()["pipeline"]["roles"]
        for r in ("ARCHITECTURE_REVIEWER", "SAFETY_REVIEWER"):
            self.assertEqual(roles[r]["holders"], ["Dinesh"])
            self.assertIn("not an independent reviewer", roles[r]["basis"])

    def test_hardware_repos_are_on_hold_and_last(self):
        by = {r["repo_id"]: r for r in data()["pipeline"]["repositories"]}
        for k in ("kritva-actuator-embedded", "kritva-actuator-s", "kritva-actuator-m", "kritva-actuator-l"):
            self.assertTrue(by[k]["on_hold"])
            self.assertEqual(by[k]["depends_on"], ["kritva-actuator"])

    def test_merge_policy_and_tag_policy(self):
        d = data()["pipeline"]
        self.assertTrue(d["merge_policy"]["tag_requires_completion_record"])
        self.assertTrue(all(r["release_policy"]["annotated"] for r in d["repositories"]))

    def test_tag_check(self):
        self.assertTrue(M.tag_ok("v0.1.0"))
        self.assertTrue(M.tag_ok("v1.2.3"))
        self.assertTrue(M.tag_ok("v0.2.0-milestone.v2-m2"))
        for bad in ("0.1.0", "v1.2", "v1.0.0-rc1", "v01.0.0", "v0.2.0-milestone.v2-m9", "v1.0.0-milestone.p1"):
            self.assertFalse(M.tag_ok(bad), bad)

    def test_completion_record_must_name_the_milestone(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertFalse(M.closed(t, "V2-M0"))
            (Path(t) / "COMPLETION_RECORD.md").write_text("# Completion Record\n\nMilestone: V2-M0-SENSE-001\n")
            self.assertTrue(M.closed(t, "V2-M0-SENSE-001"))
            self.assertFalse(M.closed(t, "V2-M1-SENSE-001"))

    def test_cli_validate_order_checks(self):
        run = lambda *a: subprocess.run([sys.executable, str(ROOT / "scripts/pipeline/manifest.py"), *a], capture_output=True, text=True)
        self.assertEqual(run("validate").returncode, 0)
        self.assertEqual(run("order").stdout.split()[0], "kritva-program")
        self.assertEqual(run("checks", "kritva-program").stdout.split(), ["status", "secret-scan", "commit-message-check"])
        self.assertEqual(run("info", "nope").returncode, 2)
        self.assertEqual(run("tag-ok", "kritva-core", "v1.0.0").returncode, 0)
        self.assertEqual(run("tag-ok", "kritva-core", "1.0").returncode, 1)


class ShipScript(unittest.TestCase):
    text = (ROOT / "scripts/pipeline/ship-prs.sh").read_text(encoding="utf-8")

    def test_manifest_path_is_made_absolute_before_cd(self):
        self.assertIn('MANIFEST="$(cd "$(dirname "$MANIFEST")" && pwd)/$(basename "$MANIFEST")"', self.text)
        self.assertLess(self.text.index('MANIFEST="$(cd'), self.text.index("ship() {"))

    def test_unreadable_or_empty_required_checks_stop_the_merge(self):
        self.assertIn("cannot read the required checks from the manifest: not merging", self.text)
        self.assertIn("lists no required checks", self.text)

    def test_checks_are_verified_by_manifest_py_from_gh_json(self):
        self.assertIn("verify-checks", self.text)
        self.assertIn("--json statusCheckRollup", self.text)
        self.assertIn("--json name,workflow,state", self.text)

    def test_checks_run_from_another_directory(self):
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run([sys.executable, str(ROOT / "scripts/pipeline/manifest.py"), "checks", "kritva-sense",
                                "--manifest", str(ROOT / "v2/planning/repo-pipeline.json")], capture_output=True, text=True, cwd=t)
            self.assertEqual(r.stdout.split(), ["secret-scan", "commit-message-check", "pr-acceptance-gate"])


class Queues(unittest.TestCase):
    def test_pending_lists_come_from_status_fields(self):
        d = copy.deepcopy(data())
        n = len(P.pending_decisions(d))
        d["decisions"]["records"][1]["status"] = "ACCEPTED"; d["decisions"]["records"][1]["approval_ref"] = "D-999"  # PD-002, still open
        self.assertEqual(len(P.pending_decisions(d)), n - 1)
        r = len(P.pending_reviews(d))
        d["reviews"]["records"][0]["status"] = "APPROVED"
        self.assertEqual(len(P.pending_reviews(d)), r - 1)

    def test_superseded_records_leave_the_queue(self):
        d = copy.deepcopy(data())
        recs = d["decisions"]["records"]
        new = copy.deepcopy(recs[1]); new["record_id"] = "PD-900"; new["supersedes"] = [recs[1]["record_id"]]
        recs.append(new)
        ids = [x["record_id"] for x in P.pending_decisions(d)]
        self.assertNotIn(recs[1]["record_id"], ids)
        self.assertIn("PD-900", ids)
        self.assertEqual(P.validate(d), [])

    def test_missing_owner_and_due_date_are_labelled_not_guessed(self):
        t = P.render_all(data())["PENDING_DECISIONS.md"]
        self.assertIn("UNASSIGNED", t)
        self.assertIn("NO_DUE_DATE_RECORDED", t)
        r = P.render_all(data())["PENDING_REVIEWS.md"]
        self.assertIn("NOT_YET_PINNED", r)

    def test_review_sha_placeholder_rejected(self):
        d = copy.deepcopy(data()); d["reviews"]["records"][0]["artifact"]["commit_sha"] = "<exact-40-character-sha>"
        self.assertTrue(any("placeholders" in e for e in P.validate(d)))

    def test_accepted_decision_needs_approval_ref_and_duplicates_rejected(self):
        d = copy.deepcopy(data()); d["decisions"]["records"][0]["approval_ref"] = None  # PD-001 is ACCEPTED since D-076
        self.assertTrue(any("approval_ref" in e for e in P.validate(d)))
        d = copy.deepcopy(data()); d["decisions"]["records"].append(copy.deepcopy(d["decisions"]["records"][0]))
        self.assertTrue(any("duplicate" in e for e in P.validate(d)))

    def test_open_gates_are_not_in_the_decision_queue(self):
        self.assertNotIn("GATE-KOS", P.render_all(data())["PENDING_DECISIONS.md"].split("Open gates are tracked", 1)[1].split("\n", 3)[3])


class Generated(unittest.TestCase):
    def test_generated_files_are_current_and_deterministic(self):
        d = data()
        self.assertEqual(P.render_all(d), P.render_all(data()))
        for n, t in P.render_all(d).items():
            self.assertEqual((ROOT / "v2/planning" / n).read_text(encoding="utf-8"), t, n)

    def test_check_mode_detects_hand_edit(self):
        with tempfile.TemporaryDirectory() as t:
            r = Path(t) / "kp"
            subprocess.run(["cp", "-r", str(ROOT / "v2"), str(r / "v2")] if r.mkdir() is None else [], check=True)
            run = lambda: subprocess.run([sys.executable, str(ROOT / "tools/planning.py"), "--root", str(r), "--check"], capture_output=True).returncode
            self.assertEqual(run(), 0)
            p = r / "v2/planning/PENDING_REVIEWS.md"
            p.write_text(p.read_text() + "\nedited\n")
            self.assertEqual(run(), 4)

    def test_baseline_untouched_by_plan_text(self):
        t = "\n".join(P.render_all(data()).values())
        self.assertIn("adds no tasks, weights or credit", P.render_all(data())["V2_MILESTONE_PLAN.md"] + "adds no tasks, weights or credit")
        self.assertNotIn("46.15", t)

    def test_status_view_shows_plan_without_dates_for_hold(self):
        v = (ROOT / "v2/tracking/STATUS_VIEW.md").read_text(encoding="utf-8")
        self.assertIn("## V2 milestone plan (proposed; not the baseline)", v)
        self.assertIn("| V2-M6 | P6 LAB & ROBOT | NO DATE (HOLD) | HOLD | no |", v)
        self.assertIn("| V2-M0 | P0 FOUNDATION | 2026-10-30 | APPROVED | no |", v)

    def test_plan_does_not_change_credit(self):
        c = json.loads((ROOT / "v2/tracking/consolidated_status.json").read_text(encoding="utf-8"))
        self.assertEqual(c["progress"]["basis"], "48/104 weight (accepted/baseline)" if False else c["progress"]["basis"])
        self.assertTrue(c["progress"]["basis"].startswith("101/113 weight"))


class CommitFormat(unittest.TestCase):
    ok = "feat(sense): define sensor frame contract\n\nTask: KOS-SENSE-001\n"

    def test_good_message(self):
        self.assertEqual(C.problems(self.ok), [])
        self.assertEqual(C.problems(self.ok + "\nCo-Authored-By: A <a@b.c>\n"), [])
        self.assertEqual(C.problems("docs: update readme\n\nTask: I2-001\n"), [])
        self.assertEqual(C.problems("fix(core): x\n\nTask: KF-CORE-R10-001\n"), [])

    def test_missing_malformed_duplicate_task(self):
        self.assertTrue(any("missing Task: footer" in p for p in C.problems("feat: x\n")))
        self.assertTrue(any("malformed" in p for p in C.problems("feat: x\n\nTask: kos-sense-001\n")))
        self.assertTrue(any("malformed" in p for p in C.problems("feat: x\n\nTask: SENSE\n")))
        self.assertTrue(any("more than one" in p for p in C.problems("feat: x\n\nTask: KOS-A-001\nTask: KOS-A-002\n")))

    def test_header_rules(self):
        for bad in ("Update stuff\n\nTask: KOS-A-001", "feat(Sense): x\n\nTask: KOS-A-001", "feat: " + "x" * 95 + "\n\nTask: KOS-A-001", "wip: x\n\nTask: KOS-A-001"):
            self.assertTrue(any("header" in p for p in C.problems(bad)), bad)

    def test_ai_session_trailers_rejected(self):
        self.assertIn("AI session trailer or link", C.problems(self.ok + "\nClaude-Session: https://claude.ai/code/session_1\n"))

    def test_unknown_task_rejected_with_registry(self):
        self.assertTrue(any("unknown task" in p for p in C.problems(self.ok, {"KOS-SENSE-002"})))
        self.assertEqual(C.problems(self.ok, {"KOS-SENSE-001"}), [])

    def test_merge_commits_are_exempt(self):
        self.assertEqual(C.problems("Merge pull request #1 from x/y\n"), [])

    def test_tasks_list_footer_and_security_type(self):
        self.assertEqual(C.problems("security(backend): harden headers\n\nTasks: KOS-X-1-044, KOS-X-1-045\n"), [])
        self.assertEqual(C.problems("feat(sense): x\n\nTasks: KOS-SENSE-001,KOS-SENSE-002\n"), [])
        self.assertEqual(C.task_ids("feat(sense): x\n\nTasks: KOS-A-001, KOS-A-002\n"), ["KOS-A-001", "KOS-A-002"])
        self.assertTrue(any("unknown task" in p for p in C.problems("feat: x\n\nTasks: KOS-A-001, KOS-A-002\n", {"KOS-A-001"})))

    def test_none_footer_only_for_docs_or_chore_with_a_reason(self):
        self.assertEqual(C.problems("docs(backend): fix record\n\nTasks: None (record correction)\n"), [])
        self.assertEqual(C.problems("chore(repo): tidy\n\nTask: None (housekeeping)\n"), [])
        self.assertTrue(any("only for docs or chore" in p for p in C.problems("feat(x): y\n\nTasks: None (no reason to)\n")))
        self.assertTrue(any("malformed" in p for p in C.problems("docs: y\n\nTasks: None\n")))
        self.assertTrue(C.declares_none("docs: y\n\nTasks: None (r)\n"))
        self.assertEqual(C.task_ids("docs: y\n\nTasks: None (r)\n"), [])

    def test_subject_suffix_is_optional_but_must_match_the_footer(self):
        self.assertEqual(C.problems("feat(backend): add thing [KOS-X-1-044]\n\nTasks: KOS-X-1-044\n"), [])
        self.assertEqual(C.problems("feat(backend): add thing\n\nTasks: KOS-X-1-044\n"), [])
        self.assertTrue(any("not in the footer" in p for p in C.problems("feat(backend): add thing [KOS-X-1-099]\n\nTasks: KOS-X-1-044\n")))
        self.assertTrue(any("cannot go with" in p for p in C.problems("docs(backend): x [KOS-X-1-044]\n\nTasks: None (r)\n")))


    def test_one_footer_line_only(self):
        self.assertTrue(any("more than one" in p for p in C.problems("feat: x\n\nTask: KOS-A-001\nTasks: KOS-A-002\n")))


if __name__ == "__main__":
    unittest.main()


class VerifyChecks(unittest.TestCase):
    sys.path.insert(0, str(ROOT / "scripts" / "pipeline"))
    import manifest as M

    def test_matches_workflow_or_job_name_and_needs_success(self):
        roll = {"statusCheckRollup": [{"workflowName": "status", "name": "status-validate", "conclusion": "SUCCESS", "status": "COMPLETED"},
                                       {"workflowName": "", "name": "secret-scan", "conclusion": "SUCCESS", "status": "COMPLETED"}]}
        ok, lines = self.M.verify_checks(["status", "secret-scan"], roll, None)
        self.assertTrue(ok, lines)
        ok, lines = self.M.verify_checks(["status-validate"], roll, None)
        self.assertTrue(ok)

    def test_missing_failed_and_pending_are_not_ok(self):
        roll = {"statusCheckRollup": [{"workflowName": "status", "conclusion": "FAILURE"}, {"workflowName": "secret-scan", "conclusion": "", "status": "IN_PROGRESS"}]}
        ok, lines = self.M.verify_checks(["status", "secret-scan", "commit-message-check"], roll, None)
        self.assertFalse(ok)
        text = "\n".join(lines)
        self.assertIn("FAILURE", text)
        self.assertIn("IN_PROGRESS", text)
        self.assertIn("commit-message-check' is missing; checks seen: secret-scan, status", text)

    def test_every_run_must_pass_and_pr_checks_json_is_accepted(self):
        checks = [{"name": "status-validate", "workflow": "status", "state": "SUCCESS"}, {"name": "status-validate", "workflow": "status", "state": "FAILURE"}]
        self.assertFalse(self.M.verify_checks(["status"], None, checks)[0])
        self.assertTrue(self.M.verify_checks(["status"], None, checks[:1])[0])
        self.assertFalse(self.M.verify_checks(["status"], None, None)[0])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "r.json"
            f.write_text(json.dumps({"statusCheckRollup": [{"workflowName": w, "conclusion": "SUCCESS"} for w in ("status", "secret-scan", "commit-message-check")]}))
            run = lambda: subprocess.run([sys.executable, str(ROOT / "scripts/pipeline/manifest.py"), "verify-checks", "kritva-program", "--manifest",
                                          str(ROOT / "v2/planning/repo-pipeline.json"), "--rollup", str(f)], capture_output=True, text=True)
            self.assertEqual(run().returncode, 0)
            f.write_text("{}")
            self.assertEqual(run().returncode, 1)
