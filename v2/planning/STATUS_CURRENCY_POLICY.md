# Status currency policy (D-164)

Status: APPROVED by the owner on 2026-11-28 (D-164). Docs only: nothing here changes tooling, credit, baseline or weight until migration step 7.

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
6. Age alone never removes credit. A long-age warning (60 days proposed, not decided) is advisory only.

## Migration order

1. Record the approval and this policy (this change, docs only).
2. Add `task_scopes.json` with its schema, validator and tests.
3. Review the per-repository shared-material lists with the owner.
4. Change `tools/refresh_sources.py` to emit per-task impact in MANIFEST.json.
5. Change `tools/consolidate_status.py` to compute credit from impact, behind a report-only flag.
6. Run old and new rules side by side and compare results; no credit change.
7. Owner enables the new rule; D-078's 14-day prerequisite is superseded.
8. Update the status READMEs of Mind, Motion and Program to describe the new rule.

## Until step 7

The 14-day rule stays in force. Reports are refreshed before expiry: Community 2026-12-05, Core 2026-12-08, Sense and Skill 2026-12-11, SDK, Mind and Program CI 2026-12-12.

## Open items

- Long-age warning threshold (60 days proposed).
- Shared-material list for each repository (step 3).
