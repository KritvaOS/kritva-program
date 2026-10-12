"""Test tools/resolve_shas.py against a throwaway git repo."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def g(repo, *a):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                          capture_output=True, text=True, check=True).stdout.strip()


class Resolve(unittest.TestCase):
    def test_resolves_flags_unresolved_and_peels_tags(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            g(r, "init", "-q", "-b", "main")
            (r / "a.txt").write_text("x")
            g(r, "add", "."); g(r, "commit", "-q", "-m", "first")
            full = g(r, "rev-parse", "HEAD")
            g(r, "tag", "-a", "v1", "-m", "annotated")
            (r / "planning").mkdir()
            (r / "planning/S.md").write_text(
                f"| I2-001 | Done (`{full[:9]}`) |\n| I2-002 | Done (`deadbee`) |\n| I2-003 | no sha here 2026 |\n")
            out = r / "o.json"
            p = subprocess.run([sys.executable, str(ROOT / "tools/resolve_shas.py"), "--repo", str(r), "--tag", "v1",
                                "--out", str(out)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            doc = json.loads(out.read_text())
            self.assertEqual(doc["tasks"]["I2-001"][0]["full"], full)
            self.assertEqual(doc["tags"]["v1"], full)  # annotated tag peeled to the commit
            self.assertEqual([u["task"] for u in doc["unresolved_or_ambiguous"]], ["I2-002"])
            self.assertNotIn("I2-003", doc["tasks"])


if __name__ == "__main__":
    unittest.main()
