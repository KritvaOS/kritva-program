# status/ — CI_DEV_INFRA report (KRP-ENG-001, KRP-M0-001 to KRP-M0-004)

`status/status.json` is the facts report for the program-owned tasks KRP-ENG-001 and the four V2-M0 tasks KRP-M0-001 to KRP-M0-004 (baseline v11, D-117) (schema 2.0, workstream CI_DEV_INFRA, repo KritvaOS/kritva-program).
Update `execution`, `git_sync` and `evidence` here as the engineering contract rollout progresses, then run `python3 tools/refresh_sources.py` (or copy to `sources/CI_DEV_INFRA.json`) and `python3 tools/consolidate_status.py --sources-dir sources`.
A self-report is a fact, not acceptance: KRP-ENG-001 earns credit only with an approval PASS in `approvals.json`, execution COMPLETE, evidence on the approved commit with a passing CI run, and no open TASK_CREDIT gate (D-022, D-027).

The four KRP-M0 tasks are reported COMPLETE with CI evidence on main commit f4ec001 (status and unit-tests runs). Like every self-report, this is a fact and not acceptance: credit needs the owner's approval record.
