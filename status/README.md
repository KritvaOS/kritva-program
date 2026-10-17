# status/ — CI_DEV_INFRA report (KRP-ENG-001)

`status/status.json` is the facts report for the program-owned task KRP-ENG-001 (schema 2.0, workstream CI_DEV_INFRA, repo KritvaOS/kritva-program).
Update `execution`, `git_sync` and `evidence` here as the engineering contract rollout progresses, then run `python3 tools/refresh_sources.py` (or copy to `sources/CI_DEV_INFRA.json`) and `python3 tools/consolidate_status.py --sources-dir sources`.
A self-report is a fact, not acceptance: KRP-ENG-001 earns credit only with an approval PASS in `approvals.json`, execution COMPLETE, evidence on the approved commit with a passing CI run, and no open TASK_CREDIT gate (D-022, D-027).
