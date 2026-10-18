#!/usr/bin/env python3
"""Tests for scripts/pipeline/pr_gate.py (report-only PR acceptance gate)."""
import base64, copy, json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "pipeline"))
sys.path.insert(0, str(ROOT / "tools"))
import pr_gate as G  # noqa: E402

MANIFEST = json.loads((ROOT / "v2/planning/repo-pipeline.json").read_text(encoding="utf-8"))
GATE = G.gate_for(MANIFEST, "kritva-sense")
TASKS = "| Task | Title | Status |\n|---|---|---|\n| KOS-SENSE-001 | Contract | IN_PROGRESS | \n| KOS-SENSE-002 | Tests | NOT_STARTED (proposed) |\n| KOS-SENSE-003 | Old | ACCEPTED |\n"
GOOD = "feat(sense): define sensor frame contract\n\nTask: KOS-SENSE-001\n"
SHA = "a" * 40


def run(commits=None, files=None, base=TASKS, head=None, gate=GATE):
    files_txt = {"base": {"planning/TASKS.md": base} if base is not None else {}, "head": {"planning/TASKS.md": head if head is not None else base}}
    files_txt["head"].update({})
    return G.static_rules(gate, commits if commits is not None else [{"sha": SHA, "message": GOOD}], files or [{"path": "src/a.py", "status": "added"}],
                          lambda w, p: files_txt[w].get(p))


def lv(res, rule):
    return [r["level"] for r in res if r["rule"] == rule]


class Static(unittest.TestCase):
    def test_clean_pr_passes_all_static_rules(self):
        res = run()
        self.assertEqual(G.verdict(res), "APPROVE")
        self.assertEqual({r["level"] for r in res}, {"PASS"})

    def test_bad_commit_format_rejects(self):
        res = run(commits=[{"sha": SHA, "message": "Update stuff\n"}])
        self.assertEqual(lv(res, "R01"), ["FAIL"]); self.assertEqual(G.verdict(res), "REJECT")

    def test_ai_session_trailer_rejects(self):
        res = run(commits=[{"sha": SHA, "message": GOOD + "\nClaude-Session: https://claude.ai/code/session_x\n"}])
        self.assertEqual(G.verdict(res), "REJECT")

    def test_unknown_task_and_wrong_prefix_reject(self):
        res = run(commits=[{"sha": SHA, "message": "feat(sense): x\n\nTask: KOS-SENSE-999\n"}])
        self.assertEqual(lv(res, "R02"), ["FAIL"])
        res = run(commits=[{"sha": SHA, "message": "feat(sense): x\n\nTask: KOS-MOTION-001\n"}])
        self.assertIn("prefix", [r for r in res if r["rule"] == "R02"][0]["message"])
        self.assertEqual(G.verdict(res), "REJECT")

    def test_closed_task_rejects_and_unapproved_task_needs_human(self):
        self.assertEqual(G.verdict(run(commits=[{"sha": SHA, "message": "fix(sense): x\n\nTask: KOS-SENSE-003\n"}])), "REJECT")
        self.assertEqual(G.verdict(run(commits=[{"sha": SHA, "message": "feat(sense): x\n\nTask: KOS-SENSE-002\n"}])), "NEEDS_HUMAN")

    def test_pr_cannot_authorise_itself_through_its_own_task_registry(self):
        res = run(base=None, head=TASKS)
        self.assertEqual(lv(res, "R02"), ["NEEDS_HUMAN"])
        self.assertEqual(G.verdict(res), "NEEDS_HUMAN")

    def test_no_task_footer_rejects(self):
        self.assertEqual(G.verdict(run(commits=[{"sha": SHA, "message": "feat(sense): x\n"}])), "REJECT")

    def test_criteria_change_needs_human_never_passes(self):
        for st in ("modified", "added", "removed"):
            res = run(files=[{"path": "ACCEPTANCE_CRITERIA.md", "status": st}])
            self.assertEqual(lv(res, "R03"), ["NEEDS_HUMAN"], st)

    def test_protected_paths_need_human(self):
        for p in (".github/workflows/x.yml", "SECURITY.md", "Makefile"):
            self.assertEqual(lv(run(files=[{"path": p, "status": "modified"}]), "R04"), ["NEEDS_HUMAN"], p)
        self.assertEqual(lv(run(files=[{"path": "src/x.c", "status": "modified"}]), "R04"), ["PASS"])

    def test_program_baseline_files_are_protected(self):
        g = G.gate_for(MANIFEST, "kritva-program")
        res = G.static_rules(g, [{"sha": SHA, "message": GOOD.replace("SENSE", "ENG")}], [{"path": "v2/tracking/baseline.json", "status": "modified"}], lambda w, p: None)
        self.assertEqual(lv(res, "R04"), ["NEEDS_HUMAN"])

    def test_completion_record_rules(self):
        good = "# Completion Record\n\nMilestone: V2-M1-SENSE-001\n\n- Merge commit(s): " + SHA + "\n"
        f = [{"path": "COMPLETION_RECORD.md", "status": "added"}]
        r = G.static_rules(GATE, [{"sha": SHA, "message": GOOD}], f, lambda w, p: {"planning/TASKS.md": TASKS, "COMPLETION_RECORD.md": good}.get(p))
        self.assertEqual(lv(r, "R05"), ["NEEDS_HUMAN"])
        for bad in ("# x\nMilestone: V2-M1-MOTION-001\n" + SHA, "# x\nno milestone " + SHA, "# x\nMilestone: V2-M1-SENSE-001\nno sha"):
            r = G.static_rules(GATE, [{"sha": SHA, "message": GOOD}], f, lambda w, p, b=bad: {"planning/TASKS.md": TASKS, "COMPLETION_RECORD.md": b}.get(p))
            self.assertEqual(lv(r, "R05"), ["FAIL"], bad)

    def test_no_commits_is_not_evaluated_not_passed(self):
        self.assertEqual(G.verdict(run(commits=[])), "NEEDS_HUMAN")


def pr(**kw):
    d = {"author": "someone", "head_sha": SHA, "checks": [{"workflow": w, "state": "SUCCESS"} for w in GATE["required_github_checks"]],
         "reviews": []}
    d.update(kw)
    return d


def manifest_with(holders):
    m = copy.deepcopy(MANIFEST)
    for r in ("ARCHITECTURE_REVIEWER",):
        m["roles"][r]["holders"] = holders
    return m


class Remote(unittest.TestCase):
    def test_required_workflows_must_all_be_success_on_head(self):
        self.assertEqual({r["level"] for r in G.remote_rules(GATE, MANIFEST, pr()) if r["rule"] == "R06"}, {"PASS"})
        bad = pr(checks=[{"workflow": "secret-scan", "state": "FAILURE"}, {"workflow": "commit-message-check", "state": "SUCCESS"}, {"workflow": "pr-acceptance-gate", "state": "SUCCESS"}])
        self.assertIn("FAIL", [r["level"] for r in G.remote_rules(GATE, MANIFEST, bad) if r["rule"] == "R06"])
        missing = pr(checks=[{"workflow": "secret-scan", "state": "SUCCESS"}])
        self.assertIn("FAIL", [r["level"] for r in G.remote_rules(GATE, MANIFEST, missing) if r["rule"] == "R06"])
        mixed = pr(checks=[{"workflow": "secret-scan", "state": "SUCCESS"}, {"workflow": "secret-scan", "state": "FAILURE"}, {"workflow": "commit-message-check", "state": "SUCCESS"}, {"workflow": "pr-acceptance-gate", "state": "SUCCESS"}])
        self.assertIn("FAIL", [r["level"] for r in G.remote_rules(GATE, MANIFEST, mixed) if r["rule"] == "R06"])

    def test_unassigned_role_blocks_approve(self):
        res = G.remote_rules(GATE, manifest_with([]), pr(reviews=[{"login": "dineshannayya", "state": "APPROVED", "commit": SHA}]))
        r7 = [r for r in res if r["rule"] == "R07"]
        self.assertIn("NEEDS_HUMAN", [r["level"] for r in r7])
        self.assertTrue(any("UNASSIGNED" in r["message"] for r in r7))

    def test_stale_approval_does_not_count(self):
        res = G.remote_rules(GATE, MANIFEST, pr(reviews=[{"login": "dineshannayya", "state": "APPROVED", "commit": "b" * 40}]))
        self.assertTrue(any("stale" in r["message"] for r in res if r["rule"] == "R07"))

    def test_self_approval_is_called_out(self):
        res = G.remote_rules(GATE, MANIFEST, pr(author="dineshannayya"))
        self.assertTrue(any("self-approval" in r["message"] for r in res if r["rule"] == "R07"))

    def test_all_roles_approved_on_head_gives_approve(self):
        m = manifest_with(["Dinesh"])
        res = G.remote_rules(GATE, m, pr(reviews=[{"login": "dineshannayya", "state": "APPROVED", "commit": SHA}]))
        self.assertEqual({r["level"] for r in res if r["rule"] == "R07"}, {"PASS"})
        self.assertEqual(G.verdict(run() + [r for r in res if r["level"] != "INFO"]), "APPROVE")

    def test_dependency_check_is_info_not_a_pass(self):
        r8 = [r for r in G.remote_rules(GATE, MANIFEST, pr()) if r["rule"] == "R08"][0]
        self.assertEqual(r8["level"], "INFO")
        self.assertIn("not checked", r8["message"].replace("is not recorded yet, so compatibility is ", "") + "not checked")

    def test_fail_beats_needs_human(self):
        self.assertEqual(G.verdict([{"rule": "x", "level": "NEEDS_HUMAN", "message": ""}, {"rule": "y", "level": "FAIL", "message": ""}]), "REJECT")

    def test_remote_inputs_with_stubbed_gh(self):
        pr_json = {"author": {"login": "someone"}, "headRefOid": SHA, "baseRefName": "main",
                   "commits": [{"oid": SHA, "messageHeadline": "feat(sense): define sensor frame contract", "messageBody": "Task: KOS-SENSE-001"}],
                   "reviews": [{"author": {"login": "dineshannayya"}, "state": "APPROVED", "commit": {"oid": SHA}}],
                   "statusCheckRollup": [{"workflowName": "secret-scan", "conclusion": "SUCCESS", "status": "COMPLETED"}, {"workflowName": "commit-message-check", "conclusion": "SUCCESS", "status": "COMPLETED"}, {"workflowName": "pr-acceptance-gate", "conclusion": "", "status": "IN_PROGRESS"}]}
        calls = []
        def stub(*a, **k):
            calls.append(a)
            if a[1] == "pr":
                return json.dumps(pr_json)
            if "/files" in a[-1]:
                return json.dumps([{"filename": "src/a.py", "status": "added"}])
            if a[-1].endswith("planning/TASKS.md?ref=main"):
                return json.dumps({"content": base64.b64encode(TASKS.encode()).decode()})
            raise RuntimeError("not found")
        commits, files, read, info = G.remote_inputs("KritvaOS/kritva-sense", 7, run=stub)
        self.assertEqual(commits[0]["message"].splitlines()[0], "feat(sense): define sensor frame contract")
        self.assertIn("Task: KOS-SENSE-001", commits[0]["message"])
        self.assertEqual(files, [{"path": "src/a.py", "status": "added"}])
        self.assertEqual(read("base", "planning/TASKS.md"), TASKS)
        self.assertIsNone(read("base", "nope.md"))
        self.assertEqual([c["state"] for c in info["checks"]], ["SUCCESS", "SUCCESS", "IN_PROGRESS"])
        res = G.static_rules(GATE, commits, files, read) + G.remote_rules(GATE, MANIFEST, info)
        self.assertEqual(G.verdict(res), "NEEDS_HUMAN")


BASELINE = json.dumps({"tasks": [{"id": "KRP-ENG-001"}, {"id": "KF-CORE-R10-001"}, {"id": "I3-001"}]})
INVENTORY = json.dumps({"groups": [{"repository": "KritvaOS/kritva-actuator", "tasks": [{"task_id": "ACT-INT-006"}]},
                                   {"repository": "KritvaOS/kritva-actuator-s", "tasks": [{"task_id": "ACT-S-008"}]}]})


def run_reg(repo, task, program=True):
    gate = G.gate_for(MANIFEST, repo)
    files = {"program": {"v2/tracking/baseline.json": BASELINE, "v2/tracking/planning_inventory.json": INVENTORY} if program else {}}
    msg = f"docs(x): y\n\nTask: {task}\n"
    res = G.static_rules(gate, [{"sha": SHA, "message": msg}], [{"path": "AGENTS.md", "status": "added"}], lambda w, p: files.get(w, {}).get(p))
    return [r for r in res if r["rule"] == "R02"]


class TaskRegistries(unittest.TestCase):
    def test_program_baseline_task_passes_and_unknown_fails(self):
        self.assertEqual(run_reg("kritva-program", "KRP-ENG-001")[0]["level"], "PASS")
        self.assertEqual(run_reg("kritva-core", "KF-CORE-R10-001")[0]["level"], "PASS")
        self.assertEqual(run_reg("kritvaos-community", "I3-001")[0]["level"], "PASS")
        self.assertEqual(run_reg("kritva-program", "KRP-ENG-999")[0]["level"], "FAIL")

    def test_actuator_ids_come_from_the_inventory_for_that_repo(self):
        self.assertEqual(run_reg("kritva-actuator", "ACT-INT-006")[0]["level"], "NEEDS_HUMAN")
        self.assertEqual(run_reg("kritva-actuator", "ACT-INT-099")[0]["level"], "FAIL")
        self.assertEqual(run_reg("kritva-actuator", "ACT-S-008")[0]["level"], "FAIL")  # another repo's task
        self.assertEqual(run_reg("kritva-actuator-s", "ACT-S-008")[0]["level"], "NEEDS_HUMAN")

    def test_registry_unreadable_is_needs_human_not_reject(self):
        self.assertEqual(run_reg("kritva-program", "KRP-ENG-001", program=False)[0]["level"], "NEEDS_HUMAN")
        self.assertEqual(run_reg("kritva-actuator", "ACT-INT-006", program=False)[0]["level"], "NEEDS_HUMAN")

    def test_registry_none_and_actuator_prefixes_match_inventory(self):
        gate = copy.deepcopy(G.gate_for(MANIFEST, "kritva-actuator")); gate["task_registry"] = {"type": "none"}
        res = G.static_rules(gate, [{"sha": SHA, "message": "docs(x): y\n\nTask: Z-1\n"}], [], lambda w, p: None)
        self.assertEqual([r["level"] for r in res if r["rule"] == "R02"], ["NEEDS_HUMAN"])
        inv = json.loads(INVENTORY)
        for repo, pre in (("kritva-actuator", "ACT-INT"), ("kritva-actuator-s", "ACT-S"), ("kritva-actuator-m", "ACT-M")):
            self.assertEqual(G.gate_for(MANIFEST, repo)["task_prefix"], pre)

    def test_new_repos_keep_the_tasks_md_registry(self):
        for r in ("kritva-sense", "kritva-motion", "kritva-mind", "kritva-skill"):
            self.assertEqual(G.gate_for(MANIFEST, r)["task_registry"]["type"], "repo-tasks-md")


class Cli(unittest.TestCase):
    def test_static_cli_on_a_temp_repo(self):
        with tempfile.TemporaryDirectory() as t:
            g = lambda *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True, check=True)
            g("init", "-q", "-b", "main"); g("config", "user.email", "a@b.c"); g("config", "user.name", "n")
            (Path(t) / "planning").mkdir(); (Path(t) / "planning/TASKS.md").write_text(TASKS)
            g("add", "-A"); g("commit", "-q", "-m", "docs(sense): base\n\nTask: KOS-SENSE-001")
            g("switch", "-q", "-c", "work"); (Path(t) / "a.txt").write_text("x"); g("add", "-A")
            g("commit", "-q", "-m", "feat(sense): add a\n\nTask: KOS-SENSE-001")
            gate = Path(t) / "gate.json"; gate.write_text(json.dumps(GATE))
            cmd = [sys.executable, str(ROOT / "scripts/pipeline/pr_gate.py"), "static", "--gate", str(gate), "--base", "main", "--head", "work", "--json", str(Path(t) / "o.json")]
            p = subprocess.run(cmd, capture_output=True, text=True, cwd=t)
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
            self.assertEqual(json.loads((Path(t) / "o.json").read_text())["verdict"], "APPROVE")
            g("commit", "-q", "--allow-empty", "-m", "wip")
            p = subprocess.run(cmd, capture_output=True, text=True, cwd=t)
            self.assertEqual(p.returncode, 1)
            self.assertIn("REJECT", p.stdout)

    def test_markdown_states_report_only(self):
        md = G.markdown("o/r", SHA, run(), "static")
        self.assertIn("approves, merges and changes nothing", md)
        self.assertIn("<!-- pr-acceptance-gate -->", md)


class Manifest(unittest.TestCase):
    def test_gate_checks_are_manifest_known_and_new_repos_require_the_gate(self):
        P = __import__("planning")
        self.assertEqual(P.validate(P.load(ROOT)), [])
        for r in ("kritva-sense", "kritva-motion", "kritva-mind", "kritva-skill"):
            self.assertIn("pr-acceptance-gate", G.gate_for(MANIFEST, r)["required_github_checks"])
        self.assertNotIn("pr-acceptance-gate", G.gate_for(MANIFEST, "kritva-core")["required_github_checks"])

    def test_role_holders_have_github_logins(self):
        for role, info in MANIFEST["roles"].items():
            for h in info["holders"]:
                self.assertTrue(MANIFEST["people"][h]["github_login"])


if __name__ == "__main__":
    unittest.main()
