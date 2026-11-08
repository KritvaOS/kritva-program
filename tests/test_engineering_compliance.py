#!/usr/bin/env python3
"""Tests for tools/engineering_compliance.py (KRP-ENG-001): the report records facts and flags what is missing."""
import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import engineering_compliance as E  # noqa: E402

SHA = "a" * 40


def fake(missing_agents=(), no_workflow=None, rules=True):
    def run(*a):
        s = " ".join(a)
        repo = next((r for r in E.REPOS if f"/{r}" in s), "")
        if s.endswith("--jq {default_branch: .default_branch, private: .private}"):
            return json.dumps({"default_branch": "main", "private": False})
        if "/commits/" in s:
            return SHA + "\n"
        if "contents/.github/workflows" in s:
            names = [f"{w}.yml" for w in E.WORKFLOWS if not (no_workflow and (repo, w) == no_workflow)]
            return json.dumps(names)
        if "/contents/" in s:
            path = s.split("/contents/")[1].split(" ")[0]
            if path in E.AGENT_FILES and (repo, path) in [(r, "AGENTS.md") for r in missing_agents] + [(r, "CLAUDE.md") for r in E.REPOS]:
                raise RuntimeError("gh: Not Found (HTTP 404)")
            return "x"
        if s.endswith("/rulesets --jq [.[] | {id, enforcement}]"):
            if not rules:
                raise RuntimeError("HTTP 403")
            return json.dumps([{"id": 1, "enforcement": "active"}, {"id": 2, "enforcement": "disabled"}])
        if "/rulesets/1" in s:
            return json.dumps({"rules": [{"type": "required_status_checks", "parameters": {"required_status_checks": [{"context": "secret-scan"}]}}]})
        raise AssertionError(s)
    return run


class Collect(unittest.TestCase):
    def test_complete_report_has_no_gaps(self):
        rep = E.collect(fake(), now="2026-11-08T00:00:00Z")
        self.assertEqual([r["repo"] for r in rep["repos"]], E.REPOS)
        self.assertEqual(E.problems(rep), [])
        self.assertEqual(rep["repos"][0]["required_checks"], ["secret-scan"])  # disabled ruleset ignored
        self.assertTrue(next(r for r in rep["repos"] if r["repo"] == "kritva-core")["contract_pin"])
        self.assertIn("None in the agent file", E.render(rep))

    def test_missing_agent_file_is_flagged(self):
        rep = E.collect(fake(missing_agents=["kritva-mind"]))
        mind = next(r for r in rep["repos"] if r["repo"] == "kritva-mind")
        self.assertEqual(mind["agent_files"], [])
        md = E.render(rep)
        self.assertIn("| MISSING |", md)
        self.assertIn("kritva-mind has no AGENTS.md or CLAUDE.md", md)

    def test_missing_enforcement_workflow_is_flagged(self):
        rep = E.collect(fake(no_workflow=("kritva-skill", "secret-scan")))
        self.assertIn("kritva-skill has no secret-scan workflow", E.render(rep))

    def test_unreadable_rulesets_are_reported_not_invented(self):
        rep = E.collect(fake(rules=False))
        self.assertIsNone(rep["repos"][0]["required_checks"])
        self.assertIn("not readable", E.render(rep))


class Check(unittest.TestCase):
    def test_check_passes_for_matching_files_and_fails_on_drift(self):
        rep = E.collect(fake(), now="2026-11-08T00:00:00Z")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for p in (E.JSON_OUT, E.MD_OUT):
                (root / p).parent.mkdir(parents=True, exist_ok=True)
            (root / E.JSON_OUT).write_text(json.dumps(rep))
            (root / E.MD_OUT).write_text(E.render(rep))
            self.assertEqual(E.main(["--root", d, "--check"]), 0)
            (root / E.MD_OUT).write_text("edited by hand")
            self.assertEqual(E.main(["--root", d, "--check"]), 1)

    def test_wrong_repository_list_is_a_problem(self):
        rep = E.collect(fake(), repos=E.REPOS[:3])
        self.assertTrue(E.problems(rep))


if __name__ == "__main__":
    unittest.main()
