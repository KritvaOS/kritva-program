"""Tests for tools/task_scopes.py (D-164 step 2). No network."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import task_scopes as ts  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASE = {"baseline_version": 3, "tasks": [
    {"id": "A-1", "workstream_id": "CORE"}, {"id": "B-1", "workstream_id": "SENSE"}]}
SRC = {"sources": [{"workstream_id": "CORE"}, {"workstream_id": "SENSE"}]}


class Validate(unittest.TestCase):
    def reg(self):
        return ts.skeleton(BASE, SRC)

    def test_skeleton_is_valid(self):
        self.assertEqual(ts.validate(self.reg(), BASE, SRC), [])

    def test_missing_task_entry(self):
        r = self.reg(); del r["tasks"]["B-1"]
        self.assertTrue(any("B-1 has no scope entry" in p for p in ts.validate(r, BASE, SRC)))

    def test_unknown_task_and_repo(self):
        r = self.reg(); r["tasks"]["Z-9"] = {"workstream_id": "CORE", "review": "UNREVIEWED", "paths": []}
        r["repos"]["NOPE"] = {"review": "UNREVIEWED", "shared_paths": []}
        p = ts.validate(r, BASE, SRC)
        self.assertTrue(any("Z-9 is not a baselined task" in x for x in p))
        self.assertTrue(any("NOPE is not a workstream" in x for x in p))

    def test_missing_repo_entry(self):
        r = self.reg(); del r["repos"]["SENSE"]
        self.assertTrue(any("no entry for workstream SENSE" in p for p in ts.validate(r, BASE, SRC)))

    def test_baseline_version_mismatch(self):
        r = self.reg(); r["baseline_version"] = 2
        self.assertTrue(any("baseline_version" in p for p in ts.validate(r, BASE, SRC)))

    def test_workstream_mismatch(self):
        r = self.reg(); r["tasks"]["A-1"]["workstream_id"] = "SENSE"
        self.assertTrue(any("workstream_id" in p for p in ts.validate(r, BASE, SRC)))

    def test_reviewed_needs_paths(self):
        r = self.reg(); r["tasks"]["A-1"]["review"] = "REVIEWED"; r["repos"]["CORE"]["review"] = "REVIEWED"
        p = ts.validate(r, BASE, SRC)
        self.assertTrue(any("tasks.A-1: REVIEWED needs" in x for x in p))
        self.assertTrue(any("repos.CORE: REVIEWED needs" in x for x in p))
        r["tasks"]["A-1"]["paths"] = ["src/a/"]; r["repos"]["CORE"]["shared_paths"] = ["Makefile"]
        self.assertEqual(ts.validate(r, BASE, SRC), [])

    def test_bad_paths(self):
        for bad in ("/abs", "../x", "a/../b", "src/*.py", "", "./x", "a\\b"):
            r = self.reg(); r["tasks"]["A-1"]["paths"] = [bad]
            self.assertTrue(ts.validate(r, BASE, SRC), bad)
        r = self.reg(); r["tasks"]["A-1"]["paths"] = ["src/", "src/"]
        self.assertTrue(any("duplicate" in p for p in ts.validate(r, BASE, SRC)))

    def test_bad_review_value(self):
        r = self.reg(); r["tasks"]["A-1"]["review"] = "MAYBE"
        self.assertTrue(any("review must be" in p for p in ts.validate(r, BASE, SRC)))

    def test_matches(self):
        self.assertTrue(ts.matches("src/a/x.py", ["src/a/"]))
        self.assertTrue(ts.matches("Makefile", ["Makefile"]))
        self.assertFalse(ts.matches("src/ab/x.py", ["src/a/"]))
        self.assertFalse(ts.matches("src/a", ["src/a/"]))


class Cli(unittest.TestCase):
    def test_init_then_check_then_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            (r / "v2/tracking").mkdir(parents=True); (r / "v2/planning").mkdir(parents=True)
            (r / ts.BASELINE).write_text(json.dumps(BASE)); (r / ts.SOURCES).write_text(json.dumps(SRC))
            self.assertEqual(ts.main(["--root", d, "--init"]), 0)
            self.assertEqual(ts.main(["--root", d, "--check"]), 0)
            self.assertEqual(ts.main(["--root", d, "--init"]), 1)
            reg = json.loads((r / ts.REGISTRY).read_text()); reg["tasks"].pop("A-1")
            (r / ts.REGISTRY).write_text(json.dumps(reg))
            self.assertEqual(ts.main(["--root", d, "--check"]), 1)


class Impact(unittest.TestCase):
    STATUS = "status/status.json"
    REPO = {"review": "REVIEWED", "shared_paths": ["Makefile", ".github/workflows/"]}

    def tasks(self):
        return {"A-1": {"review": "REVIEWED", "paths": ["src/a/", "docs/a.md"]},
                "A-2": {"review": "REVIEWED", "paths": ["src/b/"]}}

    def run_it(self, files, relation="AHEAD", truncated=False, repo=None, tasks=None):
        return ts.classify_impact(files, truncated, relation, self.STATUS, repo or self.REPO, tasks or self.tasks(), {"gen_status.py"})

    def states(self, r):
        return {k: v["state"] for k, v in r.items()}

    def test_status_only_gap_is_current(self):
        r = self.run_it(["status/status.json", "status/evidence.json"])
        self.assertEqual(self.states(r), {"A-1": "CURRENT", "A-2": "CURRENT"})

    def test_identical_is_current(self):
        self.assertEqual(self.states(self.run_it([], relation="IDENTICAL")), {"A-1": "CURRENT", "A-2": "CURRENT"})

    def test_task_scope_affects_only_that_task(self):
        r = self.run_it(["src/a/x.c", "README.md"])
        self.assertEqual(self.states(r), {"A-1": "AFFECTED", "A-2": "CURRENT"})
        self.assertEqual(r["A-1"]["classes"], ["TASK_SCOPE"])
        self.assertEqual(r["A-1"]["files"], ["src/a/x.c"])

    def test_shared_affects_every_task(self):
        r = self.run_it(["Makefile"])
        self.assertEqual(self.states(r), {"A-1": "AFFECTED", "A-2": "AFFECTED"})
        self.assertEqual(r["A-2"]["classes"], ["TASK_SHARED"])

    def test_tooling_is_report_integrity(self):
        r = self.run_it(["scripts/gen_status.py"])
        self.assertEqual(r["A-1"]["classes"], ["REPORT_INTEGRITY"])
        self.assertEqual(self.states(r), {"A-1": "AFFECTED", "A-2": "AFFECTED"})

    def test_classes_combine_and_sort(self):
        r = self.run_it(["src/a/x.c", "Makefile"])
        self.assertEqual(r["A-1"]["classes"], ["TASK_SCOPE", "TASK_SHARED"])
        self.assertEqual(r["A-2"]["classes"], ["TASK_SHARED"])

    def test_file_in_no_scope_affects_nothing(self):
        self.assertEqual(self.states(self.run_it(["docs/other.md"])), {"A-1": "CURRENT", "A-2": "CURRENT"})

    def test_unknown_relation_and_truncation_fail_closed(self):
        self.assertEqual(set(self.states(self.run_it([], relation="UNKNOWN")).values()), {"UNKNOWN"})
        self.assertEqual(set(self.states(self.run_it(["src/a/x.c"], truncated=True)).values()), {"UNKNOWN"})

    def test_unreviewed_repo_fails_closed_on_non_status_change(self):
        repo = {"review": "UNREVIEWED", "shared_paths": []}
        self.assertEqual(set(self.states(self.run_it(["src/a/x.c"], repo=repo)).values()), {"UNKNOWN"})
        self.assertEqual(set(self.states(self.run_it(["status/status.json"], repo=repo)).values()), {"CURRENT"})

    def test_unreviewed_task_fails_closed(self):
        tasks = self.tasks(); tasks["A-2"]["review"] = "UNREVIEWED"
        r = self.run_it(["docs/other.md"], tasks=tasks)
        self.assertEqual(self.states(r), {"A-1": "CURRENT", "A-2": "UNKNOWN"})

    def test_file_list_is_capped_per_task(self):
        r = self.run_it([f"src/a/{i}.c" for i in range(9)])
        self.assertEqual(len(r["A-1"]["files"]), 5)


class RealRepo(unittest.TestCase):
    def test_registry_matches_baseline(self):
        """Fails when a baseline change adds or removes a task without updating the registry."""
        p = ts.validate(ts.load(ROOT / ts.REGISTRY), ts.load(ROOT / ts.BASELINE), ts.load(ROOT / ts.SOURCES))
        self.assertEqual(p, [])


if __name__ == "__main__":
    unittest.main()
