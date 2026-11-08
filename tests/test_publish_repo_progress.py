"""Tests for tools/publish_repo_progress.py and the repo template tools/repo-templates/progress_report.py (D-120)."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import publish_repo_progress as pub  # noqa: E402

_spec = importlib.util.spec_from_file_location("progress_report", ROOT / "tools/repo-templates/progress_report.py")
pr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr)

DATA = json.loads((ROOT / "v2/tracking/consolidated_status.json").read_text(encoding="utf-8"))


class Snapshots(unittest.TestCase):
    def test_every_repository_in_the_register_gets_a_snapshot(self):
        snaps = pub.build_all(DATA)
        self.assertEqual(set(snaps), set(DATA["plan_register"]["by_repo"]))
        for k in pub.REPOS:
            self.assertIn(k, snaps)

    def test_repository_figures_add_up_to_the_program_totals(self):
        snaps = pub.build_all(DATA)
        acc = sum(a for a, _ in pub.summary(snaps).values())
        tot = sum(t for _, t in pub.summary(snaps).values())
        t = pub._db.totals(DATA)
        self.assertEqual((acc, tot), (t["acc"], t["tot"]))

    def test_each_repository_matches_the_repository_table(self):
        s = DATA["plan_register"]
        fnd = pub._db._foundation_by_repo(DATA)
        for k, (acc, tot) in pub.summary(pub.build_all(DATA)).items():
            v = s["by_repo"][k]
            f = fnd.get(k, [0, 0, 0, 0])
            self.assertEqual((acc, tot), (f[0] + v["accepted"], f[1] + v["baseline"] + v["point"]), k)

    def test_snapshots_validate_and_render(self):
        for k, snap in pub.build_all(DATA).items():
            if k not in pub.REPOS:
                continue
            self.assertEqual(pr.validate(snap), [], k)
            self.assertIn(snap["repository"], pr.render(snap))

    def test_missing_register_is_refused(self):
        bad = copy.deepcopy(DATA)
        bad["plan_register"] = None
        with self.assertRaises(ValueError):
            pub.build(bad, "Core")


class Template(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "kritva-sense"
        (self.root / "status").mkdir(parents=True)
        (self.root / "status/status.json").write_text(json.dumps({"repo": "KritvaOS/kritva-sense"}))
        self.snap = pub.build(DATA, "Sense")
        (self.root / "status/program_snapshot.json").write_text(json.dumps(self.snap))

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *args):
        return pr.main(["--root", str(self.root), *args])

    def test_write_then_check_passes(self):
        self.assertEqual(self.run_main("--write"), 0)
        self.assertEqual(self.run_main("--check"), 0)

    def test_check_fails_when_the_report_is_edited(self):
        self.run_main("--write")
        p = self.root / "status/STATUS.md"
        p.write_text(p.read_text().replace("Accepted weight", "Accepted weight (edited)"))
        self.assertEqual(self.run_main("--check"), 1)

    def test_check_fails_when_the_report_is_missing(self):
        self.assertEqual(self.run_main("--check"), 1)

    def test_check_fails_when_the_snapshot_changes_and_report_does_not(self):
        self.run_main("--write")
        snap = copy.deepcopy(self.snap)
        snap["milestones"]["M2"]["accepted"] = 0
        (self.root / "status/program_snapshot.json").write_text(json.dumps(snap))
        self.assertEqual(self.run_main("--check"), 1)

    def test_snapshot_for_another_repository_is_refused(self):
        snap = copy.deepcopy(self.snap)
        snap["repository"] = "KritvaOS/kritva-mind"
        (self.root / "status/program_snapshot.json").write_text(json.dumps(snap))
        self.assertEqual(self.run_main("--write"), 1)

    def test_accepted_above_total_is_refused(self):
        snap = copy.deepcopy(self.snap)
        snap["milestones"]["M2"]["accepted"] = 999
        self.assertTrue(pr.validate(snap))

    def test_unknown_schema_is_refused(self):
        snap = copy.deepcopy(self.snap)
        snap["schema_version"] = 2
        self.assertTrue(pr.validate(snap))

    def test_old_snapshot_warns_but_does_not_fail(self):
        import datetime as dt
        far = dt.datetime(2027, 1, 1, tzinfo=dt.timezone.utc)
        self.assertIn("days old", pr.age_warning(self.snap, now=far))
        self.assertIsNone(pr.age_warning(self.snap, now=dt.datetime(2026, 11, 9, tzinfo=dt.timezone.utc)))

    def test_report_keeps_the_four_states_apart(self):
        text = pr.render(self.snap)
        for word in ("Execution", "Evidence", "Acceptance", "Release readiness"):
            self.assertIn(f"| {word} |", text)
        self.assertIn("never approves anything", text)

    def test_publish_writes_the_four_files_per_repository(self):
        with tempfile.TemporaryDirectory() as d:
            for _r, folder, _w in pub.REPOS.values():
                (Path(d) / folder).mkdir()
            done = pub.write(pub.build_all(DATA), d)
            self.assertEqual(len(done), 6)
            for folder in done:
                for rel in ("status/program_snapshot.json", "status/STATUS.md", "scripts/progress_report.py",
                            ".github/workflows/progress-check.yml"):
                    self.assertTrue((Path(d) / folder / rel).is_file(), f"{folder}/{rel}")
                self.assertEqual(pr.main(["--root", str(Path(d) / folder), "--check"]), 0)


class Only(unittest.TestCase):
    def test_only_writes_the_named_repository(self):
        with tempfile.TemporaryDirectory() as d:
            for _r, folder, _w in pub.REPOS.values():
                (Path(d) / folder).mkdir()
            done = pub.write(pub.build_all(DATA), d, only=["kritva-mind"])
            self.assertEqual(done, ["kritva-mind"])
            self.assertFalse((Path(d) / "kritva-sense/status").exists())
            self.assertTrue((Path(d) / "kritva-mind/scripts/progress_report.py").stat().st_mode & 0o111)


class TemplateHygiene(unittest.TestCase):
    def test_workflow_actions_are_pinned_to_full_commit_ids(self):
        import re
        for line in (ROOT / "tools/repo-templates/progress-check.yml").read_text().splitlines():
            m = re.search(r"uses:\s*\S+@(\S+)", line)
            if m:
                self.assertRegex(m.group(1), r"^[0-9a-f]{40}$", line)

    def test_workflow_pins_name_their_version_tag(self):
        import re
        for line in (ROOT / "tools/repo-templates/progress-check.yml").read_text().splitlines():
            if "uses:" in line:
                self.assertRegex(line, r"uses:\s*[\w.-]+/[\w.-]+@[0-9a-f]{40}\s+# v\d+\s*$", line)

    def test_workflow_template_has_the_standard_source_header(self):
        text = "\n".join((ROOT / "tools/repo-templates/progress-check.yml").read_text().splitlines()[:20])
        for field in ("File", "Description", "Component", "Module", "Layer", "Requirements", "API", "Author", "Created"):
            self.assertRegex(text, rf"#\s*{field}\s*:\s*\S")
        self.assertIn("SPDX-License-Identifier: Apache-2.0", text)
        self.assertIn("Copyright (c) 2026 KritvaOS", text)
        self.assertRegex(text, r"Created\s*:\s*\d\d-\d\d-\d{4}")

    def test_template_has_the_standard_source_header(self):
        head = (ROOT / "tools/repo-templates/progress_report.py").read_text().splitlines()[:20]
        text = "\n".join(head)
        for field in ("File", "Description", "Component", "Module", "Layer", "Requirements", "API", "Author", "Created"):
            self.assertRegex(text, rf"#\s*{field}\s*:")
        self.assertIn("SPDX-License-Identifier: Apache-2.0", text)


if __name__ == "__main__":
    unittest.main()
