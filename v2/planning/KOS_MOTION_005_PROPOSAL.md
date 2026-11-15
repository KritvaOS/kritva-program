# KOS-MOTION-005 Proposal: Stores, Configuration Activation and Event Publisher

| Property | Value |
|---|---|
| Document ID | KOS-PLAN-MOTION-005-001 |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | PROPOSED on 2026-11-15, approved by merge of the pull request that carries decision D-129. The approval covers decisions 1 and 3 to 9 below with the recommendations as written. Decision 2 (the weight) is left to the owner and is set in the baseline freeze; baseline membership and the milestone take effect only through that later owner-run freeze |
| Owner | Dinesh (program owner) |
| Reviewer / Approver | Dinesh |
| Version | 0.1 |
| Last Updated | 2026-11-15 |
| Authority | REFERENCE: it governs no baseline, weight, approval or gate. The decision record D-129 states the approval |
| Review | Owner-reviewed, interim role D-047, not independent. Not cross-checked with an external reviewer |
| Related Tasks / Milestones | KOS-MOTION-002 (accepted, D-103), KOS-MOTION-003 (accepted, D-121), V2-M2-MOTION-002 (closed, D-122) |
| Related Documents | [KOS_MOTION_003_PROPOSAL.md](KOS_MOTION_003_PROPOSAL.md), kritva-motion `contract/MOTION_CONTRACT.md` sections 3, 7, 11, 14, 15, `contract/CONFORMANCE_TEST_PLAN.md`, `tests/manifest/conformance_manifest.json`, `tasks/KOS-MOTION-005/` (drafted, not yet merged) |

## Purpose

Propose KOS-MOTION-005 as the next Motion task: pure, in-memory reference implementations of the contract parts that need a store, an activation step or a publisher. It turns 19 of the 25 DEFERRED conformance IDs into tested IDs. This plan does not edit `baseline.json`, `approvals.json` or `gate_closures.json`. Adding the task to the baseline needs a new owner-run baseline version, and no credit follows from a proposal.

## Current state (2026-11-15)

- kritva-motion: KOS-MOTION-001, 002 and 003 are accepted. The conformance manifest has 124 IDs: 94 IN_SCOPE (each with one dedicated test), 25 DEFERRED and 5 OUT_OF_SCOPE. `make test-unit` runs the gate (381 tests on the last run). Required checks on the `main` ruleset, read back on 2026-11-09: secret-scan, commit-message-check, readme-check, pr-acceptance-gate, unit-tests and progress-check (D-124).
- V2-M2-MOTION-001 and V2-M2-MOTION-002 are closed (D-105, D-122). The integration and regression gates still exit 3 (NOT_IMPLEMENTED) and no task is registered for the remaining deferred work.
- The current baseline version, its total weight and its accepted progress are read from `baseline.json` and the status view at the freeze and are not restated here.
- Contract section 16 is PROVISIONAL, the contract is a draft, there is no v0.1.0 tag. Review is the interim D-047 role and is not independent. Gate V2-M6 is HOLD.

## ID-level dependency matrix

The 25 DEFERRED and 5 OUT_OF_SCOPE IDs split as follows. The numbers come from the manifest and from `tasks/KOS-MOTION-003/ID_MATRIX.md`, and the confirmed ID-level table is `tasks/KOS-MOTION-005/ID_MATRIX.md` (30 rows, generated from the manifest).

| Class | IDs | Decision |
|---|---|---|
| Configuration activation | 5: CT-CFG-01, 03, 04, 05, 06 | Target of KOS-MOTION-005 |
| Idempotency store | 5: CT-ID-01 to 05 | Target of KOS-MOTION-005 |
| History and feedback status | 3: CT-HIS-01, CT-LC-05 (the rejection and history half), CT-FB-03 | Target of KOS-MOTION-005 |
| Event publisher | 5: CT-EV-01 to 05 | Target of KOS-MOTION-005 |
| Replay from history | 1: CT-DET-02 | Target, classification confirmed in PR-01 (it may return to DEFERRED, see question Q-4) |
| Needs the Core security interface (not pinned) | 5: CT-AUTH-01, 02, 03, 04, 06 | Stay DEFERRED until the interface is pinned |
| Backend interface or simulator | 1 DEFERRED (CT-BE-02) and 5 OUT_OF_SCOPE (CT-BE-01, 03, 04, 06, 07) | Candidate KOS-MOTION-004 |

Rows add up: 19 targets + 5 + 1 = 25 DEFERRED, plus 5 OUT_OF_SCOPE. The 19 targets are the ones that can honestly pass today. The five CT-AUTH IDs cannot: the validator and the stores can only evaluate supplied identity and authorization results, so a pass would not show anything about section 16.

## What KOS-MOTION-005 would deliver

Pure, in-memory, deterministic code in the Python standard library, attached to the KOS-MOTION-003 lifecycle engine through explicit ports, with no change to the lifecycle semantics. No persistence, transport, backend, simulator or hardware.

1. Configuration activation (contract 3.2 to 3.4): `CONFIG_NOT_ACTIVE` until a configuration is validated and active, binding of version and digest at admission, activation that applies only to later commands, refusal of an incompatible update while affected commands are active, explicit and traceable rollback.
2. The idempotency store (7.3, 7.4): replay of results and rejections, `REQUEST_ID_CONFLICT`, client-scoped identity, retention expiry.
3. Command history (15) and feedback status (11.2, 11.3): an append-only record per submission, accepted and rejected kept apart, no overwrite, configurable retention; `VALID`, `STALE`, `INVALID` and `MISSING` reported distinctly.
4. Event streams (14): unique event IDs, one sequence per stream increasing by one, separate command, joint and backend streams, an abstract event sink with no transport, execution that survives a missing subscriber or a failed delivery, with the status query authoritative.
5. Replay of outcomes from history and configuration (CT-DET-02) if question Q-4 allows it.
6. A fixed-seed property test of the invariants over random interleavings, in addition to deterministic tests mapped one to one to the conformance IDs.

Out of scope (each needs its own proposal and decision; none is registered here):

- The Core security interface and any authentication or authorization implementation.
- The Execution Backend Interface implementation, a simulator, any hardware adapter, firmware, ROS 2, Mind or Skill integration.
- Any transport for events, and any persistent or durable storage.
- The integration and regression gates.
- Physical or safety validation (gate V2-M6, HOLD).

Limits of the evidence: tests show that the stores, the activation step and the publisher follow the contract text for supplied, ordered inputs. They do not show durability across a restart, delivery over a transport, authentication or authorization, that a backend behaves as supplied, that real time behaves as the injected clock, or that concurrent callers cannot race. Acceptance of this task is software evidence only.

## Governing rules

1. The contract and the conformance plan are the baseline. The task adds no state, phase, reason code, event name or contract field. Anything the contract leaves open is recorded in the task record as an interpretation or an open contract finding, never added silently.
2. Approval of PR-01 authorizes implementation. It does not authorize any undocumented change to the Motion contract. A needed change goes through its own contract clarification.
3. The lifecycle semantics of KOS-MOTION-003 do not change. A needed change requires a contract revision and a regression run.
4. No backend, simulator, transport, network, file or database access, no read of the system clock, and no authentication or authorization implementation.
5. DEFERRED IDs are never reported as passed. The manifest gate stays as it is.

## Delivery plan: small pull requests in kritva-motion

| PR | Deliverable | Target IDs |
|---|---|---|
| PR-01 | Design record: `STORES.md` (ports, record shapes, invariants, questions Q-1 to Q-7 settled), the confirmed ID matrix with a test that compares it with the manifest, TASK.md, criteria AC-501..AC-507, TASKS.md row. `ACCEPTANCE_CRITERIA.md` is a protected path: owner merge. Hard owner review stop: no implementation PR before PR-01 is approved | none |
| PR-02 | Configuration activation and rollback | CT-CFG-01, 03, 04, 05, 06 |
| PR-03 | Idempotency store, replay of results and rejections | CT-ID-01 to 05 |
| PR-04 | Command history, rejection records, feedback status | CT-HIS-01, CT-LC-05, CT-FB-03 |
| PR-05 | Event streams, sequence numbers, abstract event sink | CT-EV-01 to 05 |
| PR-06 | Replay from history, fixed-seed property test, manifest update, final documents, review record | CT-DET-02 |

The order follows the dependencies: replay needs history and configuration, and history needs the idempotency and rejection records. Each PR has its own tests, uses the commit format of the repository and ships one dedicated test per targeted ID. The split into increments is a delivery order; the task is accepted as a whole.

## Draft criteria for kritva-motion (AC-501..AC-507)

The full text is drafted as section 3C of kritva-motion `ACCEPTANCE_CRITERIA.md` and is added in PR-01, leaving AC-001..AC-005, AC-201..AC-207 and AC-301..AC-307 untouched.

| ID | Subject |
|---|---|
| AC-501 | Configuration activation, version and digest binding, incompatible update refused, explicit rollback (contract 3.2 to 3.4) |
| AC-502 | Idempotency and replay of results and rejections, client scoping, retention (7.3, 7.4) |
| AC-503 | Command history per submission, accepted and rejected kept apart, no overwrite (15) |
| AC-504 | Feedback status reported distinctly, invalid never reported as valid (11.2, 11.3) |
| AC-505 | Event streams, sequence numbers, delivery failure does not stop execution, status query authoritative (14) |
| AC-506 | One dedicated test per target ID, ID matrix compared with the manifest, fixed-seed property test, all 94 earlier tests pass |
| AC-507 | No I/O toward a backend, file, database or network, no system clock, no authentication implementation, software evidence only |

## Review plan

The review is owner-only (D-047) and is declared not independent. To compensate with evidence, not claims: the one-test-per-ID gate, the test that compares the ID matrix with the manifest, negative sequences, the fixed-seed property test with its seed and iteration count in the CI evidence, CI evidence bound to the exact commit, and open semantic questions recorded as interpretations or contract findings. The review checklist lives in `tasks/KOS-MOTION-005/REVIEW.md`, written at closure. A read-only review by a second person is welcome if one exists and is optional.

## Decisions (approved by merge of the pull request that carries D-129)

| # | Decision | Recommendation |
|---|---|---|
| 1 | Approve KOS-MOTION-005 with the scope above: 19 target IDs, with CT-DET-02 confirmed in PR-01 | Approve. It addresses 19 of the 25 deferred IDs, every one that can pass without the backend or the Core security interface |
| 2 | Weight | Not proposed here: the owner sets it in the baseline freeze, and D-109 requires a non-zero value. Reference points only: KOS-MOTION-003 was baselined at 8 for 55 target IDs and six pull requests (D-108), and the Motion planning rows in the seven-repository register carry 6 with a range of 5 to 7. This task has 19 target IDs and the same six-PR plan |
| 3 | Order of the next tasks | Run 005 before 004. D-107 recorded the order 003, 004, then 005; 005 needs no backend, simulator or gate work, so it does not wait for 004. 004 stays the home of CT-BE-02, the five OUT_OF_SCOPE backend IDs and the integration and regression gates, registered only after its own proposal |
| 4 | Milestone | Add a new repo milestone V2-M2-MOTION-003 through the program process; V2-M2-MOTION-001 and V2-M2-MOTION-002 stay closed. Outcome wording: Software-only Motion configuration activation, idempotent submission, command history, feedback status and event stream semantics conform to the Motion contract v0.1.0-draft through deterministic reference tests, with no persistent storage, transport, backend or physical behaviour. The planning target is inherited from phase V2-M2 (2027-01-15) and is not a commitment (PD-011 is still open). V2-M5-MOTION-001 stays reserved for the backend interface and simulator task |
| 5 | PR-01 as the design checkpoint, with no separate design task | Accept: it adds no extra weight or approval, and implementation waits for the owner's sign-off on PR-01 |
| 6 | Governing rule: PR-01 approval does not authorize undocumented contract changes | Accept |
| 7 | Review is interim and not independent | Accept D-047 and record it |
| 8 | The five CT-AUTH IDs stay DEFERRED until the Core security interface is pinned, and authentication and authorization stay supplied inputs here | Accept. A pass would not show anything about section 16 |
| 9 | Open items carried, each needing its own change | Dependency hashes for `requirements-test.txt`; the interpretation points I-27, I-32, I-34 and I-35 left open by KOS-MOTION-003, reviewed in PR-01 for any effect here; `make test-integration` and `make test-regression` stay with the backend task |

## Questions settled in PR-01

Recorded in the task record `tasks/KOS-MOTION-005/TASK.md` section 8 with a proposed handling for each, none changing the contract: Q-1 client identity and authorization are supplied inputs; Q-2 the idempotency retention field that contract 7.4 requires but 3.1 does not list; Q-3 what counts as identical content; Q-4 whether the history of 15.1 can reproduce an outcome for CT-DET-02, which decides between 19 and 18 targets; Q-5 in-memory storage and the meaning of "never overwrites"; Q-6 the abstract event sink and where the reference consumer lives; Q-7 attaching the stores to the engine without changing it.

## Step sequence

1. This pull request (kritva-program): this plan and decision D-129. It changes no baseline, approval, gate or generated file.
2. The owner sets the weight (decision 2) and the milestone is added, as a new decision, through the owner-run freeze of a new baseline version with the re-approvals that a new baseline needs (D-027, D-078), as for v10.
3. kritva-motion PR-01 (owner-merged because `ACCEPTANCE_CRITERIA.md` is protected), then owner sign-off, then PR-02 to PR-06.
4. Central approval and evidence record after the completion record, as for KOS-MOTION-003.

## Risks

- Stores built before the backend interface may not match it. Mitigated by ports, by the rule that nothing here depends on a backend, and by the rule that 004 does not change these semantics.
- Contract gaps in sections 3, 7, 14 and 15 (the retention field, the content comparison, the replay input) may force interpretations. They are recorded, not silently decided, and a contract clarification is a separate change.
- CT-DET-02 may not be reachable from the 15.1 history. The task then ends at 18 target IDs and says so.
- Owner-only review is a known limitation, not independent review.
- The tests show ordering, expiry and delivery behavior only against an injected clock and supplied inputs, not against real storage or a real transport.

## What this plan does not authorize

D-129 approves the task, its scope, the order, the milestone name and the governing rules as the owner's decision. This plan itself does not change the baseline. It does not set a weight and it does not authorize the credit for KOS-MOTION-005 (that needs an approved baseline task, a central approval and verified evidence), any baseline change, any gate closure, a required check, a contract change, implementation, hardware or safety claims, or a release tag.
