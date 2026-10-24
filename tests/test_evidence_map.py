"""Test tools/build_evidence_map.py with synthetic resolver output."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A, B, E = "a" * 40, "b" * 40, "e" * 40


def run_tool(d, choices, cands, tasks):
    d = Path(d)
    (d / "c.json").write_text(json.dumps(choices))
    (d / "cand.json").write_text(json.dumps(cands))
    (d / "base.json").write_text(json.dumps({"tasks": [{"id": t, "workstream_id": "W"} for t in tasks]}))
    p = subprocess.run([sys.executable, str(ROOT / "tools/build_evidence_map.py"), "--choices", str(d / "c.json"),
                        "--candidates", f"W={d / 'cand.json'}", "--baseline", str(d / "base.json"),
                        "--out", str(d / "o.json")], capture_output=True, text=True)
    return p, json.loads((d / "o.json").read_text())


def item(full, runs=None, against=None):
    return {"full": full, "subject": "s", "ci_runs": runs, "against": against or {}}


RUN = {"workflowName": "CI", "conclusion": "success", "headSha": A, "databaseId": 7, "url": "u"}


class EvidenceMap(unittest.TestCase):
    def test_modes_and_refusals(self):
        cands = {"tasks": {
            "T1": [item(A, [RUN])],
            "T2": [item(A, [dict(RUN, conclusion="cancelled")])],
            "T3": [item(A, against={E: {"state": "DESCENDANT", "task_files_changed": ["x"], "task_files_deleted": []}})],
            "T4": [item(A, against={E: {"state": "DESCENDANT", "task_files_changed": [], "task_files_deleted": ["x"]}})],
            "T5": [item(A, against={E: {"state": "NOT_DESCENDANT"}})],
            "T6": [item(A), item(B)],
            "T7": [item(A)],
        }}
        ms = {"mode": "MILESTONE", "commit": E, "ci_run": 9, "workflow": "CI"}
        choices = {"W": {"default": ms, "tasks": {
            "T1": {"mode": "OWN", "workflow": "CI"}, "T2": {"mode": "OWN", "workflow": "CI"},
            "T6": {}, "T7": {"mode": "RERUN", "ci_run": 11, "workflow": "CI"}}}}
        with tempfile.TemporaryDirectory() as d:
            p, out = run_tool(d, choices, cands, ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"])
            self.assertEqual(p.returncode, 0, p.stderr)
            rows = {r["task_id"]: r for r in out["rows"]}
            self.assertEqual(sorted(rows), ["T1", "T3", "T7"])
            self.assertEqual(rows["T1"]["evidence"]["ci_run"], 7)
            self.assertEqual(rows["T1"]["evidence"]["commit"], A)
            self.assertIn("TASK_FILES_CHANGED_AFTER_TASK_COMMIT", rows["T3"]["review_flags"])
            self.assertEqual(rows["T3"]["evidence"]["commit"], E)
            self.assertIn("RERUN_ATTEMPT_REPORTED_BY_OWNER_NOT_CHECKED", rows["T7"]["review_flags"])
            un = {u["task_id"]: u["reason"] for u in out["unmapped"]}
            self.assertEqual(sorted(un), ["T2", "T4", "T5", "T6", "T8"])  # cancelled / deleted / not descendant / ambiguous / no candidates
            self.assertIn("task_commit", un["T6"])

    def test_milestone_needs_against_data(self):
        cands = {"tasks": {"T1": [item(A)]}}
        choices = {"W": {"default": {"mode": "MILESTONE", "commit": E, "ci_run": 9, "workflow": "CI"}}}
        with tempfile.TemporaryDirectory() as d:
            _, out = run_tool(d, choices, cands, ["T1"])
            self.assertEqual(out["rows"], [])
            self.assertIn("--against", out["unmapped"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
