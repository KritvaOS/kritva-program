# Onboarding a workstream into central status (D-017)

Prove the pipeline with Community and Core first; add others one at a time. Nothing here is automatic: each
step is a reviewed commit. Do not create status sources for workstreams that have no verified task records.

## Preconditions (all must hold before a workstream gets a status source)

1. The repo exists and its owning workstream ID is in `workstreams.json` with the real `repo` name.
2. Its tasks have stable IDs recorded in the repo's own planning records (not invented here).
3. Task IDs are verified by reading those records; unverified IDs are marked UNVERIFIED, never guessed.
4. Mechanical stays on HOLD until the owner reopens it by decision (D-052 records the actuator reopening, owner confirmation pending).

## Steps

1. **Generator in the repo**: `scripts/status/gen_status.py` (or equivalent) emitting schema 2.0, reporting facts
   only; fail closed on missing, duplicate or unrecognised status; evidence = criteria references until real
   evidence exists; `git_sync` SYNCED only when git proves it. Copy Core's generator as the starting point.
2. **Tests and CI in the repo**: unit tests, `--check-facts`, schema validation against the vendored schema,
   and the recorded SHA-256 of the vendored schema (`status.schema.json.sha256`).
3. **Baseline entry (central decision)**: add the tasks (workstream, milestone, title) with null weights in
   `baseline.json`, add the milestone, add any gates, record a decision (D-0xx). Weights come later via
   `tools/freeze_baseline.py` and the owner's approval.
4. **Register the source**: add it to `sources.json` (pin `ref` to a reviewed commit for reproducible runs) and
   an example in `examples/sources/`. The consolidator rejects reports whose tasks are not in the baseline.
5. **Evidence**: run `tools/resolve_shas.py` in the repo to get full-SHA candidates, find real CI runs or
   reports for those exact commits, record them in the repo's report, then review and approve centrally.
6. **History**: after a successful reconciliation, `--snapshot` appends to `v2/history/`.

## Current roster state

| Workstream | State |
|---|---|
| CORE | Reporting (KF-CORE-R10-001..009 only; R02..R09 not tracked, D-014) |
| COMMUNITY | Reporting (I2-001..I4-008) |
| RAAS | Repo recorded; no verified task IDs; not onboarded |
| All others | Roster entries only; no repo or task records verified |
