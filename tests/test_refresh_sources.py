"""Tests for tools/refresh_sources.py with a fake GitHub API (no network)."""
import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from support import ROOT, fresh_ts, make_root  # noqa: E402
import consolidate_status as cs  # noqa: E402
import refresh_sources as rs  # noqa: E402

REPORT, HEAD = "d" * 40, "e" * 40


def doc(ws, repo, commit=REPORT):
    d = json.loads((ROOT / "examples/sources" / f"{ws}.example.json").read_text())
    d["updated_at"], d["repo"], d["workstream_id"] = fresh_ts(), repo, ws
    d["source"]["commit"] = commit
    return d


def fake(files, status="ahead", core_doc=None, comm_doc=None):
    api = {
        "repos/KritvaOS/kritva-core/commits/main": {"sha": HEAD},
        "repos/KritvaOS/kritvaos-community/commits/main": {"sha": HEAD},
    }
    for repo, d in (("KritvaOS/kritva-core", core_doc), ("KritvaOS/kritvaos-community", comm_doc)):
        if d is not None:
            api[f"repos/{repo}/contents/status/status.json?ref={HEAD}"] = {"content": base64.b64encode(json.dumps(d).encode()).decode()}
        api[f"repos/{repo}/compare/{REPORT}...{HEAD}"] = {"status": status, "ahead_by": len(files), "total_commits": 1,
                                                          "commits": [{}], "files": [{"filename": f} for f in files]}
    return lambda *a: api.get(a[0])


class Refresh(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.r = make_root(self.t.name + "/kp")
        self.orig = cs.gh_json

    def tearDown(self):
        cs.gh_json = self.orig
        self.t.cleanup()

    def run_it(self, g, *extra):
        cs.gh_json = g
        return rs.main(["--root", str(self.r), "--now", "2026-10-15T00:00:00Z", *extra])

    def test_status_only_gap_and_idempotent(self):
        g = fake(["status/status.json", "status/evidence.json"],
                 core_doc=doc("CORE", "KritvaOS/kritva-core"), comm_doc=doc("COMMUNITY", "KritvaOS/kritvaos-community"))
        self.assertEqual(self.run_it(g), 0)
        m = json.loads((self.r / "sources/MANIFEST.json").read_text())["sources"]["CORE"]
        self.assertEqual((m["state"], m["relation"], m["status_only"], m["fetched_head"]), ("FETCHED", "AHEAD", True, HEAD))
        self.assertEqual(self.run_it(g, "--fail-if-unchanged"), 3)  # second run changes nothing

    def test_non_status_files_flagged(self):
        g = fake(["status/status.json", "src/main.c"],
                 core_doc=doc("CORE", "KritvaOS/kritva-core"), comm_doc=doc("COMMUNITY", "KritvaOS/kritvaos-community"))
        self.run_it(g)
        m = json.loads((self.r / "sources/MANIFEST.json").read_text())["sources"]["CORE"]
        self.assertFalse(m["status_only"])

    def test_failed_fetch_keeps_old_snapshot_and_exits_2(self):
        g = fake(["status/status.json"], core_doc=doc("CORE", "KritvaOS/kritva-core"), comm_doc=None)
        before = (self.r / "sources/COMMUNITY.json").read_text() if (self.r / "sources/COMMUNITY.json").exists() else None
        self.assertEqual(self.run_it(g), 2)
        m = json.loads((self.r / "sources/MANIFEST.json").read_text())["sources"]
        self.assertEqual(m["COMMUNITY"]["state"], "FETCH_FAILED")
        after = (self.r / "sources/COMMUNITY.json").read_text() if (self.r / "sources/COMMUNITY.json").exists() else None
        self.assertEqual(before, after)

    def test_wrong_repo_identity_rejected(self):
        g = fake(["status/status.json"], core_doc=doc("CORE", "Other/repo"), comm_doc=doc("COMMUNITY", "KritvaOS/kritvaos-community"))
        self.assertEqual(self.run_it(g), 2)

    def test_freshness_thresholds(self):
        now = cs.parse_ts("2026-10-15T00:00:00Z")
        self.assertEqual(rs.freshness("2026-10-14T12:00:00Z", now), "FRESH")
        self.assertEqual(rs.freshness("2026-10-13T12:00:00Z", now), "WARN")
        self.assertEqual(rs.freshness("2026-10-10T00:00:00Z", now), "STALE")


if __name__ == "__main__":
    unittest.main()
