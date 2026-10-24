# Critical Path

**Owner of:** the dependency chain that controls overall schedule, schedule risks and activities that can delay downstream work.
**Status:** DRAFT — provisional; confirm once effort estimates and dependencies are baselined.

## Provisional chain

1. Repository reconciliation ([REPOSITORY_BASELINE.md](REPOSITORY_BASELINE.md))
2. Program baseline freeze (scope, boundaries, contracts, gates)
3. P0 FOUNDATION completion and exit-gate review
4. P1 STUDIO detailed planning and execution
5. Downstream phases P2 → P5 (software, simulation)
6. P6 LAB & ROBOT — **gated additionally on reopening mechanical work**

## Schedule risks on the path

| Item | Risk | Register |
|---|---|---|
| Reconciliation incomplete or inaccurate | Duplicated or missed work | RISK-001 |
| Mechanical HOLD duration | P6 cannot start | RISK-003 |
| Integration contracts unowned | Downstream rework | RISK-002 |

## Rules

- Float and durations are recorded only when evidence-backed estimates exist.
- Update whenever [DEPENDENCY_MAP.md](DEPENDENCY_MAP.md) or [ROADMAP.md](ROADMAP.md) changes.
