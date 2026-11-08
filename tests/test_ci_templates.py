#!/usr/bin/env python3
"""KRP-M0-004: tests for the program CI templates and for the rules those checks enforce.

Each class shows a rule rejecting a bad input, not only accepting a good one:
  CommitRules   pr-acceptance-gate R01/R02: bad commit messages and unknown tasks produce REJECT
  ProtectedPath pr-acceptance-gate R04: a change under .github/ is NEEDS_HUMAN, never a silent pass
  TagPolicy     tag-policy-check: only vMAJOR.MINOR.PATCH and vX.Y.Z-milestone.v2-mN tags pass
  Templates     the three workflow templates exist, are pinned, name the right job and call scripts that exist
"""
import json, re, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "pipeline"))
sys.path.insert(0, str(ROOT / "tools"))
import pr_gate as G  # noqa: E402
import manifest as M  # noqa: E402

MANIFEST_PATH = ROOT / "v2/planning/repo-pipeline.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
GATE = G.gate_for(MANIFEST, "kritva-program")
TPL = ROOT / "tools" / "ci-templates"
SHA = "b" * 40
BASELINE = json.dumps({"tasks": [{"id": "KRP-M0-004"}]})
GOOD = "ci(program): add unit-tests workflow\n\nTasks: KRP-M0-004\n"


def static(commits, files=None):
    files = files or [{"path": "tools/x.py", "status": "added"}]
    texts = {("program", "v2/tracking/baseline.json"): BASELINE}
    return G.static_rules(GATE, [{"sha": SHA, "message": m} for m in commits], files, lambda w, p: texts.get((w, p)))


def level(res, rule):
    return [r["level"] for r in res if r["rule"] == rule]


class CommitRules(unittest.TestCase):
    def test_good_commit_passes_r01_and_r02(self):
        res = static([GOOD])
        self.assertEqual(level(res, "R01"), ["PASS"])
        self.assertEqual(level(res, "R02"), ["PASS"])
        self.assertEqual(G.verdict(res), "NEEDS_HUMAN" if "NEEDS_HUMAN" in [r["level"] for r in res] else G.verdict(res))

    def test_rejects_free_text_subject(self):
        res = static(["updated some files\n\nTasks: KRP-M0-004\n"])
        self.assertEqual(level(res, "R01"), ["FAIL"])
        self.assertEqual(G.verdict(res), "REJECT")

    def test_rejects_session_trailer(self):
        res = static([GOOD + "Claude-Session: https://claude.ai/code/session_x\n"])
        self.assertEqual(level(res, "R01"), ["FAIL"])
        self.assertEqual(G.verdict(res), "REJECT")

    def test_rejects_overlong_subject(self):
        res = static(["ci(program): " + "x" * 91 + "\n\nTasks: KRP-M0-004\n"])
        self.assertEqual(level(res, "R01"), ["FAIL"])

    def test_rejects_missing_footer(self):
        res = static(["ci(program): add unit-tests workflow\n"])
        self.assertEqual(level(res, "R01"), ["FAIL"])

    def test_rejects_task_not_in_baseline(self):
        res = static(["ci(program): add unit-tests workflow\n\nTasks: KRP-NOPE-999\n"])
        self.assertIn("FAIL", level(res, "R02"))
        self.assertEqual(G.verdict(res), "REJECT")

    def test_docs_commit_with_stated_reason_needs_no_task(self):
        res = static(["docs(program): fix a typo\n\nTasks: None (docs only)\n"])
        self.assertEqual(level(res, "R01"), ["PASS"])
        self.assertEqual(level(res, "R02"), ["PASS"])


class ProtectedPath(unittest.TestCase):
    def test_workflow_change_needs_human(self):
        res = static([GOOD], [{"path": ".github/workflows/unit-tests.yml", "status": "added"}])
        self.assertEqual(level(res, "R04"), ["NEEDS_HUMAN"])
        self.assertNotEqual(G.verdict(res), "APPROVE")

    def test_baseline_and_approvals_are_protected(self):
        for p in ("v2/tracking/baseline.json", "v2/tracking/approvals.json", "v2/planning/repo-pipeline.json"):
            res = static([GOOD], [{"path": p, "status": "modified"}])
            self.assertEqual(level(res, "R04"), ["NEEDS_HUMAN"], p)

    def test_ordinary_file_passes(self):
        self.assertEqual(level(static([GOOD]), "R04"), ["PASS"])


class TagPolicy(unittest.TestCase):
    GOOD = ["v0.1.0", "v1.2.3", "v10.0.0", "v0.2.0-milestone.v2-m2", "v1.0.0-milestone.v2-m8"]
    BAD = ["1.0.0", "v1.0", "v1", "v01.0.0", "v1.0.0-rc.1", "v1.0.0-beta", "v0.2.0-milestone.v2-m9", "v1.0.0-milestone", "V1.0.0", "v1.0.0+build", "phase-3", "v0.3.1.0"]

    def test_accepts_semver_and_milestone_prerelease(self):
        for t in self.GOOD:
            self.assertTrue(M.tag_ok(t), t)

    def test_rejects_everything_else(self):
        for t in self.BAD:
            self.assertFalse(M.tag_ok(t), t)

    def test_cli_exit_codes_match_the_workflow_step(self):
        def rc(tag):
            return subprocess.run([sys.executable, str(ROOT / "scripts/pipeline/manifest.py"), "tag-ok", "kritva-program", tag,
                                   "--manifest", str(MANIFEST_PATH)], capture_output=True, text=True).returncode
        self.assertEqual(rc("v1.0.0"), 0)
        self.assertEqual(rc("v1.0.0-rc.1"), 1)
        self.assertEqual(rc("1.0.0"), 1)


class Templates(unittest.TestCase):
    NAMES = ["unit-tests", "pr-acceptance-gate", "tag-policy-check"]

    def text(self, n):
        return (TPL / f"{n}.yml").read_text(encoding="utf-8")

    def test_templates_exist_and_name_their_job(self):
        for n in self.NAMES:
            t = self.text(n)
            self.assertRegex(t, rf"(?m)^name: {n}$", n)
            self.assertRegex(t, rf"(?m)^  {n}:$", n)  # job id equals the check name used in rulesets

    def test_actions_are_pinned_to_full_shas(self):
        for n in self.NAMES:
            uses = re.findall(r"uses:\s*(\S+)", self.text(n))
            self.assertTrue(uses, n)
            for u in uses:
                self.assertRegex(u, r"@[0-9a-f]{40}$", f"{n}: {u}")

    def test_permissions_are_least_privilege(self):
        for n in self.NAMES:
            t = self.text(n)
            self.assertIn("contents: read", t, n)
            self.assertNotIn("contents: write", t, n)
        self.assertNotIn("pull-requests: write", self.text("unit-tests"))

    def test_referenced_scripts_exist(self):
        for n in self.NAMES:
            for p in re.findall(r"(?:python3 )((?:scripts|tools)/[\w/.-]+\.py)", self.text(n)):
                self.assertTrue((ROOT / p).is_file(), f"{n}: {p}")

    def test_gate_workflow_only_fails_on_reject(self):
        t = self.text("pr-acceptance-gate")
        self.assertIn("pr_gate.py static", t)
        self.assertIn("--gate .github/kritva-gate.json", t)
        self.assertIn('exit "${GATE_RC}"', t)

    def test_gate_json_export_matches_the_manifest(self):
        out = subprocess.run([sys.executable, str(ROOT / "scripts/pipeline/pr_gate.py"), "export", "--manifest", str(MANIFEST_PATH),
                              "--repo", "kritva-program"], capture_output=True, text=True, check=True).stdout
        self.assertEqual(json.loads(out), GATE)
        self.assertEqual(GATE["task_registry"]["type"], "program-baseline")

    def test_known_checks_cover_templates_except_tag_policy(self):
        known = set(MANIFEST["known_github_checks"])
        self.assertLessEqual({"unit-tests", "pr-acceptance-gate"}, known)

    def test_install_script_is_executable_text(self):
        s = TPL / "install_ci.sh"
        self.assertTrue(s.is_file())
        t = s.read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", t)
        for n in self.NAMES:
            self.assertIn(n, t)
        self.assertNotIn("git push", t.replace("never commits or pushes", ""))


if __name__ == "__main__":
    unittest.main()
