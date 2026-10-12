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
                f"| I2-001 | Done (`{full[:9]}`) |\n| I2-002 | Done (`deadbee`) |\n| I2-003 | no sha here 2026 |\n| I2-004, I2-005 | shared (`{full[:8]}`) |\n")
            out = r / "o.json"
            p = subprocess.run([sys.executable, str(ROOT / "tools/resolve_shas.py"), "--repo", str(r), "--tag", "v1",
                                "--out", str(out)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            doc = json.loads(out.read_text())
            self.assertEqual(doc["tasks"]["I2-001"][0]["full"], full)
            self.assertEqual(doc["tags"]["v1"], full)  # annotated tag peeled to the commit
            self.assertEqual([u["task"] for u in doc["unresolved_or_ambiguous"]], ["I2-002"])
            self.assertNotIn("I2-003", doc["tasks"])
            self.assertNotIn("I2-004", doc["tasks"])  # multi-task lines are never attributed to a task
            self.assertIn(full, doc["milestone_level_commits"])

    def test_ci_runs_in_checkout_and_covering_runs(self):
        import os, stat
        with tempfile.TemporaryDirectory() as d:
            r = Path(d) / "repo"; r.mkdir()
            g(r, "init", "-q", "-b", "main")
            (r / "t.txt").write_text("1"); g(r, "add", "."); g(r, "commit", "-q", "-m", "task")
            c1 = g(r, "rev-parse", "HEAD")
            (r / "other.txt").write_text("2"); g(r, "add", "."); g(r, "commit", "-q", "-m", "later")
            c2 = g(r, "rev-parse", "HEAD")
            (r / "t.txt").write_text("3"); g(r, "add", "."); g(r, "commit", "-q", "-m", "touch task file")
            c3 = g(r, "rev-parse", "HEAD")
            (r / "planning").mkdir()
            (r / "planning/S.md").write_text(f"| I2-001 | Done (`{c1[:9]}`) |\n| I2-002 | Done (`{c3[:9]}`) |\n")
            cwdlog = Path(d) / "cwd.log"
            runs = [{"databaseId": 1, "workflowName": "CI", "conclusion": "success", "status": "completed",
                     "url": "u1", "headSha": c2, "event": "push", "createdAt": "x"},
                    {"databaseId": 2, "workflowName": "CI", "conclusion": "success", "status": "completed",
                     "url": "u2", "headSha": c3, "event": "push", "createdAt": "x"},
                    {"databaseId": 3, "workflowName": "Bad", "conclusion": "failure", "status": "completed",
                     "url": "u3", "headSha": c3, "event": "push", "createdAt": "x"}]
            bindir = Path(d) / "bin"; bindir.mkdir()
            fake = bindir / "gh"
            fake.write_text("#!/bin/sh\npwd >> '%s'\nif echo \"$@\" | grep -q -- --commit; then echo '[]'; else cat <<'EOF2'\n%s\nEOF2\nfi\n"
                            % (cwdlog, json.dumps(runs)))
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
            out = Path(d) / "o.json"
            env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}")
            p = subprocess.run([sys.executable, str(ROOT / "tools/resolve_shas.py"), "--repo", str(r), "--ci",
                                "--covering-runs", "50", "--out", str(out)], capture_output=True, text=True, env=env)
            self.assertEqual(p.returncode, 0, p.stderr)
            item = json.loads(out.read_text())["tasks"]["I2-001"][0]
            self.assertEqual(item["ci_runs"], [])  # explicit "no runs", not a lookup failure
            cov = item["covering_runs"]
            self.assertEqual(len(cov), 1)  # failure run ignored; one entry per workflow
            self.assertEqual(cov[0]["head_sha"], c2)  # nearest descendant wins
            self.assertEqual(cov[0]["commits_after"], 1)
            self.assertEqual(cov[0]["task_files_changed_after"], [])
            later = json.loads(out.read_text())["tasks"]["I2-002"][0]["covering_runs"]
            self.assertEqual([c["head_sha"] for c in later], [c3])  # run on older c2 must NOT cover task at c3
            self.assertEqual(later[0]["commits_after"], 0)
            self.assertTrue(all(Path(x).resolve() == r.resolve() for x in cwdlog.read_text().split()))


if __name__ == "__main__":
    unittest.main()
