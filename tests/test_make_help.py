#!/usr/bin/env python3
"""Tests for the Makefile help text and the pr-open / pr-land helpers (dry runs and refusals only; nothing is pushed)."""
import io, os, re, subprocess, tarfile, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SH = ROOT / "scripts" / "pipeline"


def run(*cmd, cwd=ROOT):
    return subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True)


def tarball(d, names):
    p = Path(d) / "t.tar.gz"
    with tarfile.open(p, "w:gz") as t:
        for n in names:
            data = b"x\n"; ti = tarfile.TarInfo(n); ti.size = len(data); t.addfile(ti, io.BytesIO(data))
    return str(p)


class MakeHelp(unittest.TestCase):
    def test_help_is_the_default_and_documents_every_command(self):
        out = run("make").stdout
        self.assertIn("Usage: make", out)
        mk = (ROOT / "Makefile").read_text(encoding="utf-8")
        phony = re.search(r"^\.PHONY:(.*)$", mk, re.M).group(1).split()
        for t in phony:
            if t not in ("all", "help"):
                self.assertRegex(out, rf"(?m)^  {re.escape(t)}\b", f"make help does not document {t}")

    def test_every_phony_target_has_a_rule(self):
        mk = (ROOT / "Makefile").read_text(encoding="utf-8")
        for t in re.search(r"^\.PHONY:(.*)$", mk, re.M).group(1).split():
            self.assertRegex(mk, rf"(?m)^{re.escape(t)}:", t)

    def test_pr_open_dispatch(self):
        w = run("make", "-n", "-s", "pr_open", "TAR=/x.tgz", "BRANCH=chore/x", "MSG=hello world", "DRY=1").stdout
        self.assertIn('--tar "/x.tgz" --branch "chore/x" --msg "hello world"', w)
        self.assertIn("--dry", w)

    def test_scripts_are_executable(self):
        for n in ("pr-open.sh", "pr-land.sh", "merge-pr.sh", "ship.sh", "ship-prs.sh"):
            self.assertTrue(os.access(SH / n, os.X_OK), f"{n} is not executable")


class PrOpen(unittest.TestCase):
    def test_needs_all_three_inputs(self):
        r = run(str(SH / "pr-open.sh"), "--tar", "x")
        self.assertEqual(r.returncode, 2); self.assertIn("BRANCH=", r.stderr)

    def test_missing_tarball(self):
        r = run(str(SH / "pr-open.sh"), "--tar", "/nonexistent.tgz", "--branch", "chore/x", "--msg", "m")
        self.assertEqual(r.returncode, 1); self.assertIn("not found", r.stderr)

    def test_refuses_main_as_branch(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(str(SH / "pr-open.sh"), "--tar", tarball(d, ["a.txt"]), "--branch", "main", "--msg", "m")
        self.assertEqual(r.returncode, 1); self.assertIn("not main", r.stderr)

    def test_refuses_path_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            for bad in ("../evil.txt", "/etc/evil.txt", "a/../../evil.txt"):
                r = run(str(SH / "pr-open.sh"), "--tar", tarball(d, [bad]), "--branch", "chore/x", "--msg", "m", "--dry")
                self.assertEqual(r.returncode, 1, bad); self.assertIn("refusing", r.stderr)

    def test_dry_run_lists_files_and_changes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(str(SH / "pr-open.sh"), "--tar", tarball(d, ["v2/a.txt"]), "--branch", "chore/x", "--msg", "m", "--dry")
        self.assertEqual(r.returncode, 0); self.assertIn("v2/a.txt", r.stdout); self.assertIn("Nothing changed", r.stdout)


class PrLand(unittest.TestCase):
    def test_help_and_unknown_option(self):
        self.assertEqual(run(str(SH / "pr-land.sh"), "--help").returncode, 0)
        self.assertEqual(run(str(SH / "pr-land.sh"), "--bogus").returncode, 2)


if __name__ == "__main__":
    unittest.main()
