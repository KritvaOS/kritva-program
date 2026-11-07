---
document: SEVEN_REPO_PLAN_REGISTER
status: DRAFT
classification: PLANNING_ONLY
credit_eligible: false
owner: Dinesh
date: 2026-11-07
scope:
  repositories:
    - kritva-program
    - kritva-core
    - kritvaos-community
    - kritva-sense
    - kritva-mind
    - kritva-motion
    - kritva-skill
---

# Seven-repository plan register (DRAFT, planning only)

Owner instruction (Dinesh, chat, 2026-11-07): the proposed plan is treated as owner-approved (`APPROVED_PLAN`), and every planning row has a non-zero weight. Plan approval is not task acceptance: no row earns credit, no baseline version changes, and nothing here edits `baselines/`, `planning_inventory.json` or any generated status file. Credit still needs an approved baseline task, an approval PASS, task COMPLETE and CI evidence on the approved commit.

Interim review: approvals are owner-held under D-047 and are not independent. Weights are planning anchors, not effort. Ranges are point +-1 unless widened (KOS-MIND-005, KOS-MIND-007 and PROPOSED-NEW-SKILL-003 are wider).

Out of scope, aligned separately: kritva-enterprise_program, kritva-raas, all mechanical and actuator work (V2-M6 on HOLD).

Source commits when this was prepared (local main, equal to GitHub main): kritva-program 4a35519870b44e83c5cffb4e53e630f11434ec51; kritva-core 9fe6aa65303cae1bfe8a9d428f0dc0b32e649073; kritvaos-community a4d4fbfaaddb684bae971f2081f5ca5f678d9be5; kritva-sense ddf95185341656bea5f26b2f9196838321853852; kritva-motion cc4503f0b43a3c4e43ed69daf8b557806c28d377; kritva-mind 8cc33291919ce5599d60351d0cf181ea19cdf0ff; kritva-skill c17192001f6c672819589857e8644ad21573d8d8.

## 1. Reconciliation totals

| Subset | Rows | Point | Low | High |
|---|---:|---:|---:|---:|
| Original planning rows | 21 | 112 | 88 | 137 |
| Approved child rows | 28 | 129 | 101 | 157 |
| Counted planning register | 49 | 241 | 189 | 294 |
| Retired parents (not counted) | 14 | - | - | - |
| Moved to the baseline in v11 (D-117, not counted) | 10 | 34 | 24 | 44 |

V2 baseline (v11, once frozen) is separate: 101 V2 weight, 54 accepted, 23 task rows, because the ten M0 rows above moved from this register into the baseline (D-117). Total plan weight 101 + 241 = 342 [280-405], unchanged by the move; provisional accepted share 54/342 = 15.8% [13.3-19.3%]. These measures are never blended with the historical 155/171 (90.64%, PRE_V2 plus V2).

## 2. Roll-up by milestone (planning rows only)

| Milestone | Rows | Point | Low | High | V2 baseline | Accepted |
|---|---:|---:|---:|---:|---:|---:|
| M0 | 0 | 0 | 0 | 0 | 34 | 0 |
| M1 | 5 | 22 | 17 | 27 | 10 | 10 |
| M2 | 12 | 56 | 44 | 68 | 32 | 19 |
| M3 | 10 | 48 | 37 | 60 | 0 | 0 |
| M4 | 4 | 18 | 14 | 22 | 0 | 0 |
| M5 | 9 | 49 | 38 | 60 | 5 | 5 |
| M7 | 3 | 13 | 10 | 16 | 9 | 9 |
| M8 | 6 | 35 | 29 | 41 | 11 | 11 |
| Total | 49 | 241 | 189 | 294 | 101 | 54 |

M6 is excluded (HOLD). M4 reuses the ID as Developer Experience and Ecosystem.

Milestone titles used by this plan (status views show these titles). Booking and commercial work belongs to kritva-raas, which is outside this plan, so M4 carries the Developer Experience and Ecosystem scope here. The M4 target date is carried over from the V2-M4 record and must be re-confirmed for the new scope.

| Milestone | Plan title |
|---|---|
| M0 | FOUNDATION |
| M1 | STUDIO |
| M2 | BUILD & ARTIFACT |
| M3 | CONTROL PLANE |
| M4 | DEVELOPER EXPERIENCE & ECOSYSTEM |
| M5 | EXECUTION |
| M6 | LAB & ROBOT (HOLD, excluded) |
| M7 | LIVE & RESULTS |
| M8 | PRODUCTION |

## 3. Roll-up by repository (planning rows only)

| Repository | Rows | Point | Low | High |
|---|---:|---:|---:|---:|
| Program | 1 | 5 | 4 | 6 |
| Core | 2 | 11 | 9 | 13 |
| Community | 30 | 137 | 107 | 167 |
| Sense | 0 | 0 | 0 | 0 |
| Mind | 9 | 50 | 39 | 61 |
| Motion | 2 | 12 | 10 | 14 |
| Skill | 5 | 26 | 20 | 33 |
| Total | 49 | 241 | 189 | 294 |

## 4. Column definitions

`record_type` PLANNING_TASK or RETIRED_PARENT; `id` full stable ID; `repo`; `milestone` V2 milestone; `title`; `parent_id` for child rows; `weight_point`, `low`, `high` approved planning estimate (blank for retired parents); `plan_state` APPROVED_PLAN or DECOMPOSED_REPLACED; `execution_status` as last reported, never inferred from plan approval; `credit` always 0; `counted` true for the 49 planning rows; `dependencies`.

Titles and execution statuses are register-friendly summaries. Before relying on one that mirrors an existing repository task (KOS-MIND-001, 002, 004 to 008; KOS-SKILL-001), check that repository's own task file.

## 5. Original planning rows (21)

| record_type | id | repo | milestone | title | parent_id | weight_point | low | high | plan_state | execution_status | credit | counted | dependencies |
|---|---|---|---|---|---|---:|---:|---:|---|---|---:|---|---|
| PLANNING_TASK | PROPOSED-NEW-PROGRAM-002 | Program | M8 | Production governance and release readiness |  | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-CORE-002 | Core | M2 | Core build and artifact integration |  | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-CORE-003 | Core | M8 | Core release and security review |  | 6 | 5 | 7 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-002 | Community | M1 | Cross-capability architecture documentation |  | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-006 | Community | M3 | Control Plane service conformance |  | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-015 | Community | M7 | Live and results public documentation |  | 3 | 2 | 4 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-017 | Community | M8 | Community release and security review |  | 6 | 5 | 7 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | KOS-MIND-001 | Mind | M1 | Mind foundational contract and schema work |  | 5 | 4 | 6 | APPROVED_PLAN | IN_PROGRESS | 0 | true | not recorded in this draft |
| PLANNING_TASK | KOS-MIND-002 | Mind | M2 | Mind validation and semantics implementation |  | 5 | 4 | 6 | APPROVED_PLAN | IN_PROGRESS | 0 | true | not recorded in this draft |
| PLANNING_TASK | KOS-MIND-004 | Mind | M2 | Mind capability and contract integration |  | 6 | 5 | 7 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | KOS-MIND-005 | Mind | M5 | Mind execution and runtime integration |  | 6 | 4 | 8 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | KOS-MIND-006 | Mind | M5 | Mind execution conformance and validation |  | 6 | 5 | 7 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | KOS-MIND-007 | Mind | M5 | Joint Mind-to-Skill integration |  | 6 | 4 | 8 | APPROVED_PLAN | NOT_STARTED | 0 | true | KOS-SKILL-001 |
| PLANNING_TASK | KOS-MIND-008 | Mind | M8 | Mind production readiness and release review |  | 6 | 5 | 7 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-MOTION-002 | Motion | M5 | Motion simulated execution integration |  | 6 | 5 | 7 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-MOTION-003 | Motion | M8 | Motion production and security review |  | 6 | 5 | 7 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | KOS-SKILL-001 | Skill | M1 | Skill foundational contract and capability integration |  | 5 | 4 | 6 | APPROVED_PLAN | IN_PROGRESS | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-SKILL-002 | Skill | M2 | Skill build and package integration |  | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-SKILL-003 | Skill | M3 | Skill Control Plane registration and consumption |  | 5 | 3 | 8 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-SKILL-004 | Skill | M5 | Skill runtime execution against simulated capabilities |  | 6 | 5 | 7 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-SKILL-005 | Skill | M8 | Skill production readiness and release review |  | 6 | 5 | 7 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |

## 6. Child rows (28)

| record_type | id | repo | milestone | title | parent_id | weight_point | low | high | plan_state | execution_status | credit | counted | dependencies |
|---|---|---|---|---|---|---:|---:|---:|---|---|---:|---|---|
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-018-01 | Community | M1 | Capability contract inventory and compatibility matrix | PROPOSED-NEW-COMMUNITY-018 | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-018-02 | Community | M1 | Automated version and pin compatibility checks | PROPOSED-NEW-COMMUNITY-018 | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-003-01 | Community | M2 | Build artifact handoff specification and metadata | PROPOSED-NEW-COMMUNITY-003 | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-003-02 | Community | M2 | Reproducible integration build and artifact hash | PROPOSED-NEW-COMMUNITY-003 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-004-01 | Community | M2 | Simulator artifact interface and manifest | PROPOSED-NEW-COMMUNITY-004 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-004-02 | Community | M2 | Deterministic simulator artifact handoff tests | PROPOSED-NEW-COMMUNITY-004 | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-005-01 | Community | M2 | SDK package and build manifest | PROPOSED-NEW-COMMUNITY-005 | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-005-02 | Community | M2 | Clean-environment SDK installation and import tests | PROPOSED-NEW-COMMUNITY-005 | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-007-01 | Community | M3 | Control Plane API resource model and versioning | PROPOSED-NEW-COMMUNITY-007 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-007-02 | Community | M3 | API schema validation and compatibility fixtures | PROPOSED-NEW-COMMUNITY-007 | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-008-01 | Community | M3 | Job and run lifecycle model | PROPOSED-NEW-COMMUNITY-008 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-008-02 | Community | M3 | Deterministic lifecycle transition tests | PROPOSED-NEW-COMMUNITY-008 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-009-01 | Community | M3 | Authorization principals, permissions and resource scope | PROPOSED-NEW-COMMUNITY-009 | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-009-02 | Community | M3 | Authorization allow/deny conformance tests | PROPOSED-NEW-COMMUNITY-009 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-010-01 | Community | M3 | Control Plane service conformance harness and traceability | PROPOSED-NEW-COMMUNITY-010 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-010-02 | Community | M3 | API, lifecycle and authorization integration tests | PROPOSED-NEW-COMMUNITY-010 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-011-01 | Community | M4 | Studio workflow model | PROPOSED-NEW-COMMUNITY-011 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-011-02 | Community | M4 | Demonstrable Studio sample-project workflow | PROPOSED-NEW-COMMUNITY-011 | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-012-01 | Community | M4 | SDK developer API and CLI | PROPOSED-NEW-COMMUNITY-012 | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-012-02 | Community | M4 | SDK examples, documentation and clean-environment tests | PROPOSED-NEW-COMMUNITY-012 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-013-01 | Community | M5 | Simulator job execution orchestration | PROPOSED-NEW-COMMUNITY-013 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-013-02 | Community | M5 | Deterministic execution and result handoff | PROPOSED-NEW-COMMUNITY-013 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-014-01 | Community | M5 | SDK job submit, status and cancel integration | PROPOSED-NEW-COMMUNITY-014 | 4 | 3 | 5 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-014-02 | Community | M5 | SDK result retrieval and error handling | PROPOSED-NEW-COMMUNITY-014 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-016-01 | Community | M7 | Telemetry and results ingestion using Sense stream contract | PROPOSED-NEW-COMMUNITY-016 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-COMMUNITY-016-02 | Community | M7 | Correlation, query and export end-to-end traceability | PROPOSED-NEW-COMMUNITY-016 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | not recorded in this draft |
| PLANNING_TASK | PROPOSED-NEW-MIND-003-01 | Mind | M2 | Context lifecycle model | KOS-MIND-003 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | KOS-MIND-001 accepted |
| PLANNING_TASK | PROPOSED-NEW-MIND-003-02 | Mind | M2 | Edge and Hybrid context conformance fixtures | KOS-MIND-003 | 5 | 4 | 6 | APPROVED_PLAN | NOT_STARTED | 0 | true | KOS-MIND-001 accepted |

## 7. Retired parents (14, DECOMPOSED_REPLACED, no weight, not counted)

| record_type | id | repo | milestone | title | parent_id | weight_point | low | high | plan_state | execution_status | credit | counted | dependencies |
|---|---|---|---|---|---|---:|---:|---:|---|---|---:|---|---|
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-003 | Community | M2 | Build artifact handoff and integration |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-004 | Community | M2 | Simulator integration and artifact handoff |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-005 | Community | M2 | SDK build, package and artifact integration |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-007 | Community | M3 | Control Plane API contract and compatibility |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-008 | Community | M3 | Control Plane lifecycle and job/run state |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-009 | Community | M3 | Control Plane authorization boundary and policy |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-010 | Community | M3 | Control Plane conformance tests |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-011 | Community | M4 | Studio workflow and developer integration |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-012 | Community | M4 | SDK developer experience and examples |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-013 | Community | M5 | Simulator execution and results |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-014 | Community | M5 | SDK execution and job/run integration |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-016 | Community | M7 | Telemetry and results flow |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | PROPOSED-NEW-COMMUNITY-018 | Community | M1 | Cross-capability compatibility matrix and version pins |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false |  |
| RETIRED_PARENT | KOS-MIND-003 | Mind | M2 | Context lifecycle and Edge/Hybrid conformance |  |  |  |  | DECOMPOSED_REPLACED | NOT_COUNTED | 0 | false | KOS-MIND-001 accepted |

## 8. Baseline reference (not one of the 49 planning rows)

KOS-MOTION-003, milestone V2-M2-MOTION-002, baseline weight 8 (baseline v10, D-108). Credit 0. It is already inside the V2 baseline and must not be added to the 241 planning points. Motion's main task register has no row for it and Motion has not reported it. Execution status is pending verification of the start record on the branch `docs/start-kos-motion-003`: NOT_STARTED (or READY) if the record only prepares the work, IN_PROGRESS only after the record is merged and says the work started.

## 9. Caveats

- Community I2 to I4 software credit (21/21 tasks, 71/71 weight) is not safety clearance. KOS-I3 and KOS-I4 human safety reviews stay OPEN, KOS-CI-001 is deferred, and physical actuator deployment is blocked.
- kritva-core/planning is authoritative for Core planning.
- Per-repo status.json files lag their repositories; use task registers and the frozen baseline.
- Dependencies are recorded only where known (KOS-MIND-003 children, KOS-MIND-007). Remaining rows say so; they are to be filled when each task's criteria are made concrete.

## 9. M0 rows moved to the baseline (D-117)

The ten M0 planning rows were removed from the counted register when baseline v11 added them as baseline tasks, so no weight is counted twice. Weights and low-high ranges are unchanged (34 [24-44]). They earn no credit until completed with approval and CI evidence.

| Baseline task | Former register row | Repo | Baseline milestone | Weight | Range |
|---|---|---|---|---:|---|
| KRP-M0-001 | PROPOSED-NEW-PROGRAM-001 | Program | V2-M0-PROGRAM-001 | 5 | 4-6 |
| KRP-M0-002 | PROPOSED-NEW-PROGRAM-003 | Program | V2-M0-PROGRAM-001 | 4 | 3-5 |
| KRP-M0-003 | PROPOSED-NEW-PROGRAM-004 | Program | V2-M0-PROGRAM-001 | 3 | 2-4 |
| KRP-M0-004 | PROPOSED-NEW-PROGRAM-005 | Program | V2-M0-PROGRAM-001 | 3 | 2-4 |
| KF-CORE-M0-001 | PROPOSED-NEW-CORE-001 | Core | V2-M0-CORE-001 | 5 | 4-6 |
| KOS-COMMUNITY-M0-001 | PROPOSED-NEW-COMMUNITY-001 | Community | V2-M0-COMMUNITY-001 | 2 | 1-3 |
| KOS-SENSE-M0-001 | PROPOSED-NEW-SENSE-001 | Sense | V2-M0-SENSE-001 | 3 | 2-4 |
| KOS-MIND-M0-001 | PROPOSED-NEW-MIND-GOV-001 | Mind | V2-M0-MIND-001 | 3 | 2-4 |
| KOS-MOTION-M0-001 | PROPOSED-NEW-MOTION-001 | Motion | V2-M0-MOTION-001 | 3 | 2-4 |
| KOS-SKILL-M0-001 | PROPOSED-NEW-SKILL-GOV-001 | Skill | V2-M0-SKILL-001 | 3 | 2-4 |
