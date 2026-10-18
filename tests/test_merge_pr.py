#!/usr/bin/env python3
"""Tests for scripts/pipeline/merge-pr.sh with a fake gh on PATH (nothing touches GitHub)."""
import json, os, stat, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SH = str(ROOT / "scripts/pipeline/merge-pr.sh")
FAKE = r'''#!/usr/bin/env bash
echo "$*" >> "$FAKE_LOG"
case "$1 $2" in
  "auth status") exit 0;;
  "pr view")
     if echo "$*" | grep -q "state,baseRefName"; then echo "${FAKE_PR_STATE:-OPEN main feat/x}"; exit 0; fi
     if echo "$*" | grep -q "\-q .state"; then echo MERGED; exit 0; fi
     roll=""; for w in secret-scan commit-message-check pr-acceptance-gate; do [ "$w" = "${FAKE_BAD:-none}" ] || roll="$roll{\"workflowName\":\"$w\",\"conclusion\":\"SUCCESS\",\"status\":\"COMPLETED\"},"; done
     echo '{"author":{"login":"someone"},"headRefOid":"'$(printf 'a%.0s' $(seq 40))'","baseRefName":"main","commits":[{"oid":"a","messageHeadline":"'"${FAKE_MSG:-feat(sense): x}"'","messageBody":"Task: KOS-SENSE-001"}],"reviews":[],"statusCheckRollup":['"${roll%,}"']}'; exit 0;;
  "pr checks")
     if echo "$*" | grep -q "\-\-json"; then
        [ -n "${FAKE_NO_WORKFLOW_FIELD:-}" ] && echo "$*" | grep -q "workflow" && exit 1
        echo '[{"name":"x","workflow":"","state":"SUCCESS"}]'; exit 0; fi
     echo "all good"; exit 0;;
  "api -X"|"api repos/KritvaOS/kritva-sense/pulls/7/files") ;;
esac
if [ "$1" = api ]; then
  case "$*" in
    *"/files"*) echo '[{"filename":"src/a.py","status":"added"}]';;
    *"planning/TASKS.md"*) python3 -c "import base64;print('{\"content\":\"'+base64.b64encode(b'| KOS-SENSE-001 | T | IN_PROGRESS |\n').decode()+'\"}')";;
    *) exit 1;;
  esac; exit 0
fi
if [ "$1 $2" = "pr merge" ]; then exit 0; fi
exit 0
'''


def run(*a, env=None, state=None, bad=None, msg=None):
    with tempfile.TemporaryDirectory() as t:
        gh = Path(t) / "gh"; gh.write_text(FAKE); gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        log = Path(t) / "log"; log.write_text("")
        e = dict(os.environ, PATH=f"{t}:{os.environ['PATH']}", FAKE_LOG=str(log))
        if state: e["FAKE_PR_STATE"] = state
        if bad: e["FAKE_BAD"] = bad
        if msg: e["FAKE_MSG"] = msg
        p = subprocess.run(["bash", SH, "--base", t, *a], capture_output=True, text=True, env=e, timeout=60)
        return p, log.read_text()


class Merge(unittest.TestCase):
    def test_needs_repo_and_numeric_pr(self):
        self.assertEqual(run()[0].returncode, 2)
        self.assertEqual(run("--repo", "kritva-sense", "--pr", "x")[0].returncode, 2)
        self.assertEqual(run("--repo", "nope", "--pr", "7")[0].returncode, 2)

    def test_dry_run_never_merges(self):
        p, log = run("--repo", "kritva-sense", "--pr", "7", "--dry")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertNotIn("pr merge", log)
        self.assertIn("[dry-run] gh pr merge 7 -R KritvaOS/kritva-sense --merge --delete-branch --admin", p.stdout)

    def test_merges_with_admin_and_merge_commit(self):
        p, log = run("--repo", "kritva-sense", "--pr", "7")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("pr merge 7 -R KritvaOS/kritva-sense --merge --delete-branch --admin", log)

    def test_no_admin_flag(self):
        p, log = run("--repo", "kritva-sense", "--pr", "7", "--no-admin")
        self.assertIn("pr merge 7 -R KritvaOS/kritva-sense --merge --delete-branch\n", log)

    def test_gate_reject_blocks(self):
        p, log = run("--repo", "kritva-sense", "--pr", "7", msg="update stuff")
        self.assertEqual(p.returncode, 1)
        self.assertNotIn("pr merge", log)
        self.assertIn("REJECT", p.stdout)

    def test_missing_required_check_blocks(self):
        p, log = run("--repo", "kritva-sense", "--pr", "7", bad="secret-scan")
        self.assertEqual(p.returncode, 1)
        self.assertNotIn("pr merge", log)

    def test_old_gh_without_workflow_field_still_works(self):
        os.environ["FAKE_NO_WORKFLOW_FIELD"] = "1"
        try:
            p, log = run("--repo", "kritva-sense", "--pr", "7")
        finally:
            del os.environ["FAKE_NO_WORKFLOW_FIELD"]
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("pr merge 7", log)

    def test_closed_pr_and_wrong_base_refused(self):
        self.assertEqual(run("--repo", "kritva-sense", "--pr", "7", state="MERGED main b")[0].returncode, 2)
        self.assertEqual(run("--repo", "kritva-sense", "--pr", "7", state="OPEN dev b")[0].returncode, 2)


class MakeDispatch(unittest.TestCase):
    def test_make_merge(self):
        w = subprocess.run(["make", "-n", "-s", "merge", "REPO=kritva-sense", "PR=7", "DRY=1"], cwd=ROOT, capture_output=True, text=True).stdout
        for need in ('--repo "kritva-sense"', '--pr "7"', "--dry"):
            self.assertIn(need, w)


if __name__ == "__main__":
    unittest.main()
