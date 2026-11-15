#!/usr/bin/env python3
"""Tests for tools/engineering_compliance.py (KRP-ENG-001): the report records facts and flags what is missing."""
import base64, json, sys, tempfile, unittest
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


BODY = '"""Check the V2 commit format."""\nimport sys\n'


def with_files(files, base_run=None):
    """Extend fake() so contents/<checker path> returns base64 text from files[(repo, path)], or 404."""
    inner = base_run or fake()

    def run(*a):
        s = " ".join(a)
        if "/contents/scripts/security/" in s:
            repo = next(r for r in E.REPOS if f"/{r}/" in s)
            path = s.split("/contents/")[1].split("?")[0]
            if (repo, path) not in files:
                raise RuntimeError("gh: Not Found (HTTP 404)")
            return base64.b64encode(files[(repo, path)].encode()).decode()
        return inner(*a)
    return run


def all_files(**overrides):
    f = {(r, c): BODY for r in E.REPOS for c in E.CHECKERS}
    f.update(overrides)
    return f


class Drift(unittest.TestCase):
    def test_body_hash_ignores_the_header_block(self):
        header = "#!/usr/bin/env python3\n# Copyright (c) 2026 Somebody\n# SPDX-License-Identifier: X\n"
        self.assertEqual(E.body_sha256(header + BODY), E.body_sha256("#!/usr/bin/env python3\n" + BODY))
        self.assertNotEqual(E.body_sha256(BODY), E.body_sha256(BODY + "x = 1\n"))
        self.assertIsNone(E.body_sha256("no docstring here\n"))

    def test_default_collect_does_not_read_checkers(self):
        rep = E.collect(fake(), now="2026-11-15T00:00:00Z")
        self.assertNotIn("checkers", rep["repos"][0])
        self.assertNotIn("Commit checker drift", E.render(rep))

    def test_matching_copies_with_different_headers_are_not_drift(self):
        f = all_files()
        f[("kritva-core", E.CHECKERS[0])] = "# Copyright (c) 2026 KritvaOS\n" + BODY
        rep = E.collect(with_files(f), with_checkers=True)
        core = next(r for r in rep["repos"] if r["repo"] == "kritva-core")
        self.assertTrue(core["checkers"][E.CHECKERS[0]]["matches_base"])
        self.assertNotIn("differs from the kritva-program copy", E.render(rep))

    def test_changed_body_is_flagged_as_drift(self):
        f = all_files()
        f[("kritva-mind", E.CHECKERS[1])] = BODY + "x = 1\n"
        rep = E.collect(with_files(f), with_checkers=True)
        md = E.render(rep)
        self.assertIn("kritva-mind check_commit_messages.py differs from the kritva-program copy", md)
        self.assertIn("DIFFERS", md)

    def test_missing_file_is_reported_and_core_missing_is_a_gap(self):
        f = all_files()
        del f[("kritva-core", E.CHECKERS[0])]
        del f[("kritva-sense", E.CHECKERS[0])]
        md = E.render(E.collect(with_files(f), with_checkers=True))
        self.assertIn("kritva-core has no check_commit_format.py", md)
        self.assertNotIn("kritva-sense has no check_commit_format.py", md)
        self.assertIn("missing", md)

    def test_check_still_passes_on_files_without_checker_data(self):
        rep = E.collect(fake(), now="2026-11-15T00:00:00Z")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for p in (E.JSON_OUT, E.MD_OUT):
                (root / p).parent.mkdir(parents=True, exist_ok=True)
            (root / E.JSON_OUT).write_text(json.dumps(rep))
            (root / E.MD_OUT).write_text(E.render(rep))
            self.assertEqual(E.main(["--root", d, "--check"]), 0)


if __name__ == "__main__":
    unittest.main()
