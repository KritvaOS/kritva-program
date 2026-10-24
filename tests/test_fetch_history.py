"""Tests for pinned fetch (fake `gh`) and append-only history of tools/consolidate_status.py."""
import base64
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import GOOD, SHA, fresh_ts, make_root, run, write_sources  # noqa: E402

TIP = "c" * 40  # fake resolved main commit

FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
m = json.load(open(os.environ["GH_FAKE"]))
path = sys.argv[2]
if path in m:
    print(json.dumps(m[path])); sys.exit(0)
sys.stderr.write("404 " + path); sys.exit(1)
"""


def write_core(r):
    d = json.loads((r / "examples/sources/CORE.example.json").read_text())
    d["updated_at"] = fresh_ts()
    (r / "sources/CORE.json").write_text(json.dumps(d))


def report(r, ws):
    f = {"COMMUNITY": "COMMUNITY.example.json", "CORE": "CORE.example.json"}[ws]
    d = json.loads((r / "examples/sources" / f).read_text())
    d["updated_at"] = fresh_ts()
    return d


def fetch_env(r, mapping, bindir):
    (bindir / "gh").write_text(FAKE_GH)
    (bindir / "gh").chmod((bindir / "gh").stat().st_mode | stat.S_IEXEC)
    (bindir / "map.json").write_text(json.dumps(mapping))
    return {**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}", "GH_FAKE": str(bindir / "map.json")}


def api(repo, ref, sha_doc):
    return {f"repos/{repo}/contents/status/status.json?ref={TIP}":
            {"content": base64.b64encode(json.dumps(sha_doc).encode()).decode()}}


class Fetch(unittest.TestCase):
    def mapping(self, r, **over):
        m = {"repos/KritvaOS/kritva-core/commits/main": {"sha": TIP},
             "repos/KritvaOS/kritvaos-community/commits/main": {"sha": TIP}}
        for repo, ws in (("KritvaOS/kritva-core", "CORE"), ("KritvaOS/kritvaos-community", "COMMUNITY")):
            m.update({f"repos/{repo}/contents/status/status.json?ref={TIP}":
                      {"content": base64.b64encode(json.dumps(report(r, ws)).encode()).decode()},
                      f"repos/{repo}/compare/{SHA}...{TIP}": {"status": "ahead"}})
        m.update(over)
        return m

    def go(self, over=None, drop=()):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as b:
            r = make_root(d)
            m = self.mapping(r)
            for k in drop:
                m.pop(k)
            m.update(over or {})
            env = fetch_env(r, m, Path(b))
            p = subprocess.run([sys.executable, str(r / "tools/consolidate_status.py"), "--root", str(r), "--fetch",
                                "--strict"], capture_output=True, text=True, env=env)
            c = json.loads((r / "v2/tracking/consolidated_status.json").read_text())
            return p, {w["id"]: w["source_state"] for w in c["workstreams"]}

    def test_pinned_fetch_ok(self):
        p, st = self.go()
        self.assertEqual((st["CORE"], st["COMMUNITY"]), ("OK", "OK"))

    def test_unresolvable_ref_fails_closed(self):
        p, st = self.go(drop=["repos/KritvaOS/kritva-core/commits/main"])
        self.assertEqual(st["CORE"], "UNVERIFIED")
        self.assertEqual(p.returncode, 3)

    def test_wrong_repo_identity_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            bad = report(r, "CORE")
            bad["repo"] = "SomeoneElse/other"
            key = f"repos/KritvaOS/kritva-core/contents/status/status.json?ref={TIP}"
            p, st = self.go({key: {"content": base64.b64encode(json.dumps(bad).encode()).decode()}})
            self.assertEqual(st["CORE"], "UNVERIFIED")
            self.assertIn("identity", p.stderr)

    def test_report_commit_not_ancestor_rejected(self):
        p, st = self.go({f"repos/KritvaOS/kritva-core/compare/{SHA}...{TIP}": {"status": "diverged"}})
        self.assertEqual(st["CORE"], "UNVERIFIED")
        self.assertIn("not an ancestor", p.stderr)


class History(unittest.TestCase):
    def setup(self, d):
        r = make_root(d)
        write_sources(r)
        write_core(r)
        return r

    def snap(self, r, *extra):
        return run(r, "--sources-dir", str(r / "sources"), "--snapshot", *extra)

    def files(self, r, sub):
        d = r / "v2/history" / sub
        return sorted(p.name for p in d.glob("*.json")) if d.exists() else []

    def test_snapshot_chain_unchanged_and_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.setup(d)
            self.assertIn("S0001 appended", self.snap(r).stderr)
            self.assertIn("unchanged", self.snap(r).stderr)
            self.assertEqual(self.files(r, "snapshots"), ["S0001.json"])
            # a real change (an approval) appends S0002, chained to S0001
            ap = {"approval_id": "A1", "task_id": "I2-001", "baseline_version": 1,
                  "source_repo": "KritvaOS/kritvaos-community", "source_commit": SHA, "review_status": "APPROVED",
                  "acceptance": "PASS", "approver": "Dinesh", "approved_at": "2026-10-11T12:00:00Z",
                  "evidence_refs": ["x"], "rationale": "r"}
            (r / "v2/tracking/approvals.json").write_text(json.dumps({"authorized_approvers": ["Dinesh"], "approvals": [ap]}))
            write_sources(r, "I2-001", GOOD)
            write_core(r)
            self.assertIn("S0002 appended", self.snap(r).stderr)
            s1 = json.loads((r / "v2/history/snapshots/S0001.json").read_text())
            s2 = json.loads((r / "v2/history/snapshots/S0002.json").read_text())
            self.assertEqual(s2["prev_hash"], s1["snapshot_hash"])
            self.assertEqual(s2["accepted"], [{"task_id": "I2-001", "weight": 4}])
            self.assertEqual(run(r, "--verify-history").returncode, 0)
            s1["progress"]["basis"] = "edited"
            (r / "v2/history/snapshots/S0001.json").write_text(json.dumps(s1))
            self.assertEqual(run(r, "--verify-history").returncode, 5)

    def test_missing_required_source_records_failure_not_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.setup(d)
            (r / "sources/CORE.json").unlink()
            self.snap(r)
            self.assertEqual(self.files(r, "snapshots"), [])
            self.assertEqual(self.files(r, "failures"), ["F0001.json"])


if __name__ == "__main__":
    unittest.main()
