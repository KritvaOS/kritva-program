"""freeze_baseline.py: a proposal may add tasks and milestones (new_tasks, new_milestones); without them nothing changes.

The tool builds the next baseline in memory and freezes it as one new version. It never edits a frozen version.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import SHA, make_root  # noqa: E402

TRACK = "v2/tracking/"
NEW_MS = {"id": "V2-M1-TEST-001", "workstream_id": "COMMUNITY"}
NEW_TASK = {"id": "NEW-001", "workstream_id": "COMMUNITY", "milestone_id": "V2-M1-TEST-001", "title": "A new task"}


def tool(r, *args):
    return subprocess.run([sys.executable, str(r / "tools/freeze_baseline.py"), "--root", str(r), *args],
                          capture_output=True, text=True)


def load(r, name="baseline.json"):
    return json.loads((r / TRACK / name).read_text())


class FreezeNewTasks(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.r = make_root(self._d.name)
        self.base = load(self.r)
        self.weights = {t["id"]: {"weight": t["weight"], "rationale": t.get("weight_rationale") or "kept"}
                        for t in self.base["tasks"]}

    def tearDown(self):
        self._d.cleanup()

    def proposal(self, tasks=(NEW_TASK,), milestones=(NEW_MS,), weights=None):
        w = dict(self.weights)
        for t in tasks or ():
            w.setdefault(t["id"], {"weight": 3, "rationale": "planning estimate"})
        w.update(weights or {})
        p = self.r / TRACK / "p.json"
        doc = {"weights": w}
        if tasks is not None:
            doc["new_tasks"] = list(tasks)
        if milestones is not None:
            doc["new_milestones"] = list(milestones)
        p.write_text(json.dumps(doc))
        return str(p)

    def freeze(self, p, approve=True):
        args = ["--proposal", p]
        if approve:
            args += ["--approve", "--approver", "Dinesh", "--commit", SHA, "--reason", "test"]
        return tool(self.r, *args)

    def test_dry_run_reports_additions_and_writes_nothing(self):
        out = self.freeze(self.proposal(), approve=False)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("adds 1 task(s)", out.stdout)
        self.assertEqual(load(self.r), self.base)

    def test_approve_adds_task_and_milestone_in_one_new_version(self):
        out = self.freeze(self.proposal())
        self.assertEqual(out.returncode, 0, out.stderr)
        new = load(self.r)
        self.assertEqual(new["baseline_version"], self.base["baseline_version"] + 1)
        added = [t for t in new["tasks"] if t["id"] == "NEW-001"]
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]["weight"], 3)
        self.assertEqual(added[0]["weight_rationale"], "planning estimate")
        self.assertIn(NEW_MS, new["milestones"])
        self.assertEqual(len(new["tasks"]), len(self.base["tasks"]) + 1)
        self.assertEqual(load(self.r, f"baselines/baseline_v{new['baseline_version']}.json"), new)

    def test_previous_version_is_preserved_without_the_additions(self):
        before = self.base["baseline_version"]
        self.assertEqual(self.freeze(self.proposal()).returncode, 0)
        prev = load(self.r, f"baselines/baseline_v{before}.json")
        self.assertEqual(prev["tasks"], self.base["tasks"])
        self.assertNotIn("NEW-001", [t["id"] for t in prev["tasks"]])

    def test_existing_tasks_are_unchanged(self):
        self.freeze(self.proposal())
        new = {t["id"]: t for t in load(self.r)["tasks"]}
        for t in self.base["tasks"]:
            self.assertEqual(new[t["id"]]["weight"], t["weight"])
            self.assertEqual(new[t["id"]]["milestone_id"], t["milestone_id"])

    def test_without_new_keys_behaviour_is_unchanged(self):
        out = self.freeze(self.proposal(tasks=None, milestones=None))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(len(load(self.r)["tasks"]), len(self.base["tasks"]))

    def test_proposal_must_still_cover_the_new_task(self):
        p = self.proposal()
        doc = json.loads(Path(p).read_text())
        del doc["weights"]["NEW-001"]
        Path(p).write_text(json.dumps(doc))
        out = self.freeze(p)
        self.assertEqual(out.returncode, 1)
        self.assertIn("missing ['NEW-001']", out.stderr)
        self.assertEqual(load(self.r), self.base)

    def test_new_task_without_weight_entry_is_not_silently_weighted(self):
        out = self.freeze(self.proposal(weights={"NEW-001": {"weight": 0, "rationale": "x"}}))
        self.assertEqual(out.returncode, 1)
        self.assertIn("weight must be a positive integer", out.stderr)

    def test_refusals(self):
        existing = self.base["tasks"][0]["id"]
        cases = {
            "duplicate of an existing task": ([dict(NEW_TASK, id=existing)], (NEW_MS,), "id already exists"),
            "duplicate inside the proposal": ([NEW_TASK, NEW_TASK], (NEW_MS,), "id already exists"),
            "unknown workstream": ([dict(NEW_TASK, workstream_id="NOPE")], (NEW_MS,), "unknown workstream"),
            "unknown milestone": ([dict(NEW_TASK, milestone_id="NOPE")], (NEW_MS,), "unknown milestone"),
            "milestone of another workstream": ([dict(NEW_TASK, workstream_id="CORE")], (NEW_MS,), "belongs to workstream"),
            "missing title": ([{k: v for k, v in NEW_TASK.items() if k != "title"}], (NEW_MS,), "missing ['title']"),
            "duplicate milestone": ([NEW_TASK], (NEW_MS, NEW_MS), "id already exists"),
            "milestone with unknown workstream": ([NEW_TASK], (dict(NEW_MS, workstream_id="NOPE"),), "unknown workstream"),
        }
        for name, (tasks, milestones, expect) in cases.items():
            with self.subTest(name):
                out = self.freeze(self.proposal(tasks=tasks, milestones=milestones))
                self.assertEqual(out.returncode, 1, out.stdout)
                self.assertIn(expect, out.stderr)
                self.assertEqual(load(self.r), self.base)

    def test_existing_milestone_can_be_used(self):
        ms = self.base["milestones"][0]
        task = dict(NEW_TASK, workstream_id=ms["workstream_id"], milestone_id=ms["id"])
        out = self.freeze(self.proposal(tasks=[task], milestones=[]))
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_result_passes_the_consolidator_checks(self):
        self.assertEqual(self.freeze(self.proposal()).returncode, 0)
        out = subprocess.run([sys.executable, str(self.r / "tools/consolidate_status.py"), "--root", str(self.r), "--check"],
                             capture_output=True, text=True)
        self.assertNotIn("baseline hash", out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
