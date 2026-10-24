#!/usr/bin/env python3
"""Tests for tools/dashboard.py and the STATUS_VIEW.md / STATUS_DETAIL.md split (display only)."""
import copy, json, re, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import dashboard as D  # noqa: E402
import readiness as R  # noqa: E402

PHASES = [[f"P{i}", n] for i, n in enumerate(
    ["FOUNDATION", "STUDIO", "BUILD & ARTIFACT", "CONTROL PLANE", "BOOKING & COMMERCIAL", "EXECUTION",
     "LAB & ROBOT", "LIVE & RESULTS", "PRODUCTION"])]
TRACK = ROOT / "v2" / "tracking"


def rdoc():
    chk = lambda st: [{"id": i, "status": st.get(i, "PASS"), "detail": f"d-{i}"} for i in R.CHECK_IDS]
    return {"target_date": "2026-11-15", "report_due": "2026-11-14", "checked_at": "x", "basis": "b", "repos": [
        {"repo": "o/kritva-a", "checks": chk({"branch_protection": "ATTESTED"}), "visibility_now": {"state": "PUBLIC"}, "recommended": {"state": "PRIVATE"}, "checked_head": "a" * 40},
        {"repo": "o/kritva-actuator-b", "checks": chk({"contract_pin": "OPEN", "license": "FAIL", "security_policy": "DECISION"}),
         "visibility_now": {"state": "PUBLIC"}, "recommended": {"state": "PRIVATE"}, "checked_head": "b" * 40}]}


def doc():
    rd = rdoc()
    return {"generated_at": "2026-10-17T10:00:00Z", "baseline_version": 2, "baseline_approved": True,
            "progress": {"accepted_progress_pct": 50.0, "basis": "10/20 weight (x)"},
            "by_workstream": {"A": {"accepted_weight": 10, "weight": 12, "credited": 2, "tasks": 3},
                              "B": {"accepted_weight": 0, "weight": 8, "credited": 0, "tasks": 2}},
            "effort": {"program_planning": {"completed": 70, "remaining": 175, "total": 245, "horizon_months": "10-12"}},
            "readiness_doc": rd, "readiness": R.summary(rd),
            "workstreams": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
            "tasks": [{"task_id": "T1", "credit": True, "evidence_state": "VERIFIED"},
                      {"task_id": "T2", "credit": False, "evidence_state": "REPORTED_AWAITING_APPROVAL"}],
            "gates": [{"gate_id": "G1", "status": "OPEN", "title": "t", "blocking_effect": ["RELEASE"], "owner": "Dinesh"},
                      {"gate_id": "G2", "status": "CLOSED", "title": "t", "blocking_effect": ["RELEASE"], "owner": "Dinesh"}],
            "errors": [], "warnings": ["C: no status source (UNVERIFIED)", "odd thing"]}


def view(c, phases=PHASES):
    return "\n".join(D.render_view_lines(c, phases, ["| m |", "|---|"]))


class Reconcile(unittest.TestCase):
    def test_phase_names_come_from_the_plan(self):
        self.assertEqual(D.phase_names(ROOT), PHASES)

    def test_phase_names_empty_when_missing(self):
        self.assertEqual(D.phase_names(ROOT / "nope"), [])

    def test_clean_data_reconciles(self):
        self.assertEqual(D.check(doc()), [])

    def test_workstream_mismatch_withholds_breakdown(self):
        c = doc(); c["by_workstream"]["A"]["accepted_weight"] = 9
        t = view(c)
        self.assertIn("NOT_VERIFIED", t)
        self.assertNotIn("| A |", t)

    def test_effort_mismatch_withholds_effort(self):
        c = doc(); c["effort"]["program_planning"]["total"] = 999
        t = view(c)
        self.assertIn("NOT_VERIFIED", t)
        self.assertNotIn("~70 PM done", t)

    def test_missing_inputs_are_not_verified_not_silent(self):
        c = doc(); c.pop("effort"); c.pop("readiness_doc"); c.pop("readiness"); c["by_workstream"] = {}
        self.assertGreaterEqual(view(c, []).count("NOT_VERIFIED"), 2)


class Content(unittest.TestCase):
    def test_no_mermaid_and_fences_balanced(self):
        t = view(doc())
        self.assertNotIn("mermaid", t.lower())
        self.assertEqual(t.count("```") % 2, 0)

    def test_progress_shows_numerator_and_denominator(self):
        t = view(doc())
        self.assertIn("| A | 10/12 | 83.3% | 2/3 |", t)
        self.assertIn("| B | 0/8 | 0.0% | 0/2 |", t)
        self.assertIn("10/20 weight", t)

    def test_milestones_have_only_recorded_dates(self):
        t = view(doc())
        s = t[t.index("## Dated milestones"):t.index("## Phase order")]
        self.assertEqual(sorted(set(re.findall(r"\d{4}-\d{2}-\d{2}", s))), ["2026-10-17", "2026-11-14", "2026-11-15"])

    def test_phase_order_has_no_dates_or_percent(self):
        t = view(doc())
        s = t[t.index("## Phase order"):t.index("Order only")]
        self.assertFalse(re.search(r"\d{4}-\d{2}-\d{2}|%|\bdays?\b", s))
        self.assertIn("P0 FOUNDATION > P1 STUDIO", s)
        self.assertIn("P8 PRODUCTION", s)

    def test_matrix_has_every_check_and_repo(self):
        t = view(doc())
        s = t[t.index("## Repository readiness"):t.index("## Dated milestones")]
        for cid in R.CHECK_IDS:
            self.assertIn(f"| {cid} |", s)
        self.assertIn("| Check | a | b |", s)
        self.assertIn("| contract_pin | PASS | OPEN |", s)
        self.assertIn("| license | PASS | FAIL |", s)
        self.assertIn("| security_policy | PASS | DEC |", s)
        self.assertIn("| branch_protection | ATT | PASS |", s)
        self.assertIn("**READY** | **NOT_READY**", s)
        self.assertIn("1 of 2 repositories READY", s)

    def test_owner_actions_come_from_records_and_sort_by_severity(self):
        rows = D.owner_action_rows(doc())
        items = [r[0] for r in rows]
        self.assertEqual(items[:3], ["b: license is FAIL", "b: security_policy is DECISION", "b: contract_pin is OPEN"])
        self.assertIn("G1 is OPEN", items)
        self.assertNotIn("G2 is CLOSED", " ".join(items))
        self.assertTrue(any("awaiting central approval" in i for i in items))
        self.assertEqual([r for r in rows if r[0].startswith("G1")][0][2], "Dinesh")

    def test_unrecorded_owner_is_stated_not_invented(self):
        rows = D.owner_action_rows(doc())
        self.assertTrue(all(r[2] in ("Dinesh", "not recorded", "not recorded per check") for r in rows))
        self.assertNotIn("due", " ".join(r[3] for r in rows).lower())

    def test_data_quality_categorises_warnings(self):
        t = view(doc())
        s = t[t.index("## Data quality"):]
        self.assertIn("| Warnings | 2 |", s)
        self.assertIn("| Workstreams registered / baselined | 3 / 2 |", s)
        self.assertIn("(not zero progress): C.", s)
        self.assertIn("- odd thing", s)

    def test_no_blended_health_figure(self):
        t = view(doc()).lower()
        self.assertNotIn("overall health", t)
        self.assertIn("never combined", t)

    def test_view_is_deterministic(self):
        self.assertEqual(view(doc()), view(doc()))


class Changes(unittest.TestCase):
    def test_first_snapshot_has_no_changes(self):
        c = doc(); f = D.facts(c)
        rec = D.changes_record(None, f, c["generated_at"])
        self.assertIsNone(rec["since"])
        self.assertIn("tracked from this snapshot", "\n".join(D.changes_lines({"changes": rec})))

    def test_unchanged_facts_carry_the_record_over(self):
        c = doc(); f = D.facts(c)
        prev = {"generated_at": "2026-10-16T00:00:00Z", "status_facts": f,
                "changes": {"since": "2026-10-15T00:00:00Z", "recorded_at": "2026-10-16T00:00:00Z", "items": ["x"]}}
        self.assertEqual(D.changes_record(prev, f, "2026-10-17T00:00:00Z"), prev["changes"])

    def test_changed_facts_are_listed(self):
        old = doc(); new = doc()
        new["gates"][0]["status"] = "CLOSED"
        new["credited_dummy"] = 1
        new["tasks"][1]["credit"] = True
        new["progress"] = {"accepted_progress_pct": 60.0, "basis": "12/20 weight (x)"}
        new["readiness_doc"]["repos"][1]["checks"][R.CHECK_IDS.index("contract_pin")]["status"] = "PASS"
        new["readiness"] = R.summary(new["readiness_doc"])
        prev = {"generated_at": "2026-10-16T00:00:00Z", "status_facts": D.facts(old)}
        rec = D.changes_record(prev, D.facts(new), "2026-10-17T00:00:00Z")
        self.assertEqual(rec["since"], "2026-10-16T00:00:00Z")
        text = "\n".join(rec["items"])
        self.assertIn("Accepted progress: 10/20 weight (x) -> 12/20 weight (x)", text)
        self.assertIn("added T2", text)
        self.assertIn("Gate G1: OPEN -> CLOSED", text)
        self.assertIn("Readiness b: NOT_READY -> NOT_READY", text)


class Committed(unittest.TestCase):
    def setUp(self):
        self.v = (TRACK / "STATUS_VIEW.md").read_text(encoding="utf-8")
        self.d = (TRACK / "STATUS_DETAIL.md").read_text(encoding="utf-8")

    def test_view_is_short_plain_markdown(self):
        self.assertLess(len(self.v.splitlines()), 150)
        self.assertNotIn("mermaid", self.v.lower())
        self.assertEqual(self.v.count("```") % 2, 0)
        for h in ("## Owner actions and blockers", "## What changed", "## Measures (never blended)",
                  "## Data quality"):
            self.assertIn(h, self.v)

    def test_detail_holds_the_full_tables_and_no_mermaid(self):
        for h in ("## Summary", "## Workstreams", "## Tasks", "## Gates"):
            self.assertIn(h, self.d)
        self.assertNotIn("mermaid", self.d.lower())
        self.assertIn("STATUS_VIEW.md", self.d)


    def test_check_mode_covers_both_files(self):
        with tempfile.TemporaryDirectory() as t:
            r = Path(t) / "kp"
            subprocess.run(["cp", "-r", str(ROOT), str(r)], check=True)
            cmd = [sys.executable, str(r / "tools/consolidate_status.py"), "--root", str(r), "--sources-dir", str(r / "sources"), "--check"]
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            p = r / "v2/tracking/STATUS_DETAIL.md"
            p.write_text(p.read_text(encoding="utf-8") + "\nedited by hand\n", encoding="utf-8")
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 4)
            p.unlink()
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 4)


if __name__ == "__main__":
    unittest.main()
