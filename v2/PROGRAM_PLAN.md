# Program Plan

**Owner of:** overall program objectives, scope, operating model, phases, governance and planning rules.
**Status:** DRAFT

## 1. Objective

Deliver Kritva V2 as a coordinated program across multiple engineering repositories, using this repository as the single source of truth for planning, milestones, dependencies, workstream status, effort estimates and release gates.

## 2. Operating model

- **Umbrella repository** (this repo): planning, tracking, evidence links.
- **Engineering repositories:** authoritative for source code, tests, releases and their own milestone records. They are never duplicated here.
- **Reconcile before replanning:** verify repository state, branches, tags, tests, release records and outstanding gates before declaring work complete or planning new tasks.

## 3. Phases (frozen names — do not rename or renumber)

| Phase | Name | Intent (summary) |
|---|---|---|
| P0 | FOUNDATION | Integration ownership, contracts, development infrastructure, program baseline |
| P1 | STUDIO | Studio workstream requirements, architecture and executable tasks |
| P2 | BUILD & ARTIFACT | Build and artifact pipeline |
| P3 | CONTROL PLANE | Control plane |
| P4 | BOOKING & COMMERCIAL | Booking and commercial capabilities |
| P5 | EXECUTION | Simulated Lab Agent and robots |
| P6 | LAB & ROBOT | Physical Lab Agent and robots |
| P7 | LIVE & RESULTS | Live video, telemetry and results |
| P8 | PRODUCTION | Security, scale, operations and launch |

Phase scope beyond the names above is intentionally left to each phase's own planning; detailed plans for P2–P8 are not created until their prerequisites are satisfied.

> Note: the earlier "Kritva V2 Planning Structure" document used different P0–P8 meanings (e.g. EVT/PVT). Those are **superseded** by the names above. See [DECISIONS.md](DECISIONS.md) D-002.

## 4. Planning rules

1. Existing engineering repositories remain authoritative for implementation.
2. Keep Core R1.0 closed; do not recreate completed Core tasks.
3. Preserve completed Community work (KOS-I2/I3/I4) and their identifiers.
4. Software acceptance (simulation, mocks, versioned interfaces) is never represented as physical hardware or safety validation.
5. Mechanical work is on HOLD (see [PRODUCT_SCOPE.md](PRODUCT_SCOPE.md)).
6. Status is evidence-backed; commit counts are not effort or acceptance.
7. No empty future plans or pre-created empty folders. (D-044 adds proposed top-level milestones in `v2/planning/` only: no tasks, weights or placeholder folders.)
8. One document, one responsibility; link instead of copying.

## 5. Governance

- Every phase and milestone has entry/exit criteria in [GATE_REGISTER.md](GATE_REGISTER.md).
- Decisions are recorded in [DECISIONS.md](DECISIONS.md).
- Scope changes preserve the previous baseline so progress cannot improve by silently removing tasks.
- A milestone closes only through its `COMPLETION_RECORD.md`.

## 6. Progress and status model

Track these dimensions separately:

| Dimension | Values |
|---|---|
| Execution | NOT_STARTED, IN_PROGRESS, BLOCKED, COMPLETE |
| Review | NOT_REVIEWED, IN_REVIEW, CHANGES_REQUIRED, APPROVED |
| Acceptance | NOT_RUN, PASS, FAIL, WAIVED |
| Git sync | NOT_COMMITTED, COMMITTED, NOT_SYNCED, SYNCED |
| Readiness | PLANNABLE, IMPLEMENTABLE, HARDWARE-BLOCKED |

Progress is acceptance-based: `accepted weight / total baseline weight × 100%` at task, milestone, phase and program level. Schedule is tracked separately: baseline date, forecast date, variance, trend. Actual effort comes from evidence-backed logs only.

## 7. Recommended order of work

1. Initialise repository dashboard and status.
2. Reconcile existing repositories ([REPOSITORY_BASELINE.md](REPOSITORY_BASELINE.md), [REQUIREMENT_TRACEABILITY.md](REQUIREMENT_TRACEABILITY.md)).
3. Freeze program baseline (scope, boundaries, dependencies, critical path, risks, gates).
4. Complete non-mechanical P0 FOUNDATION with task-level acceptance and completion record.
5. Review the P0 exit gate before expanding P1 STUDIO.
