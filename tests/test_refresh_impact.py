"""Tests for the per-task impact that tools/refresh_sources.py records in MANIFEST.json (D-164 step 4). No network."""
import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import consolidate_status as cs  # noqa: E402
import refresh_sources as rs  # noqa: E402
import task_scopes as ts  # noqa: E402

REPORT, HEAD, REPO = "d" * 40, "e" * 40, "KritvaOS/kritva-core"
BASE = {"baseline_version": 5, "tasks": [{"id": "A-1", "workstream_id": "CORE"}, {"id": "A-2", "workstream_id": "CORE"}]}
SRC = {"status_path": "status/status.json", "freshness_days": 14, "sources": [{"workstream_id": "CORE", "repo": REPO, "ref": "main"}]}
DOC = {"schema_version": "2.0", "workstream_id": "CORE", "repo": REPO, "source": {"commit": REPORT},
       "tasks": [{"task_id": "A-1"}, {"task_id": "A-2"}], "updated_at": "2026-11-28T00:00:00Z"}


def fake(files, status="ahead"):
    api = {f"repos/{REPO}/commits/main": {"sha": HEAD},
           f"repos/{REPO}/contents/status/status.json?ref={HEAD}": {"content": base64.b64encode(json.dumps(DOC).encode()).decode()},
           f"repos/{REPO}/compare/{REPORT}...{HEAD}": {"status": status, "ahead_by": len(files), "total_commits": 1, "commits": [{}],
                                                       "files": [{"filename": f} for f in files]}}
    return lambda *a: api.get(a[0])


class RefreshImpact(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.r = Path(self.t.name)
        (self.r / "v2/tracking").mkdir(parents=True)
        (self.r / "v2/planning").mkdir(parents=True)
        (self.r / ts.BASELINE).write_text(json.dumps(BASE))
        (self.r / "v2/tracking/sources.json").write_text(json.dumps(SRC))
        self.reg = ts.skeleton(BASE, SRC)
        self.reg["repos"]["CORE"] = {"review": "REVIEWED", "shared_paths": ["Makefile"]}
        self.reg["tasks"]["A-1"].update(review="REVIEWED", paths=["src/a/"])
        self.reg["tasks"]["A-2"].update(review="REVIEWED", paths=["src/b/"])
        self.write_reg()
        self.orig = cs.gh_json

    def tearDown(self):
        cs.gh_json = self.orig
        self.t.cleanup()

    def write_reg(self):
        (self.r / ts.REGISTRY).write_text(json.dumps(self.reg))

    def manifest(self, files, **kw):
        cs.gh_json = fake(files, **kw)
        self.assertEqual(rs.main(["--root", str(self.r), "--now", "2026-11-28T01:00:00Z"]), 0)
        return json.loads((self.r / "sources/MANIFEST.json").read_text())["sources"]["CORE"]

    def test_task_scope_gap_marks_one_task_affected(self):
        m = self.manifest(["status/status.json", "src/a/x.c"])
        self.assertEqual(m["gap_kind"], "OTHER_FILES")
        i = m["impact"]
        self.assertEqual((i["basis"], i["summary"]), ("task_scopes", {"CURRENT": 1, "AFFECTED": 1, "UNKNOWN": 0}))
        self.assertEqual(list(i["affected"]), ["A-1"])
        self.assertEqual(i["affected"]["A-1"]["classes"], ["TASK_SCOPE"])
        self.assertNotIn("_all_files", m)
        self.assertNotIn("_truncated", m)

    def test_status_only_gap_leaves_everything_current(self):
        i = self.manifest(["status/status.json"])["impact"]
        self.assertEqual(i["summary"], {"CURRENT": 2, "AFFECTED": 0, "UNKNOWN": 0})
        self.assertEqual(i["affected"], {})

    def test_shared_change_affects_all(self):
        self.assertEqual(self.manifest(["Makefile"])["impact"]["summary"]["AFFECTED"], 2)

    def test_registry_baseline_mismatch_is_unavailable_not_a_crash(self):
        self.reg["baseline_version"] = 4
        self.write_reg()
        i = self.manifest(["src/a/x.c"])["impact"]
        self.assertEqual(i["basis"], "UNAVAILABLE")
        self.assertIn("baseline", i["reason"])

    def test_missing_registry_is_unavailable(self):
        (self.r / ts.REGISTRY).unlink()
        self.assertEqual(self.manifest(["src/a/x.c"])["impact"]["basis"], "UNAVAILABLE")

    def test_manifest_is_idempotent(self):
        self.manifest(["src/a/x.c"])
        cs.gh_json = fake(["src/a/x.c"])
        self.assertEqual(rs.main(["--root", str(self.r), "--now", "2026-11-28T01:00:00Z", "--fail-if-unchanged"]), 3)


if __name__ == "__main__":
    unittest.main()
