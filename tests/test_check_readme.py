#!/usr/bin/env python3
"""Tests for scripts/docs/check_readme.py and the README standard files (D-055)."""
import subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "docs"))
import check_readme as C  # noqa: E402

FIELDS = "".join(f"| {f} | value |\n" for f in C.FIELDS)
HEADS = "\n".join(f"## {h}\n\ntext\n" for h in (
    "Purpose and Scope", "Position in the Ecosystem", "Architecture", "Documents to Read", "Repository Structure",
    "Tool and Development Workflow", "Dependencies", "Milestones", "Tasks and Acceptance", "Status Reporting",
    "Validation and Regression", "Git Workflow", "Safety and Security", "Release and Versioning", "Ownership",
    "Related Repositories", "License"))
GOOD = f"# r\n\n> d\n\n| Property | Value |\n|---|---|\n{FIELDS}\n{HEADS}"


class CheckReadme(unittest.TestCase):
    def run_check(self, text, files=()):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for f in files:
                (d / f).parent.mkdir(parents=True, exist_ok=True)
                (d / f).write_text("x")
            (d / "README.md").write_text(text)
            return C.check(d / "README.md", d)

    def test_complete_readme_passes(self):
        self.assertEqual(self.run_check(GOOD), [])

    def test_missing_metadata_field_fails(self):
        bad = GOOD.replace("| GitHub Setting | value |\n", "")
        self.assertIn("metadata field missing: GitHub Setting", self.run_check(bad))

    def test_empty_metadata_field_fails(self):
        bad = GOOD.replace("| Tasks | value |", "| Tasks |  |")
        self.assertIn("metadata field empty: Tasks", self.run_check(bad))

    def test_missing_topic_fails(self):
        bad = GOOD.replace("## Release and Versioning", "## Misc")
        self.assertIn("no heading for: release and versioning", self.run_check(bad))

    def test_broken_link_fails_and_good_link_passes(self):
        self.assertTrue(any("does not resolve: docs/a.md" in p for p in self.run_check(GOOD + "\n[a](docs/a.md)\n")))
        self.assertEqual(self.run_check(GOOD + "\n[a](docs/a.md#top) [w](https://example.com/x) [h](#top)\n", ["docs/a.md"]), [])

    def test_placeholder_fails_but_code_is_ignored(self):
        self.assertTrue(any("placeholder" in p for p in self.run_check(GOOD + "\nSee <repository-name>\n")))
        self.assertTrue(any("placeholder" in p for p in self.run_check(GOOD + "\nTODO\n")))
        self.assertEqual(self.run_check(GOOD + "\n```\n<repo> [x](nope.md) TODO\n```\nand `<y>` `[z](nope)`\n"), [])
        self.assertEqual(self.run_check(GOOD + "\nExample:\n\n    feat(x): <imperative summary> [<TASK-ID>]\n"), [])
        self.assertTrue(any("does not resolve" in p for p in self.run_check(GOOD + "\n    see [a](nope.md)\n")))


class Repository(unittest.TestCase):
    def test_program_readme_passes(self):
        self.assertEqual(C.check(ROOT / "README.md", ROOT), [])

    def test_cli_exit_codes(self):
        run = lambda *a: subprocess.run([sys.executable, str(ROOT / "scripts/docs/check_readme.py"), *a], capture_output=True, text=True)
        self.assertEqual(run(str(ROOT / "README.md")).returncode, 0)
        self.assertEqual(run(str(ROOT / "nope.md")).returncode, 1)

    def test_standard_files_exist_and_link_each_other(self):
        d = ROOT / "v2/planning/standards"
        names = ["README_STANDARD.md", "README_TEMPLATE_PUBLIC.md", "README_TEMPLATE_PRIVATE.md", "DOCUMENT_HEADER_STANDARD.md",
                 "README_REVIEW_CHECKLIST.md", "README_MIGRATION_PLAN.md"]
        for n in names:
            self.assertTrue((d / n).is_file(), n)
        std = (d / "README_STANDARD.md").read_text(encoding="utf-8")
        for n in names[1:]:
            self.assertIn(n, std)

    def test_templates_carry_every_metadata_field(self):
        for n in ("README_TEMPLATE_PUBLIC.md", "README_TEMPLATE_PRIVATE.md"):
            t = (ROOT / "v2/planning/standards" / n).read_text(encoding="utf-8")
            for f in C.FIELDS:
                self.assertIn(f"| {f} |", t, f"{n}: {f}")


if __name__ == "__main__":
    unittest.main()
