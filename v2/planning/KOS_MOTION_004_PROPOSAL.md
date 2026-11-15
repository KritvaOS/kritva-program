# KOS-MOTION-004 Proposal: Execution Backend Interface, Simulator and Integration and Regression Gates

| Property | Value |
|---|---|
| Document ID | KOS-PLAN-MOTION-004-001 |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | PROPOSED on 2026-11-15, awaiting the owner's decisions below. Nothing here is approved, baselined or credited |
| Owner | Dinesh (program owner) |
| Reviewer / Approver | Dinesh |
| Version | 0.1 |
| Last Updated | 2026-11-15 |
| Authority | REFERENCE: it governs no baseline, weight, approval or gate. A decision record will state any approval |
| Review | Interim D-047 role, not independent. Not cross-checked by an external reviewer |
| Related Tasks / Milestones | KOS-MOTION-003 (accepted, D-121), KOS-MOTION-005 (accepted, D-132), V2-M2-MOTION-003 (closed, D-133) |
| Related Documents | [KOS_MOTION_003_PROPOSAL.md](KOS_MOTION_003_PROPOSAL.md), kritva-motion `tasks/KOS-MOTION-004/TASK.md`, `BACKEND.md` and `ID_MATRIX.md`, `contract/MOTION_CONTRACT.md` section 17, `tests/manifest/conformance_manifest.json` |

## Purpose

Propose KOS-MOTION-004 as the next Motion task: a software-only Execution Backend Interface (contract 17), a deterministic scripted simulator at level S1 behind it, a runtime driver that connects the lifecycle engine (KOS-MOTION-003) and the stores (KOS-MOTION-005) to a backend, and the first real `make test-integration` and `make test-regression` gates. It turns the six conformance IDs that need a backend into tested IDs. This plan does not edit `baseline.json`, `approvals.json` or `gate_closures.json`. Adding the task to the baseline needs a new owner-run baseline version, and no credit follows from a proposal.

## Current state (2026-11-15)

- Baseline v14 (D-130) holds KOS-MOTION-001, 002, 003, 005 and M0-001 for Motion; KOS-MOTION-003 and 005 are accepted and credited (D-121, D-132). The repo milestones V2-M2-MOTION-001, 002 and 003 are closed (D-105, D-122, D-133).
- kritva-motion: the engine is a pure state machine that returns backend requests as data and receives backend answers as method calls; `lifecycle/port.py` is an unimplemented four-method protocol. The conformance manifest has 124 IDs: 113 IN_SCOPE (each with one test), 6 DEFERRED and 5 OUT_OF_SCOPE. `make test-unit` runs the gate; `make test-integration` and `make test-regression` exit 3 (NOT_IMPLEMENTED).
- Contract section 16 is PROVISIONAL, the contract is a draft, there is no v0.1.0 tag. Review is the interim D-047 role and is not independent. Gate V2-M6 is HOLD.
- The next free decision number is D-134.

## ID-level dependency matrix (confirmed in PR-01 by a test against the manifest)

| Class | IDs | Decision |
|---|---|---|
| Backend interface, simulator, driver | 6: CT-BE-01 (declaration), CT-BE-02 (dispatch against declared capabilities), CT-BE-03 (no actuator-specific identifier), CT-BE-04 (reports drive the lifecycle), CT-BE-06 (swap invariance), CT-BE-07 (termination semantics) | Targets of KOS-MOTION-004. CT-BE-05 is already IN_SCOPE |
| Needs the Core security interface (not pinned) | 5: CT-AUTH-01, 02, 03, 04, 06 | Stay DEFERRED until the interface is pinned |

After the task the manifest would hold 119 IN_SCOPE, 5 DEFERRED and 0 OUT_OF_SCOPE IDs.

## What KOS-MOTION-004 would deliver

In scope, in the Python standard library, in memory, deterministic, on the injected clock:

1. The backend port of 17.4 (pull model) and a capability declaration with every item of 17.2, with a validator that names each missing or malformed item.
2. A runtime driver that checks every outgoing operation against the current declaration before dispatch (17.3), executes the engine's requests through the port and turns backend reports (start, rejection, termination accepted or confirmed, hold, feedback, health, faults) into engine inputs, keeping request accepted, confirmed and unconfirmed apart (17.5).
3. A scripted simulator at level S1 that declares its capabilities, models no dynamics and marks every output as simulated.
4. A second, deliberately different test-only backend, so swap invariance (CT-BE-06) is shown on two implementations.
5. `make test-integration` (scenarios over driver, stores, engine and backend, no mock of own code), `make test-regression` (committed golden traces compared byte for byte), `make test`, and CI workflows for both gates.
6. Three small engine hooks, listed in the task record and covered by the 113 earlier tests: an input for a backend that rejects a dispatch, emission of the two events finding F-8 names, and an update of the backend description.

Out of scope (each needs its own proposal and decision; none is registered here): simulation levels S2 and S3, a real actuator adapter, firmware, ROS 2 and any transport, the Core security interface and authorization, persistent storage, hardware-in-loop, and any physical or safety validation (gate V2-M6, HOLD).

Limits of the evidence: the tests show that the interface, the driver and a scripted simulator follow the contract text. They do not show that a real actuator, firmware or transport conforms, that a simulated stop is a physical stop, that real time behaves like the injected clock, or that concurrent callers cannot race. Acceptance is software evidence only.

## Governing rules

1. The contract and the conformance plan are the baseline. The task adds no state, phase, reason code, event name or contract field. Anything the contract leaves open (for example the format of the capability declaration, which 17.2 lists but does not define) is recorded as an interpretation or an open contract finding, never added silently.
2. Approval of PR-01 authorizes implementation. It does not authorize any change to the Motion contract.
3. The lifecycle and store semantics do not change beyond the listed hooks. The engine, the stores and admission never import the backend package, the simulator or the driver.
4. No network, file, database, subprocess, thread or system clock in the source.
5. DEFERRED IDs are never reported as passed. The manifest gate stays as it is.

## Delivery plan: small pull requests in kritva-motion

| PR | Deliverable | Target IDs |
|---|---|---|
| PR-01 | Design record (task record, `BACKEND.md`, ID matrix with a manifest test, criteria AC-401 to AC-407, TASKS row). Protected path: owner merge. Hard owner review stop | none |
| PR-02 | Backend package: port, capability declaration and validator, report records, import-direction test | none |
| PR-03 | Scripted S1 simulator | CT-BE-01 |
| PR-04 | Runtime driver, termination semantics, engine hooks | CT-BE-02, 04, 07 |
| PR-05 | `make test-integration`, second backend, identifier scan, CI workflow | CT-BE-03, 06 |
| PR-06 | `make test-regression`, golden traces, property test, `make test`, CI workflow, final documents | none |

## Decisions for the owner

| # | Decision | Recommendation |
|---|---|---|
| 1 | Scope | Backend interface, simulator, driver and both gates in one task (chosen in chat on 2026-11-15) |
| 2 | Simulator level | S1 only, scripted and deterministic; S2 and S3 stay unregistered (chosen in chat on 2026-11-15) |
| 3 | Milestone | A new repo milestone V2-M2-MOTION-004 for the software scope. V2-M5-MOTION-001 ("validated against a simulated actuator interface") stays open for S2 and S3 level simulation, so an S1 simulation is not presented as more than it is |
| 4 | Weight in the next baseline | 7. Comparable to KOS-MOTION-005 (weight 6, 19 IDs, six PRs) and KOS-MOTION-003 (weight 8, 55 IDs, six PRs): six target IDs but three new packages, two gates, three hooks and six PRs. The owner may set 6 to 8; the weight takes effect only through the owner-run freeze |
| 5 | Finding F-8 | Close it inside the task: the engine emits `BACKEND_HEALTH_CHANGED` and `FEEDBACK_STATUS_CHANGED`, which 14.3 lists, because the `backend` stream has no producer otherwise. If declined, the driver emits the health event and F-8 stays open |
| 6 | CI | Two new workflows, `integration-tests` and `regression-tests`; making them required checks on the `main` ruleset is a separate owner action, as D-123 was for `progress-check` |
| 7 | Contract clarification | Record that 17.2 defines no declaration format (finding C-1). A later clarification may add a schema; this task adds none |
| 8 | Start | Approve the proposal (decisions 3 to 7 with the recommendations), baseline the task in v15, then approve PR-01 by merging it. Implementation starts only after both |

## Next steps after the owner's decisions

A decision record (next free number D-134) states the approval. A new baseline version adds the task with its weight and milestone; the approvals ledger, `evidence_choices` and the status sources follow the pattern used for KOS-MOTION-005 (D-129, D-130, D-132). Until then kritva-motion reports the task as IN_PROGRESS planning inventory with no weight and no credit.
