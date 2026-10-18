#!/usr/bin/env python3
"""Tests for scripts/pipeline/pr_check.py and the Makefile pr_check target (stubbed gh, no network)."""
import base64, copy, json, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "pipeline"))
import pr_check as C  # noqa: E402
import pr_gate as G  # noqa: E402

MANIFEST = json.loads((ROOT / "v2/planning/repo-pipeline.json").read_text(encoding="utf-8"))
SHA = "b" * 40
TASKS = "| Task | Title | Status |\n|---|---|---|\n| KOS-SENSE-001 | Contract | IN_PROGRESS |\n"
OK = [{"workflowName": w, "conclusion": "SUCCESS", "status": "COMPLETED"} for w in ("secret-scan", "commit-message-check", "pr-acceptance-gate")]


class Gh:
    """Fake gh: one open PR #7 in KritvaOS/kritva-sense."""
    def __init__(self, author="someone", me="dineshannayya", files=None, msg="feat(sense): add a\n\nTask: KOS-SENSE-001", checks=OK, draft=False):
        self.author, self.me, self.msg, self.checks, self.draft = author, me, msg, checks, draft
        self.files = files or [{"filename": "src/a.py", "status": "added"}]
        self.reviews, self.posted = [], []

    def __call__(self, *a, **k):
        j = " ".join(a)
        if a[:3] == ("gh", "api", "user"):
            if not self.me:
                raise RuntimeError("not signed in")
            return self.me + "\n"
        if a[:3] == ("gh", "pr", "list"):
            return json.dumps([{"number": 7, "isDraft": self.draft, "title": "t"}])
        if a[:3] == ("gh", "pr", "view"):
            head, _, body = self.msg.partition("\n\n")
            return json.dumps({"author": {"login": self.author}, "headRefOid": SHA, "baseRefName": "main",
                               "commits": [{"oid": SHA, "messageHeadline": head, "messageBody": body}],
                               "reviews": self.reviews, "statusCheckRollup": self.checks})
        if "-X POST" in j and "/reviews" in j:
            self.posted.append(a)
            self.reviews.append({"author": {"login": self.me}, "state": "APPROVED", "commit": {"oid": SHA}})
            return "{}"
        if a[-1].endswith("/files"):
            return json.dumps(self.files)
        if "planning/TASKS.md?ref=main" in a[-1]:
            return json.dumps({"content": base64.b64encode(TASKS.encode()).decode()})
        raise RuntimeError("not found: " + j)


def unassigned():
    m = copy.deepcopy(MANIFEST)
    m["roles"]["ARCHITECTURE_REVIEWER"]["holders"] = []
    return m


def sweep(m, gh, only_pr=None, do_approve=True, repos=("kritva-sense",)):
    out = []
    rc = C.sweep(m, list(repos), only_pr, do_approve, run=gh, out=out.append)
    return rc, "\n".join(out)


class Sweep(unittest.TestCase):
    def test_approves_clear_pr_pinned_to_head_and_never_merges(self):
        gh = Gh()
        rc, out = sweep(MANIFEST, gh)
        self.assertEqual(rc, 0)
        self.assertEqual(len(gh.posted), 1)
        self.assertIn(f"commit_id={SHA}", gh.posted[0])
        self.assertIn("event=APPROVE", gh.posted[0])
        self.assertIn("| APPROVE |", out)
        self.assertNotIn("merge", " ".join(" ".join(c) for c in gh.posted).lower().replace("merging is a separate", ""))

    def test_unassigned_role_stays_needs_human_after_my_approval(self):
        gh = Gh()
        rc, out = sweep(unassigned(), gh)
        self.assertEqual(len(gh.posted), 1)
        self.assertIn("NEEDS_HUMAN", out)
        self.assertIn("UNASSIGNED", out)

    def test_dry_run_posts_nothing(self):
        gh = Gh()
        rc, out = sweep(MANIFEST, gh, do_approve=False)
        self.assertEqual(gh.posted, [])
        self.assertIn("would approve", out)

    def test_reject_is_left_alone_and_exits_1(self):
        gh = Gh(msg="update stuff\n\nTask: KOS-SENSE-001")
        rc, out = sweep(MANIFEST, gh)
        self.assertEqual(rc, 1)
        self.assertEqual(gh.posted, [])
        self.assertIn("REJECT", out)

    def test_protected_path_needs_human_not_approved(self):
        gh = Gh(files=[{"filename": ".github/workflows/x.yml", "status": "added"}])
        rc, out = sweep(MANIFEST, gh)
        self.assertEqual(gh.posted, [])
        self.assertIn("NEEDS_HUMAN", out)

    def test_own_pr_is_not_self_approved(self):
        gh = Gh(author="dineshannayya")
        rc, out = sweep(MANIFEST, gh)
        self.assertEqual(gh.posted, [])
        self.assertIn("self-approval", out)

    def test_user_without_role_does_not_approve(self):
        gh = Gh(me="stranger")
        rc, out = sweep(MANIFEST, gh)
        self.assertEqual(gh.posted, [])
        self.assertIn("holds none of the required roles", out)

    def test_draft_is_not_approved(self):
        gh = Gh(draft=True)
        rc, out = sweep(MANIFEST, gh)
        self.assertEqual(gh.posted, [])
        self.assertIn("draft", out)

    def test_failed_required_check_is_reject(self):
        gh = Gh(checks=[{"workflowName": "secret-scan", "conclusion": "FAILURE", "status": "COMPLETED"}] + OK[1:])
        rc, out = sweep(MANIFEST, gh)
        self.assertEqual((rc, gh.posted), (1, []))

    def test_unreadable_repo_is_reported_and_exit_2(self):
        def boom(*a, **k):
            if a[:3] == ("gh", "api", "user"):
                return "dineshannayya"
            raise RuntimeError("gh: not found")
        rc, out = sweep(MANIFEST, boom)
        self.assertEqual(rc, 2)
        self.assertIn("ERROR", out)

    def test_no_open_pr(self):
        def none(*a, **k):
            return "dineshannayya" if a[:3] == ("gh", "api", "user") else "[]"
        rc, out = sweep(MANIFEST, none, repos=("kritva-sense", "kritva-mind"))
        self.assertEqual(rc, 0)
        self.assertEqual(out.count("no open PR"), 2)


class Cli(unittest.TestCase):
    def test_needs_target(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/pipeline/pr_check.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        r = subprocess.run([sys.executable, str(ROOT / "scripts/pipeline/pr_check.py"), "--pr", "3"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_makefile_dispatch(self):
        def mk(*a):
            return subprocess.run(["make", "-n", "-s", *a], cwd=ROOT, capture_output=True, text=True).stdout.split()
        self.assertEqual(mk("pr_check", "all")[:3], ["python3", "scripts/pipeline/pr_check.py", "all"])
        w = mk("pr_check", "REPO=kritva-sense", "PR=7", "DRY=1")
        self.assertEqual(w[2:], ["--repo", "kritva-sense", "--pr", "7", "--no-approve"])
        self.assertNotIn("all", w)

    def test_makefile_repo_array_matches_manifest(self):
        import re
        mk = (ROOT / "Makefile").read_text(encoding="utf-8")
        block = re.search(r"^REPOS := \\\n((?:\t[\w-]+(?: \\)?\n)+)", mk, re.M).group(1)
        listed = block.replace("\\", " ").split()
        active = [r["repo_id"] for r in MANIFEST["repositories"]]
        self.assertEqual(listed, active)

    def test_makefile_passes_the_array(self):
        out = subprocess.run(["make", "-n", "-s", "pr_check", "all"], cwd=ROOT, capture_output=True, text=True).stdout
        self.assertIn('--repos "kritva-program kritva-core', out)
        out = subprocess.run(["make", "-n", "-s", "pr_check", "all", "REPOS=kritva-sense kritva-mind"], cwd=ROOT, capture_output=True, text=True).stdout
        self.assertIn('--repos "kritva-sense kritva-mind"', out)

    def test_repos_option_is_validated(self):
        run = lambda *a: subprocess.run([sys.executable, str(ROOT / "scripts/pipeline/pr_check.py"), *a], capture_output=True, text=True)
        r = run("all", "--repos", "kritva-sense,nope")
        self.assertEqual(r.returncode, 2)
        self.assertIn("not in the manifest: nope", r.stderr)
        self.assertEqual(run("--repo", "kritva-sense", "--repos", "kritva-mind").returncode, 2)


if __name__ == "__main__":
    unittest.main()
