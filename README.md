# kritva-program

Private umbrella repository for **Kritva program management**: planning, milestones, dependencies, workstream status, effort accounting, risks, release gates and progress tracking.

This repository records program-level truth. It does **not** contain engineering source code. Engineering repositories (Core, Community, etc.) remain the authoritative source for their own code, tests, releases and milestone records; this repository links to their evidence.

## Layout

| Path | Purpose |
|---|---|
| [v2/README.md](v2/README.md) | V2 program dashboard (start here) |
| [v2/tracking/STATUS.md](v2/tracking/STATUS.md) | Detailed current status and next actions |
| [v2/](v2/) | Program-level planning documents (see dashboard for the index) |
| [v2/milestones/](v2/milestones/) | Per-phase milestone packages (P0 and P1 drafted; later phases created when planning begins) |

## Rules

1. Existing engineering repositories stay authoritative for implementation; reconcile against them before planning.
2. Use the frozen phase names exactly (see [v2/PROGRAM_PLAN.md](v2/PROGRAM_PLAN.md)).
3. Mechanical work is on HOLD until explicitly reopened.
4. Status is evidence-backed. A commit is not acceptance.
5. Do not create empty future plans.
