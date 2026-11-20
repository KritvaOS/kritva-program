# KOS-MOTION-006 Proposal: Motion Contract Clarification and Conformance Alignment

| Property | Value |
|---|---|
| Document ID | KOS-PLAN-MOTION-006-001 |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | PROPOSED on 2026-11-17, awaiting the owner's decisions below. Nothing here is approved, baselined or credited |
| Owner | Dinesh (program owner) |
| Reviewer / Approver | Dinesh |
| Version | 0.1 |
| Last Updated | 2026-11-17 |
| Authority | REFERENCE: it governs no baseline, weight, approval or gate. A decision record will state any approval |
| Review | Interim D-047 role, not independent. The plan was cross-checked in an external audit round with ChatGPT; that is a second opinion, not an independent safety review |
| Related Tasks / Milestones | KOS-MOTION-001 to 005 (all accepted; KOS-MOTION-004 credited in D-136), V2-M2-MOTION-004 (closed, D-137) |
| Related Documents | [KOS_MOTION_004_PROPOSAL.md](KOS_MOTION_004_PROPOSAL.md), kritva-motion `contract/MOTION_CONTRACT.md` sections 3, 7, 8, 9, 11, 13, 15 and 17, `tasks/KOS-MOTION-004/REVIEW.md`, `tests/manifest/conformance_manifest.json` |

## Purpose

Propose KOS-MOTION-006 as the next Motion task: a contract-and-conformance task that closes the open findings and interpretation points the review of KOS-MOTION-004 left behind. It makes the contract text implementable without guessing (retention, fault handling, backend capability declaration, termination detail), adds the conformance IDs and tests that follow from those clarifications, and keeps the engine, the stores and the driver unchanged. Where a clarified rule shows the runtime does not yet behave as written, the task records the mismatch and a linked follow-up; it does not fix the runtime. This plan does not edit `baseline.json`, `approvals.json` or `gate_closures.json`, and no credit follows from a proposal.

## Current state (2026-11-17)

- KOS-MOTION-001, 002, 003, 004 and 005 are accepted. KOS-MOTION-004 is credited (D-136, weight 7, baseline v15); its repo milestone V2-M2-MOTION-004 is closed (D-137) and the required checks are recorded (D-138).
- The conformance manifest has 124 IDs: 119 IN_SCOPE (each with a test), 5 DEFERRED (CT-AUTH-01, 02, 03, 04, 06) and 0 OUT_OF_SCOPE. The suite holds 571 unit, 11 integration and 5 regression tests and 13 golden traces, plus fixed-seed property tests.
- The contract is `v0.1.0-draft`, untagged, and section 16 is PROVISIONAL. Review is the interim D-047 role, not independent. Gate V2-M6 is HOLD. All evidence is software evidence.
- Open items carried from the 004 review: interpretation points I-27, I-32, I-34, I-35 and I-36 to I-46, and findings Q-2, Q-9, Q-10 and C-1. Four ChatGPT audit findings were checked against the code and hold: the idempotency retention rule (Q-2) leaves out `max_deadline_ms`; engine monitoring of the joint configuration (I-36) uses the active configuration; the lifecycle property test imports the engine's own model tables (TRANSITIONS, PHASES_OF_STATE, REASON_CODES), so it is not an independent oracle; the store property test compares content using only `command_type`, `target` and `parameters`.
- The next free decision number is D-139.

## Alternatives considered

| Option | Result |
|---|---|
| A. Contract clarification and conformance alignment (this proposal) | Recommended. It is the only option that needs no new external interface and removes the ambiguity the later work builds on |
| B. CT-AUTH (authorization IDs) | Not now. It needs the Core security interface pinned first; the five IDs stay DEFERRED |
| C. Runtime process (transport, durable stores) | Not now. No registered milestone, and the contract points it relies on are the ones A clarifies |
| D. Independent hardening review | Needs an independent reviewer, which the program does not have. D-047 stays in force |
| S2 and S3 simulation | Stays with V2-M5-MOTION-001 (kritva-actuator is on HOLD) |

## What KOS-MOTION-006 would deliver

In scope, documents, schemas and tests only:

1. **Disposition and change-impact matrices (PR-01).** Every open point and finding gets one disposition (clarify the contract, record an implementation choice, defer, or accept as is), and every contract change is classified under section 1.2 compatibility rules before any text is edited. The contract version is decided from that classification; it is not fixed as `v0.2.0-draft` in advance.
2. **Configuration and idempotency (sections 3, 7, 8, 15, PR-02).** Completeness of 3.1 including `max_deadline_ms`, `max_execution_timeout_ms`, `default_priority` and the idempotency retention; retention defined as max deadline plus max execution timeout plus max termination bound (Q-2); a compatibility matrix; immutable binding of a command to its configuration; content identity (Q-9, Q-10) as RFC 8785 canonical JSON hashed with SHA-256, with known-answer vectors covering Unicode, numeric serialization, key ordering and rejected non-finite numbers.
3. **Fault, termination and recovery (sections 9, 11, 13, PR-03).** Fault-specific cause resolution (I-27); `CLEAR_FAULT` failure at application time as a terminal failure with a reason distinct from the admission code `FAULT_NOT_CLEARABLE` (I-34); feedback loss while HOLDING (I-35); and the monitoring rule for the joint configuration (I-36).
4. **Backend capability and termination (section 17, PR-04).** A versioned capability-declaration schema with an `extensions` object (C-1, I-40); a stable failure detail (I-41); target-bound and advisory termination (I-44, I-46); isolation of backend free text from contract fields (I-45). I-42 and I-43 stay implementation choices and get no conformance ID.
5. **Schemas, error codes, conformance plan, manifest and tests (PR-05).** New IDs and one dedicated test each, goldens relabelled as drift detectors with a contract-section reference for any update, independent-oracle property tests, full content-identity coverage, and acceptance criteria AC-601 to AC-610 numbered consistently with no hard-coded test counts.
6. **Verification and acceptance record (PR-06).** Full gates, review record, no tag.

Out of scope (each needs its own proposal and decision): any change to the engine, the stores or the driver; a fix for a runtime behaviour that a clarification shows to be missing (registered with a linked follow-up, probably KOS-MOTION-007); CT-AUTH-01, 02, 03, 04 and 06 (stay DEFERRED); a `v0.1.0` or later tag (section 16 is PROVISIONAL); real actuators, transport, persistent storage, hardware-in-loop and any physical or safety validation (gate V2-M6, HOLD).

Limits of the evidence: the tests show that the contract text, the schemas and the manifest agree with the existing software. They do not show independent review, real-actuator conformance, or real-time behaviour. A passing test that predates a clarification is not proof of the new behaviour; PR-01 marks each such case.

## ID-level dependency matrix (to be confirmed in PR-01 by a test against the manifest)

New IDs proposed (checked as unused in the manifest). Each is IN_SCOPE only when current runtime behaviour already meets the clarified rule and one dedicated test shows it; each that exposes an unmet behaviour is DEFERRED with the unmet behaviour recorded.

| Area | IDs | Planned handling |
|---|---|---|
| Configuration, identity, determinism | CT-CFG-09, CT-CFG-10, CT-ID-06, CT-DET-03 | IN_SCOPE where met; content-identity vectors are new tests |
| Faults, feedback, history, events | CT-FLT-24, CT-FLT-25, CT-FB-07, CT-HIS-02, CT-EV-06 | CT-FLT-24 (I-34), CT-FLT-25 (I-27) and CT-FB-07 (I-35) DEFERRED if the runtime does not yet meet them |
| Backend | CT-BE-08, CT-BE-09, CT-BE-10, CT-BE-11 | IN_SCOPE where the driver and simulator already conform |
| Authorization | CT-AUTH-01, 02, 03, 04, 06 | Stay DEFERRED until the Core security interface is pinned |

The final counts are set in PR-05. The manifest gate stays as it is, and DEFERRED IDs are never reported as passed.

## Governing rules

1. The contract and the conformance plan are the baseline. Changes follow the section 1.2 classification made in PR-01. Nothing is edited silently, and an open point is closed only by a recorded disposition.
2. Approval of PR-01 authorizes the clarification work and the contract version it names. It does not authorize any runtime change.
3. No change to `lifecycle`, stores, admission, the backend package or the driver. A mismatch found is registered, not fixed.
4. Evidence stays software evidence. No wording may imply safety validation or independent review.
5. Baseline, weight, milestone and credit change only through kritva-program decisions, never from kritva-motion.

## Delivery plan: small pull requests in kritva-motion

| PR | Deliverable | Notes |
|---|---|---|
| PR-01 | Design record: task record, disposition matrix, change-impact matrix, ID matrix with a manifest test, section 1.2 version classification, AC-601 to AC-610, TASKS row. Protected path: owner merge. Hard owner review stop | none |
| PR-02 | Sections 3, 7, 8, 15: configuration completeness, retention, compatibility, binding, content identity, known-answer vectors | CT-CFG, CT-ID, CT-DET |
| PR-03 | Sections 9, 11, 13: fault cause resolution, `CLEAR_FAULT` failure, feedback loss while HOLDING, joint-configuration monitoring | CT-FLT, CT-FB |
| PR-04 | Section 17: capability-declaration schema with `extensions`, stable failure detail, termination binding, free-text isolation | CT-BE |
| PR-05 | Schemas, error codes, conformance plan, manifest, new tests, relabelled goldens, independent-oracle property tests | CT-HIS, CT-EV |
| PR-06 | Full verification, review record and acceptance record, no tag | none |

## Top risks (PR-01 must settle them)

1. Misclassifying the version or compatibility effect of a change under section 1.2.
2. Normative wording that cannot be implemented or tested for I-27, I-34, I-35 and I-36.
3. Mistaking old passing tests for proof of new behaviour.

## Decisions for the owner

| # | Decision | Recommendation |
|---|---|---|
| 1 | Approve KOS-MOTION-006 as the next Motion task | Approve, with option A above |
| 2 | Dependency | Depends on KOS-MOTION-001 to 005 (all accepted) |
| 3 | Weight in the next baseline | 6, an initial planning estimate comparable to KOS-MOTION-005 (six PRs, documents and tests). The owner may set 5 to 8; the weight takes effect only through the owner-run freeze |
| 4 | Contract version | Decide after the PR-01 classification; do not fix `v0.2.0-draft` in advance |
| 5 | I-27, I-34, I-35, I-36 | Clarify the contract; defer the matching IDs if the runtime does not yet conform |
| 6 | I-32, I-37 to I-39, I-40, I-41, I-44, I-45, I-46 | Clarify as listed in the delivery plan |
| 7 | I-42 and I-43 | Implementation choices, no conformance ID |
| 8 | Q-2, Q-9, Q-10, C-1 | Close in this task as described above |
| 9 | CT-AUTH-01, 02, 03, 04, 06 | Stay DEFERRED |
| 10 | Review | Keep the interim D-047 role, not independent |
| 11 | Tag | None; section 16 stays PROVISIONAL |
| 12 | Milestone | A new repo milestone V2-M2-MOTION-005 rather than reopening closed ones |
| 13 | Baseline and credit | Through kritva-program only: decision record, new baseline version (v16) with the weight, then credit after acceptance |
| 14 | Start | Approve the proposal, baseline the task in v16, then approve PR-01 by merging it. Implementation starts only after both |

## Next steps after the owner's decisions

A decision record (next free number D-139) states the approval. A new baseline version adds the task with its weight and milestone; the approvals ledger, `evidence_choices` and the status sources follow the pattern used for KOS-MOTION-004. Until then kritva-motion reports the task as planning inventory with no weight and no credit.
