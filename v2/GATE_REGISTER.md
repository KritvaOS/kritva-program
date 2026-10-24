# Gate Register

**Owner of:** phase and milestone entry/exit criteria, evidence, approval and open blockers.
**Status:** DRAFT — P0/P1 gates defined; later gates defined when those phases are planned.

## P0 FOUNDATION

| Gate | Criterion | Evidence | Approval | Status |
|---|---|---|---|---|
| P0-ENTRY | Repository initialised with dashboard and status | v2/README.md, tracking/STATUS.md | TBD | Pending |
| P0-EXIT-1 | Existing repos reconciled (branches, tags, tests, releases, open reviews) | REPOSITORY_BASELINE.md | TBD | Pending |
| P0-EXIT-2 | Requirement traceability baseline established | REQUIREMENT_TRACEABILITY.md | TBD | Pending |
| P0-EXIT-3 | Scope, system/platform boundaries, dependency map, critical path, risks and gates frozen | corresponding docs | TBD | Pending |
| P0-EXIT-4 | Integration ownership and contracts defined | DEPENDENCY_MAP.md, milestone package | TBD | Pending |
| P0-EXIT-5 | Software vs physical acceptance separation documented | PROGRAM_PLAN.md, PRODUCT_SCOPE.md | TBD | Pending |
| P0-EXIT-6 | P0 review complete and COMPLETION_RECORD approved | milestones/P0/.../COMPLETION_RECORD.md | TBD | Pending |

## P1 STUDIO

| Gate | Criterion | Evidence | Approval | Status |
|---|---|---|---|---|
| P1-ENTRY | P0 exit gate passed | P0 COMPLETION_RECORD | TBD | Blocked on P0 |
| P1-EXIT | Studio requirements, architecture and tasks approved; acceptance defined; review complete | milestones/P1/... | TBD | Pending |

## P2–P8

Gates are defined when each phase's planning begins. P6 LAB & ROBOT entry additionally requires an explicit decision reopening mechanical work.

## Rule

A gate passes on evidence and recorded approval, never on a commit alone.
