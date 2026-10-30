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

## Registering an empty-report source (D-077)

SENSE is registered with `tasks: []` before any task is baselined. This is an exception to precondition 2, approved
for Stage 1 only. For such a source:

1. Merge the repo's `status/status.json` (schema 2.0, `tasks: []`, full commit SHA) to its `main` first.
2. Register it in a separate reviewed change: `sources.json`, the repo name in `workstreams.json`, an example file.
3. Run `python3 tools/refresh_sources.py`; check the source reads FETCHED. A gap of STATUS_ONLY is accepted as it is. A gap of OTHER_FILES is accepted when every listed file is reviewed documentation, a planning record or the status report (the SENSE exception is D-079); otherwise a reviewer reads the change first (see the gap rule in the Stage 1 plan).
4. Run `python3 tools/consolidate_status.py --sources-dir sources` and compare the generated files before and after.
   Baseline, approvals, gates, weights and other workstreams must be unchanged.
5. A failed fetch, identity mismatch or ancestry error stays a reported failure; never record it as an empty report.

## Current roster state

| Workstream | State |
|---|---|
| CORE | Reporting (KF-CORE-R10-001..009 only; R02..R09 not tracked, D-014) |
| COMMUNITY | Reporting (I2-001..I4-008) |
| SENSE | Reporting with an empty task list (D-077, [STATUS_INGESTION_PLAN.md](../planning/STATUS_INGESTION_PLAN.md)); KOS-SENSE-001 (weight 5) and KOS-SENSE-002 (weight 4) are baselined in v3 under D-078 but have no approval, so no credit; the code and test files in the SENSE gap are an accepted exception (D-079); no credit |
| All others | Roster entries only; no repo or task records verified |
