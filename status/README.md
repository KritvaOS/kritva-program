# status/ — CI_DEV_INFRA report (KRP-ENG-001, KRP-M0-001 to KRP-M0-004)

`status/status.json` is the facts report for the program-owned tasks KRP-ENG-001 and the four V2-M0 tasks KRP-M0-001 to KRP-M0-004 (registered in baseline v11, D-117; credited on baseline v17) (schema 2.0, workstream CI_DEV_INFRA, repo KritvaOS/kritva-program).
Update `execution`, `git_sync` and `evidence` here as the engineering contract rollout progresses, then run `python3 tools/refresh_sources.py` (or copy to `sources/CI_DEV_INFRA.json`) and `python3 tools/consolidate_status.py --sources-dir sources`.
A self-report is a fact, not acceptance: KRP-ENG-001 earns credit only with an approval PASS in `approvals.json`, execution COMPLETE, evidence on the approved commit with a passing CI run, and no open TASK_CREDIT gate (D-022, D-027).

The four KRP-M0 tasks are reported COMPLETE with CI evidence on main commit f4ec001 (status and unit-tests runs). Like every self-report, this is a fact and not acceptance: credit needs the owner's approval record.

KRP-ENG-001 is reported COMPLETE with CI evidence on main commit 0b0f180 (status run). It earns credit only with the owner's approval record.

This report was refreshed on 2026-11-28 against main fc448ec. The program does not expire a report on age (D-165): a task keeps its credit until the repository changes inside that task's scope or the repository's shared material after `source.commit` (see `v2/planning/task_scopes.json`), so refresh `source.commit` and `updated_at` when those files change. A report older than 60 days only raises a warning.
