# KOS-MOTION-003 Proposal: Lifecycle, Termination and Fault State Machine

| Property | Value |
|---|---|
| Document ID | KOS-PLAN-MOTION-003-001 |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | DRAFT proposal for owner review (2026-11-06). Nothing here is approved |
| Owner | Dinesh (program owner) |
| Reviewer / Approver | Dinesh |
| Version | 0.1 |
| Last Updated | 2026-11-06 |
| Authority | REFERENCE: it governs no baseline, weight, approval or gate |
| Review | Cross-checked with an external AI reviewer (ChatGPT, 2026-11-06) in two rounds: direction agreed, four adjustments applied below. Not an independent review (D-047) |
| Related Tasks / Milestones | KOS-MOTION-001, KOS-MOTION-002 (accepted, D-103), V2-M2-MOTION-001 (closed, D-105) |
| Related Documents | [KOS_MOTION_002_PROPOSAL.md](KOS_MOTION_002_PROPOSAL.md), kritva-motion `contract/MOTION_CONTRACT.md` sections 6, 7, 9, 10, 12, 13, `contract/CONFORMANCE_TEST_PLAN.md`, `tests/manifest/conformance_manifest.json` |

## Purpose

Propose KOS-MOTION-003 as the next Motion task: a pure, in-memory reference implementation of the Motion lifecycle, termination and fault semantics of the contract, driven by supplied events and an injected monotonic clock. It turns the DEFERRED conformance IDs that need this state machine into tested IDs. This plan does not edit `baseline.json`, `approvals.json` or `gate_closures.json`. Adding the task to the baseline needs a new owner-run baseline version, and no credit follows from a proposal.

## Current state (2026-11-06)

- Baseline v9: 43 tasks, total weight 163. Accepted progress 155/163 (D-103).
- kritva-motion: KOS-MOTION-001 and 002 are accepted. The reference validator checks configuration, the eleven-step admission order, effective limits, joint-state preconditions and queries on supplied data. The conformance manifest has 124 IDs: 39 IN_SCOPE (each with one test), 80 DEFERRED, 5 OUT_OF_SCOPE. `make test-unit` runs the gate. Required checks: secret-scan, commit-message-check, pr-acceptance-gate, unit-tests, readme-check.
- V2-M2-MOTION-001 is closed with a narrowed outcome (D-105). The runtime state machine and the integration and regression gates are recorded there as deferred work with no registered task. `make test-integration` and `make test-regression` still exit 3.
- Contract section 16 is PROVISIONAL, the contract is a draft, there is no v0.1.0 tag. Review is the interim D-047 role and is not independent. Gate V2-M6 is HOLD.
- The next free decision number is D-107.

## ID-level dependency matrix (from the manifest, to be confirmed in PR-01)

The 80 DEFERRED IDs split as follows. The numbers come from the manifest `reason` field as of main, not from estimates.

| Class | IDs | Decision |
|---|---|---|
| Lifecycle-only: the manifest reason is "needs the runtime lifecycle, termination and fault state machine" | 52: LC 8 (01..08), ARB 10 (02, 03, 04, 07, 09, 10, 11, 13, 15, 16), TMO 11 (01..11), FB 3 (02, 04, 05), CMP 3 (01..03), FLT 17 (01, 02, 03, 05, 07, 08, 09, 10, 11, 14, 15, 16, 17, 19, 20, 21, 22) | Target of KOS-MOTION-003 |
| Lifecycle plus a runtime part, to classify in PR-01 | 4: CT-FLT-18 (completion evidence for `SET_VELOCITY`), CT-FB-06 (`is_current` computed at runtime), CT-VAL-11 (execution semantics: absolute position, signed velocity), CT-DET-01 (determinism of lifecycle, timeout and event order with a simulated clock) | Decide per ID in PR-01: in scope when the lifecycle engine alone can show it, otherwise stay DEFERRED with a reason |
| Needs a store, publisher or activation runtime | 21: CFG 5, ID 5, EV 5, HIS 1, FB-03, DET-02, AUTH-06 (needs idempotency and history, not authorization) | Stay DEFERRED (candidate KOS-MOTION-005) |
| Needs the Core security interface (not pinned) | 5: AUTH-01..04, AUTH-06 (AUTH-06 also needs the idempotency store; classify once) | Stay DEFERRED until the interface is pinned |
| Backend interface or simulator | CT-BE-02 DEFERRED, CT-BE-01, 03, 04, 06, 07 OUT_OF_SCOPE | Candidate KOS-MOTION-004 |

PR-01 replaces this table with the confirmed, ID-level one (a table that sums to 80 DEFERRED plus 5 OUT_OF_SCOPE and is checked by a test). Where the table above and the manifest disagree, the manifest wins and the difference is recorded in the task record.

## What KOS-MOTION-003 would deliver

A software-only lifecycle engine in the Python standard library, in memory and deterministic. No store, no publisher, no backend, no simulator, no hardware.

In scope:

1. The public lifecycle of contract 7.5 (`ACCEPTED`, `RUNNING`, `COMPLETED`, `CANCELLED`, `FAILED`), the transition table, and rejection of every transition not in it. A terminal state never changes. Each transition is recorded once with a timestamp and a `reason_code`.
2. The execution phases of contract 7.6 (`NONE`, `DISPATCH_PENDING`, `TERMINATING`) as phases, not states. A late start confirmation never revives a command that is `TERMINATING` or terminal.
3. Arbitration and `STOP`, `HOLD`, `CANCEL`, `CLEAR_FAULT` as commands with their own lifecycle (contract 6, 7.8, 9), including preemption and queueing rules as the contract states them.
4. Time and termination (contract 10): deadline, execution timeout, termination attempts and unconfirmed termination, using an injected monotonic clock and never the system clock.
5. Completion (contract 12) from supplied execution evidence.
6. Faults and joint state (contract 13): detection from supplied fault reports, latching, clearing and recovery eligibility, kept separate from the termination of a single command.
7. An explicit event vocabulary, derived from the contract, for the inputs the engine receives and the actions it emits, defined against an abstract execution port (a protocol class with no implementation). No backend-specific states exist in the engine.
8. A property-style test of the lifecycle invariants over random event sequences with a fixed seed, in addition to deterministic tests mapped one to one to the conformance IDs.

Out of scope (each needs its own proposal and decision; none is registered here):

- Stores and publishers: idempotency, configuration activation, command history, events and notifications.
- The Execution Backend Interface implementation, a simulator, any hardware adapter, firmware, ROS 2, Mind or Skill integration.
- The integration and regression gates.
- The Core security interface and authorization.
- Physical or safety validation (gate V2-M6, HOLD).

Limits of the evidence: tests show that the engine follows the contract text for a supplied, ordered event stream. They do not show that a backend confirms or fails in the supplied way, that a physical actuator stops, that real time behaves as the injected clock, or that concurrent callers cannot race. Acceptance of this task is software evidence only.

## Governing rules (agreed with the external reviewer)

1. The contract and the conformance plan are the baseline. The engine reuses the contract's state, phase, reason-code and event names. It adds no state and no name. Anything the contract leaves open is recorded in the task record as an interpretation or an open contract finding, never added silently.
2. Approval of PR-01 authorizes implementation. It does not authorize any undocumented change to the Motion contract. A needed change goes through its own contract clarification.
3. The engine has no import of a simulator or hardware module and no state such as a motor or actuator state.
4. A later backend task implements the execution port without changing the lifecycle semantics. A needed semantic change requires a contract revision and a regression run.
5. DEFERRED IDs are never reported as passed. The manifest gate stays as it is.

## Delivery plan: small pull requests in kritva-motion

| PR | Deliverable | Notes |
|---|---|---|
| PR-01 | Design: `LIFECYCLE.md` (states, phases, transitions, invariants, event vocabulary, execution-port boundary), the confirmed ID dependency matrix, the TASK.md and the criteria AC-301..AC-307, TASKS.md row | `ACCEPTANCE_CRITERIA.md` is a protected path: owner merge. Hard owner review stop: no implementation PR before PR-01 is approved |
| PR-02 | Normal lifecycle: admission to `ACCEPTED`, dispatch, `RUNNING`, completion, injected clock, transition recording | Targeted IDs from LC and CMP |
| PR-03 | Cancellation, deadline, execution timeout, termination and unconfirmed termination | Targeted IDs from TMO and part of ARB |
| PR-04 | `STOP`, `HOLD`, `CANCEL` as commands, arbitration and preemption | Targeted IDs from ARB and FB |
| PR-05 | Fault detection, latching, clearing and recovery eligibility | Targeted IDs from FLT |
| PR-06 | Manifest update to IN_SCOPE for the covered IDs, generated transition matrix check, fixed-seed property test, documentation, review record | Existing 39 tests and the gate stay intact |

Each PR has its own tests, uses the commit format of the repository and ships one dedicated test per targeted ID where an ID is covered. The split into increments is a delivery order; the task is accepted as a whole.

## Draft criteria for kritva-motion (AC-301..AC-307)

To be added to kritva-motion `ACCEPTANCE_CRITERIA.md` as a new section in PR-01, leaving AC-001..AC-005 and AC-201..AC-207 untouched.

| ID | Criterion (testable) | Verified by |
|---|---|---|
| AC-301 | The engine implements the lifecycle states and the transition table of contract 7.5. Every transition in the table is reachable by a test and every transition not in the table is rejected by a test. A terminal state never changes. Each transition is recorded once with a timestamp and reason code. | unit tests; generated transition matrix compared with `LIFECYCLE.md` by a test that fails on a missing, extra or duplicated transition |
| AC-302 | The phases of contract 7.6 follow its rules: cancellation before dispatch completes without backend termination; after dispatch and before start confirmation the command moves to `TERMINATING`; a late start confirmation never revives a terminating or terminal command and is ignored and recorded. | unit tests |
| AC-303 | `STOP`, `HOLD`, `CANCEL` and `CLEAR_FAULT` follow contract 7.8 and 9: own command identity and lifecycle, outcomes derived from the referenced termination attempt, preemption and arbitration as written. Acceptance of a request is not reported as its effect. | unit tests |
| AC-304 | Deadline, execution timeout and termination follow contract 10 with an injected monotonic clock. The engine never reads the system clock. Unconfirmed termination ends in `FAILED` with the contract's reason code. | unit tests with a fake clock |
| AC-305 | Faults follow contract 13: detection from supplied reports, latching, clearing and recovery eligibility are distinct from command termination, and a completed command does not clear a fault. | unit tests |
| AC-306 | Every conformance ID classified as in scope in the confirmed matrix has exactly one dedicated test, mapped in the manifest and checked by the gate. Remaining IDs stay DEFERRED with a reason. A fixed-seed property test checks the invariants (terminal states final, exactly one terminal state per accepted command, no revival, no transition outside the table) over random event sequences, and records the seed, the iteration count and the command. Negative cases include invalid, duplicate, stale and conflicting events. Randomized tests do not replace the mapped tests. All 39 earlier IN_SCOPE tests still pass. | `make test-unit` |
| AC-307 | The engine has no I/O toward a backend or device, imports no simulator or hardware module, and contains no backend-specific state. The documentation and the acceptance record state that passing tests is software evidence only, never physical or safety validation, and that the review is not independent. | review (owner-reviewed, D-047) |

## Review plan

The review is owner-only (D-047) and is declared not independent. To compensate with evidence, not claims: the one-test-per-ID gate, the generated transition matrix compared with the document, the fixed-seed property test with its seed and iteration count in the CI evidence, negative event-sequence tests, CI evidence bound to the exact commit, and open semantic questions recorded as interpretations or contract findings. The review checklist lives in `tasks/KOS-MOTION-003/REVIEW.md`. A read-only review by a second person is welcome if one exists and is optional.

## Decisions needed from Dinesh

| # | Decision | Recommendation |
|---|---|---|
| 1 | Approve KOS-MOTION-003 with the scope above | Approve. It addresses 52 of the 80 deferred IDs with a bounded, hardware-free scope |
| 2 | Order of the next tasks | 003 lifecycle, then 004 backend interface, simulator and the integration and regression gates, then 005 stores and publishers; each registered only after its own proposal |
| 3 | Weight | Proposal: 8, an estimate of effort days drafted with an AI assistant (larger than 002 because of six pull requests and the property tests). The owner approves or changes it. A baseline v10 is needed, so total weight would become 171 and accepted progress would stay 155/171 until accepted |
| 4 | Milestone | Add a new milestone for the lifecycle task through the program process; V2-M2-MOTION-001 stays closed |
| 5 | PR-01 as the design checkpoint, with no separate design task | Accept: it adds no extra weight or approval, and implementation waits for the owner's sign-off on PR-01 |
| 6 | Governing rule: PR-01 approval does not authorize undocumented contract changes | Accept |
| 7 | Review is interim and not independent | Accept D-047 and record it |
| 8 | Open items carried, each needing its own change | Dependency hashes for `requirements-test.txt`; the three recorded contract findings (non-positive timeouts, the ID pattern trailing newline, the CT-VAL-03 plan row); `make test-integration` and `make test-regression` stay with the backend task |

## Step sequence

1. This pull request (kritva-program): this plan only. It changes no baseline, approval, gate or generated file.
2. Owner decisions above, recorded as a new decision (D-107 or later) in `v2/DECISIONS.md`.
3. Baseline v10 with the new task and milestone, through the owner-run freeze, with the re-approvals that a new baseline version needs (D-027, D-078), as for v9.
4. kritva-motion PR-01 (owner-merged because `ACCEPTANCE_CRITERIA.md` is protected), then owner sign-off, then PR-02 to PR-06.
5. Central approval and evidence record after the completion record, as for KOS-MOTION-002.

## Risks

- A state machine built before the backend interface may not match it. Mitigated by the event vocabulary, the abstract execution port and the rule that task 004 does not change the lifecycle semantics.
- Contract ambiguity in sections 7, 10 and 13 may force interpretations. They are recorded, not silently decided, and a contract clarification is a separate change.
- 52 to 56 IDs is a large task. The six-PR plan limits the review size of each step; if PR-01 shows that the scope is too large, the owner can split it before approval.
- Owner-only review is a known limitation, not independent review.
- Timing and ordering behavior is shown only against an injected clock and supplied events, not against a real runtime.

## What this plan does not authorize

Approval of KOS-MOTION-003, any weight, any baseline change, any gate closure, a required check, a contract change, implementation, hardware or safety claims, or a release tag.
