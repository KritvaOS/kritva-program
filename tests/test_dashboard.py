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
    """Executive view plus the sections moved to the detail file."""
    return "\n".join([*D.render_view_lines(c, phases, ["| m |", "|---|"]), *D.detail_extra_lines(c, phases)])


def exec_view(c, phases=PHASES):
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
        self.assertIn("reported separately", t)

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
        for h in ("## Program progress at a glance", "## Milestones", "## Repositories", "## Work by repository and milestone",
                  "## Needs owner attention", "## Notes on the total", "## Data health"):
            self.assertIn(h, self.v)
        for h in ("## What changed", "## Phase order", "## Dated milestones", "## V2 milestone plan"):
            self.assertNotIn(h, self.v)
        self.assertIn("Program completion:", self.v)
        for m in range(9):
            self.assertRegex(self.v, rf"\| M{m} \|")
        self.assertIn("HOLD", self.v)

    def test_detail_holds_the_full_tables_and_no_mermaid(self):
        for h in ("## Summary", "## Workstreams", "## Tasks", "## Gates", "## What changed", "## Owner actions and blockers", "## Data quality"):
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


class ExecutiveView(unittest.TestCase):
    def plan_doc(self):
        c = doc()
        c["by_milestone"] = {"KF-CORE-R10": {"tasks": 4, "credited": 3, "weight": 10, "accepted_weight": 9, "weighted": True},
                             "V2-M1-SENSE-001": {"tasks": 2, "credited": 1, "weight": 20, "accepted_weight": 10, "weighted": True}}
        c["milestone_alignment"] = [{"class": "PRE_V2", "workstream": "CORE", "milestone": "KF-CORE-R10", "weight": 10, "accepted_weight": 9}]
        c["plan_register"] = {"rows": 2, "point": 30, "low": 20, "high": 40, "retired_parents": 1, "v2_baseline_weight": 20, "v2_accepted_weight": 10,
                              "titles": {"M0": "FOUNDATION", "M1": "STUDIO"},
                              "by_milestone": {"M0": {"rows": 1, "point": 10, "low": 5, "high": 15, "baseline": 0, "accepted": 0},
                                               "M1": {"rows": 1, "point": 20, "low": 15, "high": 25, "baseline": 20, "accepted": 10}},
                              "by_repo": {"Core": {"rows": 1, "point": 10, "low": 5, "high": 15, "baseline": 0, "accepted": 0, "baseline_tasks": 0, "accepted_tasks": 0},
                                          "Sense": {"rows": 1, "point": 20, "low": 15, "high": 25, "baseline": 20, "accepted": 10, "baseline_tasks": 2, "accepted_tasks": 1}},
                              "matrix": {"Core": {"M0": {"rows": 1, "point": 10, "baseline": 0, "accepted": 0}},
                                         "Sense": {"M1": {"rows": 1, "point": 20, "baseline": 20, "accepted": 10}}},
                              "tasks": [{"id": "T-1", "repo": "Core", "milestone": "M0", "title": "x", "weight": 10, "status": "NOT_STARTED"}]}
        c["v2_plan"] = {"milestones": [{"id": "V2-M0", "phase": "P0 FOUNDATION", "target_date": "2026-10-30"},
                                       {"id": "V2-M1", "phase": "P1 OLD NAME", "target_date": "2026-11-30"}]}
        return c

    def test_one_total_combines_foundation_baseline_and_plan(self):
        t = D.totals(self.plan_doc())
        self.assertEqual((t["acc"], t["tot"]), (19, 60))  # 9 + 10 accepted of 10 + 20 + 30
        self.assertEqual((t["tacc"], t["ttot"]), (4, 8))  # 3 + 1 accepted of 4 + 2 + 2
        v = exec_view(self.plan_doc())
        self.assertIn("Program completion: 31.7%  (19 / 60 weight)", v)
        self.assertIn("| **Total** | **19 / 60** | **4 / 8** | **31.7%** |", v)
        self.assertNotIn("before v11", v.lower())

    def test_milestone_table_has_foundation_row_bars_and_m6_hold(self):
        t = exec_view(self.plan_doc())
        self.assertRegex(t, r"\| Foundation \(PRE_V2\) \| Completed before V2 \| done \|[^\n]*\| 9 / 10 \| 90\.0% \| 3 / 4 \|")
        self.assertRegex(t, r"\| M1 \| STUDIO \| 2026-11-30 \* \|[^\n]*\| 10 / 40 \| 25\.0% \| 1 / 3 \|")
        self.assertIn("HOLD (excluded)", t)
        self.assertIn("must be re-confirmed", t)

    def test_repo_table_includes_foundation_work(self):
        t = exec_view(self.plan_doc())
        self.assertIn("| Core | 3 / 5 | 9 / 20 |", t)
        self.assertIn("| Sense | 1 / 3 | 10 / 40 |", t)

    def test_matrix_has_foundation_column(self):
        t = exec_view(self.plan_doc())
        self.assertIn("| Repository | Foundation (PRE_V2) | M0 |", t)
        self.assertIn("| Core | 9/10 (90%) | 0/10 (0%) |", t)

    def test_attention_is_capped_at_five(self):
        c = self.plan_doc()
        c["gates"] = [{"gate_id": f"G{i}", "status": "OPEN", "title": "t", "blocking_effect": ["X"], "owner": "Dinesh"} for i in range(8)]
        t = D.attention_lines(c)
        self.assertEqual(sum(1 for l in t if re.match(r"\| \d+ \|", l)), 5)
        self.assertTrue(any("more open item" in l for l in t))

    def test_missing_register_is_not_verified(self):
        self.assertIn("NOT_VERIFIED", exec_view(doc()))

    def test_detail_lists_plan_tasks(self):
        t = "\n".join(D.plan_tasks_lines(self.plan_doc()))
        self.assertIn("| M0 | Core | T-1 | x | 10 | NOT_STARTED |", t)

    def test_rollups_reconcile_to_the_headline(self):
        c = self.plan_doc()
        t = D.totals(c)
        fnd = D._foundation_by_repo(c)
        reg = c["plan_register"]["by_repo"]
        self.assertEqual(sum(v[0] for v in fnd.values()) + sum(v["accepted"] for v in reg.values()), t["acc"])
        self.assertEqual(sum(v[1] for v in fnd.values()) + sum(v["baseline"] + v["point"] for v in reg.values()), t["tot"])
        v = exec_view(c)
        self.assertIn("Planning-only tasks are in the denominator but earn no credit", v)
        self.assertIn("V2 approved planning scope (not baselined)", v)
        self.assertIn("does not merge their baselines", v)
