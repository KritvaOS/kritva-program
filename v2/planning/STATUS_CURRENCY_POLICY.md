# Status currency policy (D-164)

Status: APPROVED by the owner on 2026-11-28 (D-164) and ENABLED the same day (D-165).

## Problem

A source report loses credit when its `updated_at` is more than 14 days old (D-078; `tools/consolidate_status.py`). The window expires a report even when nothing relevant changed in the repository.

## Rule (design A2)

1. Each source report records `source.commit`, the repository commit it describes.
2. Currency is decided by the commit gap between `source.commit` and the repository head (GitHub compare, as `tools/refresh_sources.py` already does for `gap_kind`).
3. Each baselined task has a scope entry in `v2/planning/task_scopes.json`: the paths that belong to the task, plus the repository's shared material (contracts, CI, build files).
4. Each changed file in the gap is classified:
   - TASK_SCOPE: inside the scope of one or more tasks; only those tasks lose credit until the report is refreshed.
   - TASK_SHARED: inside shared material; every task of that repository loses credit until refreshed.
   - REPORT_INTEGRITY: changes the status files or their tooling; the report must be refreshed or reviewed.
   - Anything that cannot be classified is UNKNOWN and fails closed (credit withheld until reviewed).
5. A gap with no file in any class (for example only docs outside every scope) leaves credit unchanged.
6. Age alone never removes credit. A report older than 60 days (`age_warning_days`, owner decision 2026-11-28) gets an advisory
   warning only.
7. The rule is selected by `currency_rule` in `v2/tracking/sources.json`: `age` (the 14-day rule, the default) or `commit-gap`.
   `commit-gap` needs `--sources-dir` and the `sources/MANIFEST.json` written by `tools/refresh_sources.py`. A source with no
   usable impact data, or a manifest entry that does not describe the committed report, earns no credit (fails closed). Impact is
   as of the manifest fetch, so a manifest fetched more than 72 hours ago raises an advisory warning to refresh.

## Migration order

1. Record the approval and this policy (this change, docs only).
2. Add `task_scopes.json` with its schema, validator and tests.
3. Review the per-repository shared-material lists with the owner.
4. Change `tools/refresh_sources.py` to emit per-task impact in MANIFEST.json.
5. Change `tools/consolidate_status.py` to compute credit from impact, behind a report-only flag.
6. Run old and new rules side by side and compare results; no credit change.
7. Owner enables the new rule; D-078's 14-day prerequisite is superseded.
8. Update the status READMEs of Mind, Motion and Program to describe the new rule.

## Enabled

Enabled on 2026-11-28 by D-165 (`currency_rule` is `commit-gap` in `v2/tracking/sources.json`). D-078's 14-day freeze prerequisite is
superseded. Reports are refreshed when a task's files change, not on a calendar.

## Progress (2026-11-28)

Steps 1 to 6 are merged: the decision (D-164), the scope registry and validator, the reviewed scopes, per-task impact in the
manifest, the report-only preview and its first side-by-side run (95.08% against 100.0%, all three differences real). Step 7 was
split: 7a added the `currency_rule` switch (#177, default `age`); after the SDK and CI_DEV_INFRA reports were refreshed (#24, #178) the
side-by-side run showed 100.0% under both rules, and 7b set `currency_rule` to `commit-gap` and recorded D-165. Step 8 (the Mind and
Motion status READMEs) remains.

## Decided

- Long-age warning threshold: 60 days (advisory only).
- Shared-material lists: reviewed with the owner at step 3 (#172, #173) and narrowed for the SDK at step 6 (#176).
