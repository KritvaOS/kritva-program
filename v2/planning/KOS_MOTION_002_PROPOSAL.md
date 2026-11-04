# KOS-MOTION-002 Proposal and Baselining Plan

| Property | Value |
|---|---|
| Document ID | KOS-PLAN-MOTION-BASELINE-001 |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | DRAFT proposal for owner review (2026-11-04). Nothing here is approved |
| Owner | Dinesh (program owner) |
| Reviewer / Approver | Dinesh |
| Version | 0.1 |
| Last Updated | 2026-11-04 |
| Authority | REFERENCE: it governs no baseline, weight, approval or gate |
| Related Tasks / Milestones | KOS-MOTION-001, KOS-MOTION-002, V2-M1-MOTION-001, V2-M2-MOTION-001 |
| Related Documents | [baseline_v9_proposal.json](../tracking/baseline_v9_proposal.json), [KOS_SENSE_001_BASELINING_PLAN.md](KOS_SENSE_001_BASELINING_PLAN.md), [STATUS_INGESTION_PLAN.md](STATUS_INGESTION_PLAN.md), [ACCEPTANCE_STANDARD.md](ACCEPTANCE_STANDARD.md), [ONBOARDING.md](../tracking/ONBOARDING.md) |

## Purpose

Propose KOS-MOTION-002 (Command validation, limit enforcement and fault-path tests) as the next Motion task, and set out how the two Motion tasks KOS-MOTION-001 and KOS-MOTION-002 could become approved, weighted baseline tasks, following the path Sense took in D-078 and D-099. This plan does not edit `baseline.json`, `approvals.json` or `gate_closures.json`. The baseline changes only through the owner-run freeze below, and no credit follows from a proposal.

## Current state (2026-11-04)

- The baseline is version 8: 41 tasks, total weight 153, 10 milestones. It contains no MOTION task or milestone.
- `v2/planning/milestones.json` carries V2-M1-MOTION-001 (planning date 2026-11-30) and V2-M2-MOTION-001 (2027-01-15, D-076) as PROPOSED with empty task lists. The V2-M2 outcome reads "Command validation, limit enforcement and fault-path tests pass; gates implemented". Under D-093 the planning layer stays separate from the baseline.
- `v2/tracking/workstreams.json` lists MOTION with `repo: null`, and no status source is registered for it.
- kritva-motion: KOS-MOTION-001 is IN_PROGRESS in `planning/TASKS.md`. Its package (architecture, decision register MOTION-AD-001 to 044, contract v0.1.0-draft, five JSON schemas, error codes, conformance test plan) is merged as PROPOSED (pull request #9, merge commit d28611442a1d6adbd04a6af66b0bdb1d3eecd067) and recorded in D-098. It is not reviewed, not accepted and not tagged. Its acceptance criteria AC-001..AC-005 are PROPOSED.
- kritva-motion `ACCEPTANCE_CRITERIA.md` already says `make test-unit` stays NOT_IMPLEMENTED "until KOS-MOTION-002". `make test-integration` and `make test-regression` are NOT_IMPLEMENTED with no task.
- Architecture and safety review is held by the owner on an interim basis (D-047); the author and the approver are the same person until an independent reviewer exists.

## What KOS-MOTION-002 would deliver

A software-only reference validator for the Motion contract and the tests that run it. No runtime, no hardware, no backend, no simulator.

In scope:

1. Configuration validation (contract 3): completeness and consistency, policy vocabularies, continuous joints, backend capability checks.
2. The fixed admission order of contract 8.4, reporting the first failure, with every admission code of `ERROR_CODES.md` section 1 reached by at least one fixture.
3. Limit enforcement (contract 8.3): the intersection of backend, configuration and command limits, widening rejected, non-finite values rejected.
4. Joint-state preconditions (contract 8.6): the exemption matrix, `TARGET_STATE_UNKNOWN`, `TARGET_FAULTED`, `TARGET_DEGRADED` and feedback freshness, evaluated against a supplied joint-state snapshot. These are the "fault-path" cases that this task covers: admission decisions on a joint that is faulted, degraded or unknown.
5. Schema evidence: the five JSON schemas with positive and negative example documents, run by `make test-unit` (today these 38 cases exist only as an out-of-repo script).
6. A machine-checked mapping from implemented tests to conformance test IDs and contract sections, so a missing, duplicated or skipped test fails the gate.

Out of scope (each needs its own proposal and decision; none is registered here):

- The lifecycle, termination, fault-propagation and recovery state machine (contract 7, 9, 10, 13.4 and 13.9). The proposal names this as a candidate KOS-MOTION-003 and does not register it.
- Integration and regression gates, the Execution Backend Interface implementation, simulators, any physical actuator adapter, firmware, Mind or Skill integration.
- Any hardware-in-loop or physical safety validation (gate V2-M6, HOLD). Software acceptance of this task is never physical or safety validation.

Honest note on the milestone: V2-M2-MOTION-001 promises "gates implemented". KOS-MOTION-002 implements `make test-unit` only, so closing V2-M2 would need further tasks for the integration and regression gates, as Sense needed KOS-SENSE-009 and KOS-SENSE-010. The proposal does not claim otherwise.

## Draft criteria for kritva-motion (AC-201..AC-207)

To be added to kritva-motion `ACCEPTANCE_CRITERIA.md` as a new section, leaving AC-001..AC-005 untouched, with a TASKS.md row. `ACCEPTANCE_CRITERIA.md` is a protected path of the pull request gate, so this change needs the owner.

| ID | Criterion (testable) | Verified by |
|---|---|---|
| AC-201 | The validator rejects an invalid configuration at activation: unknown policy values, a continuous joint with position mode, `DEGRADE` with `feedback_required` true, a degradation policy that lists `SET_POSITION` or `HOLD` for `FEEDBACK_OPTIONAL_UNAVAILABLE`, and a policy the declared backend capabilities cannot satisfy. | unit tests with fixtures |
| AC-202 | Admission validation runs in the fixed order of contract 8.4 and reports only the first failure. Every admission code in `ERROR_CODES.md` section 1 is reached by at least one fixture, and a fixture that violates two steps reports the earlier step. | unit tests |
| AC-203 | Effective limits are the intersection of backend, configuration and command constraints. A constraint that widens a limit is rejected `INVALID_CONSTRAINT`; out-of-limit values are rejected `LIMIT_POSITION`, `LIMIT_VELOCITY` or `LIMIT_ACCELERATION`; non-finite numbers are rejected `NON_FINITE_VALUE`. | unit tests |
| AC-204 | Joint-state preconditions follow the exemption matrix of contract 8.6 for `UNKNOWN`, `FAULTED` and `DEGRADED` snapshots, including `TARGET_STATE_UNKNOWN` with health `READY`, and feedback freshness. `STOP`, `CANCEL`, queries and `CLEAR_FAULT` follow their own rows. | unit tests |
| AC-205 | The five schemas validate their positive example documents and reject their negative ones. Every CT-SCH test ID in the conformance plan has an executable case. | `make test-unit` |
| AC-206 | A machine-checked mapping links each implemented test to a conformance test ID and contract section. The gate fails on a missing, duplicated, unmapped or skipped test. Tests are deterministic: no clock, randomness or network. | `make test-unit` |
| AC-207 | The validator performs no I/O toward a backend or device. The documentation states that passing tests is software evidence only and never physical or safety validation. | review (independent safety reviewer when assigned) |

## Decisions needed from Dinesh

| # | Decision | Recommendation |
|---|---|---|
| 1 | Approve KOS-MOTION-002 as the next Motion task, with the scope above | Approve. The scope is bounded and the criteria already point to it |
| 2 | Baseline KOS-MOTION-001 and KOS-MOTION-002 together, as Sense did for its first two tasks, or baseline neither yet | Together. Without KOS-MOTION-001 in the baseline, accepting it would earn no credit and its evidence would have nowhere to be recorded. Baselining does not accept anything |
| 3 | Initial weights | The draft proposal uses 5 and 5 (estimated 4 to 7 effort days each), drafted with an AI assistant. They are estimates, not recorded effort, and the owner approves them |
| 4 | Language and dependencies for the validator | Recommend following the approach of kritva-sense's reference validator so the two repositories look alike; confirm it before approval. The default is Python 3 using only the standard library, with JSON Schema checks needing either a development-time dependency installed by the CI workflow or a vendored checker; the owner picks one. A production implementation in another language is a later task |
| 5 | Register the MOTION status source | `workstreams.json` has `repo: null` and kritva-motion has no `status/status.json`. Without a source, the two Motion tasks have nothing to report through. ONBOARDING.md and D-077 describe the steps. Recommend a separate small change (a status generator and registration, `Tasks: None` or a task ID from the owner) before or alongside the freeze, and an explicit decision on whether D-077's empty-report exception applies |
| 6 | The `unit-tests` required check for kritva-motion | A `unit-tests` workflow is needed for a real gate. Recommend the same sequence as D-097: add the workflow in kritva-motion, then record the required-check change centrally. The ruleset itself is an owner action and stays OWNER-ATTESTED |
| 7 | The AC-002 wording (A-2) and AC-006..AC-010 from KOS-MOTION-001 | Independent of this proposal. Recommend recording the interpretation in the review (option a) now and a formal amendment separately; AC-201..AC-207 do not depend on it |
| 8 | Interim reviewer independence | Accept D-047 as the review path and record that the review is not independent |

## Step sequence

1. This pull request (kritva-program): this plan and the DRAFT [baseline_v9_proposal.json](../tracking/baseline_v9_proposal.json). It changes no baseline, approval, gate or generated file.
2. Owner decisions in the table above. The owner records the approval as a new decision (next free number) in `v2/DECISIONS.md`.
3. kritva-motion pull request: TASKS.md row for KOS-MOTION-002, `tasks/KOS-MOTION-002/TASK.md` and the criteria AC-201..AC-207 (needs the owner because `ACCEPTANCE_CRITERIA.md` is protected). Sense merged its row and criteria before the baseline step.
4. Owner-run freeze, in one change:
   - add milestones V2-M1-MOTION-001 and V2-M2-MOTION-001 (workstream MOTION) and the approved tasks to `baseline.json` with weights null;
   - run the dry run, then the approved freeze (commands below);
   - re-approve the effective approvals on v9 with `tools/record_approvals.py`, because approvals bound to v8 would otherwise stop counting (D-027, D-078);
   - refresh the sources first so the CORE and COMMUNITY reports are inside the 14-day freshness window;
   - update the tests that hard-code baseline totals (today 41 tasks and weight 153; with the draft weights 43 and 163);
   - commit the frozen `baseline.json`, the baseline hash and the generated outputs together.
5. Regenerate the status snapshot and run consolidation. Credit stays zero until a task has passing evidence.
6. Implement KOS-MOTION-002 in kritva-motion through normal pull requests. Closure needs the approved COMPLETION_RECORD.md, an annotated SemVer tag and the evidence rules of the acceptance standard.

## Draft baseline entries (for the owner-run step)

Milestones: `{"id": "V2-M1-MOTION-001", "workstream_id": "MOTION"}` and `{"id": "V2-M2-MOTION-001", "workstream_id": "MOTION"}`.

Tasks (weights null in `baseline.json`; the weights and rationales are in the proposal):

| Task | Title | Milestone | requires_physical |
|---|---|---|---|
| KOS-MOTION-001 | Motion command and state contract | V2-M1-MOTION-001 | false |
| KOS-MOTION-002 | Command validation, limit enforcement and fault-path tests | V2-M2-MOTION-001 | false |

The baseline has no dependency field. The dependency (KOS-MOTION-002 depends on KOS-MOTION-001, and its acceptance begins after KOS-MOTION-001 is accepted) is recorded in kritva-motion.

## Owner-run freeze procedure

Run from the repository root by the owner only, after the decision pull request is merged and anchored to that merged commit.

```
python3 tools/freeze_baseline.py --root . --proposal v2/tracking/baseline_v9_proposal.json
python3 tools/freeze_baseline.py --root . --proposal v2/tracking/baseline_v9_proposal.json --approve
```

The first is a dry run that writes nothing. Check the stated task count, total weight and hash before approving.

## Invariants and verification

- No agent edits `baseline.json`, `approvals.json` or `gate_closures.json` without an owner decision.
- Credit comes only from approved baseline tasks with passing evidence; weights are never derived from effort claims in this plan.
- Before this pull request: `python3 -m unittest discover -s tests` and `python3 tools/consolidate_status.py --sources-dir sources --check`.

## Risks

- Baselining KOS-MOTION-001 before it is reviewed gives a weighted task whose only evidence is a draft. It carries no credit until it has passing evidence and an approval.
- Without a MOTION status source and a `unit-tests` workflow, neither task can report evidence, so baselining first gives zero credit by design.
- The task title says "fault-path tests", but only admission-time fault, degraded and unknown cases belong to this task. Readers may expect the whole fault state machine; the plan says it does not.
- Self-approval under D-047 is a known limitation, not independent review.
- The kritva-core security interface and upstream versions are unpinned, so contract section 16 stays PROVISIONAL; the validator treats authorization as a supplied input.
- The private program record also needs the MOTION registration (D-075) if the owner wants it there.

## What this plan does not authorize

Approval of KOS-MOTION-001 or KOS-MOTION-002, any weight, any baseline change, any gate closure, a status source, a required check, implementation of the validator, hardware or safety claims, or a release tag.
