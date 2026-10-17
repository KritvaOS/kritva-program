"""Effort accounting (D-020): validated, display-only, and unable to change evidence-credited progress."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from support import ROOT, SHA, make_root, run, write_sources  # noqa: E402
import effort  # noqa: E402

REG = {"CORE", "COMMUNITY", "SENSE"}
AUTH = {"Dinesh"}


def rng(lo, b, hi, basis):
    return {"low": lo, "base": b, "high": hi, "basis": basis}


def draft(**over):
    d = {"schema_version": "1.0", "estimate_version": 1, "reporting_cutoff": "2026-10-13", "unit": "person_month",
         "approval": {"status": "DRAFT", "approver": None, "approved_at": None, "commit": None, "content_sha256": None},
         "crosswalk": [], "workstreams": []}
    d.update(over)
    return d


def ws(**over):
    w = {"workstream_id": "CORE", "completed": rng(18, 20, 24, "RECORDED_ACTUAL"), "remaining": rng(0, 1, 3, "OWNER_ESTIMATE"),
         "confidence": "H", "assumptions": [], "source_refs": [], "owner_notes": ""}
    w.update(over)
    return w


def approve(d):
    d["approval"] = {"status": "APPROVED", "approver": "Dinesh", "approved_at": "2026-10-14T00:00:00Z", "commit": SHA,
                     "content_sha256": effort.content_hash(d)}
    return d


class Validation(unittest.TestCase):
    def errs(self, d):
        return effort.validate(d, REG, AUTH)

    def test_empty_draft_and_good_estimate_are_valid(self):
        self.assertEqual(self.errs(draft()), [])
        self.assertEqual(self.errs(draft(workstreams=[ws()])), [])

    def test_bad_numbers_and_order_rejected(self):
        for bad in (rng(5, 4, 6, "RECORDED_ACTUAL"), rng(-1, 0, 1, "RECORDED_ACTUAL"), rng(1, 2, float("inf"), "RECORDED_ACTUAL"),
                    rng(1, 2, 3, "GUESS"), rng(True, 2, 3, "RECORDED_ACTUAL"), {"low": 1, "base": 2, "high": 3}):
            self.assertTrue(self.errs(draft(workstreams=[ws(completed=bad)])), bad)

    def test_remaining_cannot_claim_actuals(self):
        self.assertTrue(self.errs(draft(workstreams=[ws(remaining=rng(1, 2, 3, "RECORDED_ACTUAL"))])))

    def test_unknown_or_duplicate_workstream_and_unknown_keys(self):
        self.assertTrue(self.errs(draft(workstreams=[ws(workstream_id="NOPE")])))
        self.assertTrue(self.errs(draft(workstreams=[ws(), ws()])))
        self.assertTrue(self.errs(draft(workstreams=[ws(total=rng(1, 2, 3, "DERIVED"))])))  # total is derived, never stored
        self.assertTrue(self.errs(draft(extra=1)))

    def test_confidence_and_support_rules(self):
        self.assertTrue(self.errs(draft(workstreams=[ws(confidence="X")])))
        self.assertTrue(self.errs(draft(workstreams=[ws(confidence="L")])))  # L needs assumptions and refs
        self.assertEqual(self.errs(draft(workstreams=[ws(confidence="L", assumptions=["a"], source_refs=["r"])])), [])
        rec = ws(completed=rng(1, 2, 3, "RECONSTRUCTED_ACTUAL"))
        self.assertTrue(self.errs(draft(workstreams=[rec])))

    def test_missing_data_is_allowed_but_not_zero(self):
        d = draft(workstreams=[ws(completed=None, remaining=None, confidence=None)])
        self.assertEqual(self.errs(d), [])
        s = effort.summary(d, {w: {} for w in REG}, {})
        self.assertTrue(all(r["completed"] is None and r["total"] is None for r in s["rows"]))
        self.assertEqual(s["workstreams_fully_estimated"], 0)

    def test_total_is_derived_per_bound(self):
        s = effort.summary(draft(workstreams=[ws()]), {w: {} for w in REG}, {})
        core = next(r for r in s["rows"] if r["workstream_id"] == "CORE")
        self.assertEqual(core["total"], (18, 21, 27))

    def test_approval_rules(self):
        good = approve(draft(workstreams=[ws()]))
        self.assertEqual(self.errs(good), [])
        bad = copy.deepcopy(good)
        bad["approval"]["approver"] = "Claude"
        self.assertTrue(self.errs(bad))
        bad = copy.deepcopy(good)
        bad["approval"]["commit"] = "abc"
        self.assertTrue(self.errs(bad))
        bad = copy.deepcopy(good)
        bad["workstreams"][0]["remaining"]["base"] = 2  # edited after approval
        self.assertTrue(any("content_sha256" in e for e in self.errs(bad)))
        d = draft()
        d["approval"]["approver"] = "Dinesh"  # a DRAFT must not carry approval fields
        self.assertTrue(self.errs(d))

    def test_crosswalk_rules(self):
        ok = {"legacy_name": "Electrical/Power", "status": "MAPPED", "rationale": "r",
              "maps_to": [{"workstream_id": "CORE", "share": 0.5}, {"workstream_id": "SENSE", "share": 0.5}]}
        self.assertEqual(self.errs(draft(crosswalk=[ok])), [])
        bad = dict(ok, maps_to=[{"workstream_id": "CORE", "share": 0.5}])
        self.assertTrue(self.errs(draft(crosswalk=[bad])))
        self.assertTrue(self.errs(draft(crosswalk=[dict(ok, rationale="")])))
        self.assertTrue(self.errs(draft(crosswalk=[ok, ok])))
        self.assertEqual(self.errs(draft(crosswalk=[{"legacy_name": "X", "status": "UNDECIDED", "maps_to": [], "rationale": ""}])), [])


class Integration(unittest.TestCase):
    def snapshot(self, r):
        c = json.loads((r / "v2/tracking/consolidated_status.json").read_text())
        return {k: c[k] for k in ("progress", "tasks", "by_workstream", "by_phase", "by_milestone", "measures", "gates")}

    def test_effort_never_changes_progress_or_credit(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            write_sources(r)
            self.assertEqual(run(r, "--sources-dir", str(r / "sources")).returncode, 0)
            before = self.snapshot(r)
            e = json.loads((r / effort.FILE).read_text())
            e["workstreams"] = [ws(workstream_id="COMMUNITY", completed=rng(10, 12, 14, "RECORDED_ACTUAL"),
                                   remaining=rng(3, 4, 5, "OWNER_ESTIMATE"))]
            (r / effort.FILE).write_text(json.dumps(e))
            p = run(r, "--sources-dir", str(r / "sources"))
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(self.snapshot(r), before)
            view = (r / "v2/tracking/STATUS_VIEW.md").read_text() + (r / "v2/tracking/STATUS_DETAIL.md").read_text()
            self.assertIn("Effort and capability", view)
            self.assertIn("NOT_ESTIMATED", view)
            self.assertIn("16 (13-19)", view)
            c = json.loads((r / "v2/tracking/consolidated_status.json").read_text())
            self.assertEqual(c["effort"]["status"], "DRAFT")
            self.assertEqual(run(r, "--sources-dir", str(r / "sources"), "--check").returncode, 0)

    def test_invalid_effort_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            write_sources(r)
            e = json.loads((r / effort.FILE).read_text())
            e["workstreams"] = [ws(workstream_id="NOPE")]
            (r / effort.FILE).write_text(json.dumps(e))
            p = run(r, "--sources-dir", str(r / "sources"))
            self.assertEqual(p.returncode, 1)
            self.assertIn("effort_estimates.json", p.stderr)

    def test_compute_never_receives_effort(self):
        import inspect
        sys.path.insert(0, str(ROOT / "tools"))
        import consolidate_status as cs
        self.assertNotIn("effort", inspect.getsource(cs.compute))

    def test_approve_cli_dry_checks_and_writes(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            base = [sys.executable, str(r / "tools/effort.py"), "--root", str(r)]
            self.assertEqual(subprocess.run(base + ["--check"], capture_output=True, text=True).returncode, 0)
            bad = subprocess.run(base + ["--approve", "--approver", "Claude", "--commit", SHA], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1)
            self.assertEqual(json.loads((r / effort.FILE).read_text())["approval"]["status"], "DRAFT")
            ok = subprocess.run(base + ["--approve", "--approver", "Dinesh", "--commit", SHA], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(json.loads((r / effort.FILE).read_text())["approval"]["status"], "APPROVED")
            self.assertEqual(subprocess.run(base + ["--check"], capture_output=True, text=True).returncode, 0)
            again = subprocess.run(base + ["--approve", "--approver", "Dinesh", "--commit", SHA], capture_output=True, text=True)
            self.assertEqual(again.returncode, 1)


if __name__ == "__main__":
    unittest.main()
