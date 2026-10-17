import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import readiness as R  # noqa: E402

T = ROOT / "v2/tracking"
LOAD = lambda n: json.loads((T / n).read_text(encoding="utf-8"))


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.doc = LOAD("repo_readiness.json")
        self.reg = {w["id"]: w for w in LOAD("workstreams.json")["workstreams"]}

    def errs(self, doc, hashes=None):
        return R.validate(doc, self.reg, hashes)

    def repo(self, doc, name):
        return next(r for r in doc["repos"] if r["repo"] == name)

    def check(self, r, cid):
        return next(c for c in r["checks"] if c["id"] == cid)

    def test_committed_file_is_valid_and_covers_every_repo(self):
        e, w = self.errs(self.doc)
        self.assertEqual((e, w), ([], []))
        self.assertEqual(len(self.doc["repos"]), 9)
        for r in self.doc["repos"]:
            self.assertEqual([c["id"] for c in r["checks"]], R.CHECK_IDS)
            self.assertEqual(r["recommended"]["state"], "PRIVATE")

    def test_every_registered_repo_is_listed(self):
        listed = {r["repo"] for r in self.doc["repos"]}
        for ws in ("CORE", "COMMUNITY", "RAAS", "CI_DEV_INFRA", "ACT_INT", "ACT_EMB", "ACT_S", "ACT_M", "ACT_L"):
            self.assertIn(self.reg[ws]["repo"], listed)

    def test_no_repo_is_ready_without_owner_signoff(self):
        doc = copy.deepcopy(self.doc)
        for r in doc["repos"]:
            self.check(r, "owner_signoff")["status"] = "DECISION"
            state, blocking = R.readiness(r)
            self.assertEqual(state, "NOT_READY")
            self.assertIn("owner_signoff", blocking)

    def test_readiness_is_derived_not_asserted(self):
        doc = copy.deepcopy(self.doc)
        r = self.repo(doc, "KritvaOS/kritva-core")
        for c in r["checks"]:
            c["status"] = "PASS"
            c["evidence"] = "x"
        self.assertEqual(R.readiness(r), ("READY", []))
        self.check(r, "history_secret_scan")["status"] = "FAIL"
        self.assertEqual(R.readiness(r), ("NOT_READY", ["history_secret_scan"]))

    def test_attested_and_na_do_not_block_but_open_decision_and_fail_do(self):
        r = copy.deepcopy(self.repo(self.doc, "KritvaOS/kritva-core"))
        for c in r["checks"]:
            c["status"] = "NA"
        for st, blocks in (("ATTESTED", False), ("NA", False), ("OPEN", True), ("DECISION", True), ("FAIL", True)):
            self.check(r, "license")["status"] = st
            self.assertEqual(R.readiness(r)[0] == "NOT_READY", blocks, st)

    def test_pass_without_evidence_is_rejected(self):
        doc = copy.deepcopy(self.doc)
        c = self.check(self.repo(doc, "KritvaOS/kritva-core"), "license")
        c.pop("evidence")
        self.assertTrue(any("PASS needs evidence" in p for p in self.errs(doc)[0]))

    def test_signoff_without_evidence_is_rejected(self):
        doc = copy.deepcopy(self.doc)
        c = self.check(self.repo(doc, "KritvaOS/kritva-core"), "owner_signoff")
        c["status"] = "PASS"
        c.pop("evidence", None)
        self.assertTrue(any("owner_signoff" in p for p in self.errs(doc)[0]))

    def test_structure_errors(self):
        for mutate, text in (
            (lambda d: d["repos"][0]["checks"].pop(), "missing check"),
            (lambda d: d["repos"][0]["checks"].append(copy.deepcopy(d["repos"][0]["checks"][0])), "duplicate check"),
            (lambda d: d["repos"][0]["checks"][0].update(id="made_up"), "unknown check"),
            (lambda d: d["repos"][0]["checks"][0].update(status="GREEN"), "status must be one of"),
            (lambda d: d["repos"][0]["checks"][0].update(detail=""), "detail is required"),
            (lambda d: d["repos"][0].update(checked_head="abc"), "40-hex"),
            (lambda d: d["repos"][0]["recommended"].update(state="MAYBE"), "recommended needs"),
            (lambda d: d["repos"][0]["visibility_now"].update(state="OPEN"), "visibility_now needs"),
            (lambda d: d["repos"][0].update(workstream_ids=["NOPE"]), "not in workstreams.json"),
            (lambda d: d["repos"].append(copy.deepcopy(d["repos"][0])), "duplicate repo"),
            (lambda d: d["repos"][0].update(repo="somewhere/else"), "repo name"),
        ):
            doc = copy.deepcopy(self.doc)
            mutate(doc)
            self.assertTrue(any(text in p for p in self.errs(doc)[0]), text)

    def test_workstream_must_belong_to_the_repo(self):
        doc = copy.deepcopy(self.doc)
        self.repo(doc, "KritvaOS/kritva-core")["workstream_ids"] = ["COMMUNITY"]
        self.assertTrue(any("belongs to" in p for p in self.errs(doc)[0]))

    def test_changed_source_copy_is_a_warning_not_an_error(self):
        sha = self.repo(self.doc, "KritvaOS/kritva-core")["program_copy"]["sha256"]
        self.assertEqual(self.errs(self.doc, {"CORE": sha}), ([], []))
        e, w = self.errs(self.doc, {"CORE": "0" * 64})
        self.assertEqual(e, [])
        self.assertTrue(any("changed since the readiness check" in x for x in w))

    def test_program_copy_hashes_match_the_committed_sources(self):
        import hashlib
        for r in self.doc["repos"]:
            pc = r.get("program_copy")
            if pc:
                got = hashlib.sha256((ROOT / "sources" / f"{pc['workstream_id']}.json").read_bytes()).hexdigest()
                self.assertEqual(got, pc["sha256"], r["repo"])

    def test_readiness_never_affects_progress(self):
        import consolidate_status as cs  # noqa: F401
        c = LOAD("consolidated_status.json")
        self.assertEqual(c["progress"]["accepted_progress_pct"], 46.15)
        self.assertIn("readiness", c)
        self.assertNotIn("readiness_doc", c)

    def test_render_lists_every_repo_with_checklist_marks(self):
        doc = copy.deepcopy(self.doc)
        self.check(self.repo(doc, "KritvaOS/kritva-core"), "owner_signoff")["status"] = "DECISION"
        text = "\n".join(R.render_lines(doc))
        for r in self.doc["repos"]:
            self.assertIn(f"### {r['repo']}", text)
        self.assertIn("- [x] **PASS** history_secret_scan", text)
        self.assertIn("- [ ] **DECISION** owner_signoff", text)


if __name__ == "__main__":
    unittest.main()
