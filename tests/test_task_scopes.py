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


class RealRepo(unittest.TestCase):
    def test_registry_matches_baseline(self):
        """Fails when a baseline change adds or removes a task without updating the registry."""
        p = ts.validate(ts.load(ROOT / ts.REGISTRY), ts.load(ROOT / ts.BASELINE), ts.load(ROOT / ts.SOURCES))
        self.assertEqual(p, [])


if __name__ == "__main__":
    unittest.main()
