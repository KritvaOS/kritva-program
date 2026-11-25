# Dependency Map

**Owner of:** provider/consumer relationships, prerequisite work, interface dependencies and acceptance conditions.
**Status:** DRAFT — only dependencies stated in the planning discussion are recorded; the rest are to be derived during P0 reconciliation.

## Known dependencies

| ID | Consumer | Provider / prerequisite | Type | Condition | Status |
|---|---|---|---|---|---|
| DEP-001 | P1 STUDIO detailed planning | P0 FOUNDATION reviewed | Phase | P0 exit gate passed | Open |
| DEP-002 | P0 non-mechanical package | Repository reconciliation | Work | REPOSITORY_BASELINE complete | Open |
| DEP-003 | P6 LAB & ROBOT | Mechanical HOLD reopened (design, actuators, BOM, fabrication) | Scope | Recorded decision in DECISIONS.md | Blocked (HOLD) |
| DEP-004 | P6 LAB & ROBOT physical acceptance | P5 EXECUTION simulated results | Evidence | Simulated acceptance does **not** substitute for physical safety | Open |
| DEP-005 | All new planning | Core R1.0 / Community I2–I4 evidence | Evidence | Referenced, not recreated | Open *(unverified)* |
| DEP-006 | kritva-sdk (SDK-003, SDK-005) | kritva-sense contract 0.1.0 (`contract/SENSE_CONTRACT.md`, `contract/sense-sample.schema.json`), pin tag `v0.2.0` = 543f5743d6ffd8fa1ed1ee5fdbf8295ae6a69a77 | Interface | Approved Sense contract vendored as an immutable pinned snapshot; CI drift check | PLANNED (PLANNING_ONLY) |
| DEP-007 | kritva-sdk (SDK-004) | Approved Control Plane service API and security boundary | Interface | Control Plane API approved (D-148, provisional) | Unresolved: no approved API |
| DEP-008 | kritva-sdk (SDK-006) | Approved simulation interface (placement open, D-144) | Interface | Sim interface approved | Unresolved: no approved interface |

## To derive in P0

Cross-workstream interface dependencies (Sense ↔ Motion ↔ Skill ↔ Mind ↔ Sim ↔ SDK ↔ Studio ↔ Control Plane), each with versioned contract, provider repo, consumer repo and acceptance condition.

## Rule

This file owns relationships only. Schedule-controlling subset → [CRITICAL_PATH.md](CRITICAL_PATH.md). Status → [WORKSTREAM_STATUS.md](WORKSTREAM_STATUS.md).
