#!/usr/bin/env python3
"""Tests for scripts/pipeline/ship.sh and the Makefile ship target (print mode only; nothing is pushed)."""
import subprocess, tarfile, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SH = str(ROOT / "scripts/pipeline/ship.sh")


def ship(*a):
    return subprocess.run(["bash", SH, *a], capture_output=True, text=True)


class Ship(unittest.TestCase):
    def folder(self, t, repos):
        for r in repos:
            (Path(t) / r).mkdir()
            (Path(t) / r / "0001-x.patch").write_text("p")
        (Path(t) / "empty").mkdir()
        return t

    def test_discovers_repos_and_passes_safe_flags(self):
        with tempfile.TemporaryDirectory() as t:
            self.folder(t, ["kritva-sense", "kritva-program"])
            r = ship("--patches", t, "--branch", "feat/x", "--print")
            self.assertEqual(r.returncode, 0, r.stderr)
            o = r.stdout
            for need in ("--admin", "--go", "--manifest", "repo-pipeline.json", "--branch feat/x", f"--patches {t}"):
                self.assertIn(need, o)
            self.assertIn("kritva-program", o)
            self.assertIn("kritva-sense", o)
            self.assertNotIn("empty", o)

    def test_dry_drops_go_and_only_limits_repos(self):
        with tempfile.TemporaryDirectory() as t:
            self.folder(t, ["kritva-sense", "kritva-program"])
            o = ship("--patches", t, "--branch", "b", "--only", "kritva-program", "--dry", "--print").stdout
            self.assertNotIn("--go", o)
            self.assertNotIn("kritva-sense", o)

    def test_tar_is_extracted_under_tmp_not_in_cwd(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "src/kritva-program"; src.mkdir(parents=True); (src / "0001-a.patch").write_text("p")
            tgz = Path(t) / "x.tar.gz"
            with tarfile.open(tgz, "w:gz") as f:
                f.add(src, arcname="kritva-program/")
            r = ship("--tar", str(tgz), "--branch", "b", "--print")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("--patches /tmp/ship.", r.stdout)

    def test_errors(self):
        self.assertEqual(ship("--patches", "/tmp").returncode, 2)  # no branch
        self.assertEqual(ship("--branch", "b").returncode, 2)  # no source
        self.assertEqual(ship("--branch", "b", "--tar", "/nope.tgz").returncode, 2)
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(ship("--branch", "b", "--patches", t).returncode, 2)  # no patches
            self.assertEqual(ship("--branch", "b", "--patches", t, "--tar", t).returncode, 2)  # both

    def test_makefile_dispatch(self):
        w = subprocess.run(["make", "-n", "-s", "ship", "TAR=/x.tgz", "BRANCH=feat/x", "ONLY=kritva-program", "DRY=1"], cwd=ROOT, capture_output=True, text=True).stdout
        for need in ('--branch "feat/x"', '--tar "/x.tgz"', '--only "kritva-program"', "--dry"):
            self.assertIn(need, w)


if __name__ == "__main__":
    unittest.main()
