# V2-M1 STUDIO: Closure Execution Plan

**Status:** PROPOSED — execution guidance for owner review; not an approval, baseline amendment, schedule reforecast, task acceptance, or milestone completion record.

**Plan owner:** Dinesh (program owner)  
**Milestone:** `V2-M1` — STUDIO  
**Current approved target:** 2026-12-31 (D-160, 2026-11-27; replaces the withdrawn D-076 M1 date)  
**Baseline reference:** approved baseline v17  
**Status snapshot reviewed:** `v2/tracking/STATUS_VIEW.md`, generated 2026-11-28T07:35:06Z

## 1. Purpose

This plan defines a controlled, evidence-led route to close V2-M1. It orders the remaining M1 work, makes cross-repository dependencies explicit, defines task-level exit evidence, and describes the milestone-level review and completion-record process.

The plan is intentionally limited to the approved M1 scope and the M1 exit conditions already recorded in `v2/planning/milestones.json`. It does not create tasks, change task weights, grant credit, approve acceptance criteria, change the frozen baseline, or authorize implementation in another repository.

## 2. Current position

The 2026-11-28 generated status view reports:

| Measure | Snapshot |
|---|---:|
| M1 accepted | 4 of 8 tasks |
| M1 accepted weight | 19 of 36 |
| Remaining | 4 tasks |
| Remaining weight | 17 |

The four remaining items shown in the M1 block are:

| Repository | Task ID | Current status | Weight | Plan disposition |
|---|---|---:|---:|---|
| Community | `PROPOSED-NEW-COMMUNITY-002` | NOT_STARTED | 4 | Architecture reconciliation |
| Community | `PROPOSED-NEW-COMMUNITY-018-01` | NOT_STARTED | 4 | Contract inventory and compatibility matrix |
| Community | `PROPOSED-NEW-COMMUNITY-018-02` | NOT_STARTED | 4 | Automated pin/version compatibility checks |
| Skill | `KOS-SKILL-001` | IN_PROGRESS | 5 | Skill manifest and execution contract |

The four credited M1 tasks in the snapshot are `KOS-SENSE-001`, `KOS-MIND-001`, `KOS-MOTION-001` and `KOS-SDK-001`. Their existing credit is not reopened by this plan. Revisit only if new evidence identifies a regression or invalid acceptance.

**Important accounting distinction:** the Community items are approved planning rows and Skill-001 is an approved planning task in the program register, but planning approval is not baseline inclusion or task credit. Under baseline v17, approved-plan tasks earn no credit until separately baselined, completed, accepted and supported by the required evidence. Do not modify `v2/tracking/baseline.json`, approvals or gate-closure records as part of executing this plan.

## 3. Milestone outcome and formal exit conditions

The authoritative V2-M1 outcome in `v2/planning/milestones.json` is:

> Studio scope and the capability interfaces it consumes are defined; the first capability contracts (Sense, Motion, Mind, Skill) are reviewed.

The recorded milestone exit conditions are:

1. P0 exit review passed (DEP-001).
2. Contract task 001 of each capability repository reviewed and tagged `v0.1.0`.
3. Studio ownership location (repository or component) decided.

This plan supplements those conditions with an evidence checklist; it does not replace or weaken them. The milestone completion review must verify each condition against an authoritative decision, review, tag or other immutable evidence. A task marked complete in a status table is not, by itself, proof that an M1 exit condition is satisfied.

## 4. Dependency model and recommended order

### 4.1 Dependency graph

```text
Community-002: reconcile existing system architecture
                  |
                  v
Community-018-01: inventory approved contracts and compatibility
                  |
                  v
Community-018-02: implement deterministic pin/version checks
                  |
                  +------------------------------+
                                                 |
Skill-001: manifest and execution contract ------+--> integrated M1 contract review
  (progress in parallel; reconcile final pins)         |
                                                       v
                                            M1 exit review and record
```

The program register already declares the sequence:

- `PROPOSED-NEW-COMMUNITY-018-01` depends on `PROPOSED-NEW-COMMUNITY-002`.
- `PROPOSED-NEW-COMMUNITY-018-02` depends on `PROPOSED-NEW-COMMUNITY-018-01`.

Do not start 018-02 before the inventory and its compatibility rules are reviewable. Skill-001 is a parallel workstream: its design and contract drafting can proceed while Community-002 and 018-01 are underway, but its final dependency pins and cross-repository references must be reconciled against the approved inventory before acceptance.

### 4.2 Execution waves

| Wave | Work | Entry condition | Exit condition |
|---|---|---|---|
| A — Architecture | Community-002 | Plan acknowledged; current architecture and decisions collected | Existing architecture reconciled, ownership/boundaries reviewed, evidence linked |
| B — Contract inventory | Community-018-01 | Community-002 architecture direction is stable and reviewed | Inventory/matrix complete, source pins traceable, compatibility rules reviewed |
| Parallel — Skill contract | KOS-SKILL-001 | Owner-approved task acceptance criteria and authoritative dependency contracts identified | Manifest/execution contract reviewed, criteria evidenced, final pins reconciled with inventory |
| C — Automation | Community-018-02 | 018-01 inventory and rules accepted for implementation | Deterministic checker and positive/negative fixtures integrated in CI |
| D — Integration and closure | All M1 items and milestone exit conditions | Task evidence complete; no unresolved blocking discrepancy | Integrated review passes and approved M1 completion record is recorded |

Waves A and the Skill design work may run in parallel. Wave B follows A. Wave C follows B. The final review waits for all workstreams and all milestone exit conditions.

## 5. Task execution packages and acceptance evidence

### 5.1 Community — PROPOSED-NEW-COMMUNITY-002

**Register title:** Cross-capability architecture documentation  
**Execution approach:** reconcile the existing Community `ARCHITECTURE.md`; do not create a competing architecture source or rewrite the document without a demonstrated need.

Required scope:

- Confirm repository/component ownership and responsibilities against current program decisions.
- Reconcile Core, Sense, Mind, Motion, Skill and SDK boundaries and dependency direction.
- Reflect current placement decisions: SDK in `kritva-sdk` (D-149); Studio in Community; Control Plane as a separate planned repository; Sim placement remains open unless subsequently decided.
- Clearly distinguish planned components and intended interfaces from implemented integrations.
- Identify authoritative contract sources and avoid copying detailed contracts into the system architecture.
- Resolve inconsistencies between architecture diagrams, explanatory text and approved decisions.

**Acceptance evidence:**

- Merged architecture reconciliation with immutable merge commit.
- Review record identifying the architecture version/commit reviewed.
- Traceability from material ownership and placement statements to the relevant program decisions.
- Explicit list of unresolved questions; unresolved items that affect M1 exit must be escalated, not silently treated as complete.

**Out of scope:** implementing Control Plane, Studio, SDK adapters, runtime integration, or physical/hardware architecture changes.

### 5.2 Community — PROPOSED-NEW-COMMUNITY-018-01

**Register title:** Capability contract inventory and compatibility matrix  
**Prerequisite:** Community-002.

Required scope:

- Inventory the authoritative, versioned contract sources for Core, Sense, Mind, Motion and Skill, and the SDK/Studio interfaces where they are relevant to the M1 architecture.
- For every entry, record owning repository, contract/task identifier, version or immutable commit reference, canonical path, review/approval evidence and status.
- Distinguish approved/pinned contracts from proposed, draft, implemented-but-unreviewed or unavailable contracts.
- Record dependency direction, required interface/version constraints and compatibility policy.
- Record unresolved version choices as explicit blockers or owner decisions; never invent a version pin or infer approval from a tag alone.
- Keep the inventory a navigational/compatibility index, not a duplicate copy of the source contracts.

**Acceptance evidence:**

- Version-controlled inventory and compatibility matrix merged.
- Every row has a traceable authoritative source and an unambiguous state.
- Review confirms that version pins refer to reviewed/approved contract revisions.
- Missing or incompatible references are explicitly represented and are not labelled compatible.

**Out of scope:** implementing capability APIs, changing source contracts, or unilaterally approving another repository's contract.

### 5.3 Community — PROPOSED-NEW-COMMUNITY-018-02

**Register title:** Automated version and pin compatibility checks  
**Prerequisite:** Community-018-01.

Required scope:

- Validate that required contract references exist and are immutable/reproducible.
- Validate declared versions and compatibility rules against the accepted inventory.
- Detect missing pins, malformed pins, unsupported version combinations and stale references according to the agreed policy.
- Provide deterministic, actionable failure output suitable for CI.
- Add positive fixtures for valid combinations and negative fixtures for each failure class.
- Integrate the checker into the Community repository's required CI path, using existing repository conventions.

**Acceptance evidence:**

- Merged implementation and documented invocation.
- Positive and negative fixtures with expected results.
- CI run on the exact closing commit showing the required checks passed.
- Review confirms that unspecified or unknown compatibility is rejected or reported as unresolved, never silently accepted.

**Out of scope:** a general-purpose dependency manager, automatic contract upgrades, or changing the source-of-truth contract versions.

### 5.4 Skill — KOS-SKILL-001

**Repository task title:** Skill manifest and execution contract  
**Program status:** IN_PROGRESS; repository acceptance criteria currently state that criteria are proposed and the unit/integration/regression gates are not implemented.

The repository's `ACCEPTANCE_CRITERIA.md` is the task-level source. Its criteria include manifest identity/version/capabilities and input/output schemas; preconditions; lifecycle; resource and failure reporting; one-way dependency direction; and independent resolution, validation and authorization of proposals before execution.

Required sequence:

1. Owner reviews and approves the task acceptance criteria before treating proposed criteria as normative.
2. Reconcile normative dependencies with approved Core, Mind and Motion contracts; record exact approved versions or immutable references when available. Do not manufacture pins.
3. Specify the manifest and execution contract: identity, version, declared capabilities, input/output schemas, preconditions, lifecycle, resource/failure reporting, error semantics and versioning.
4. Specify the proposal path so a proposal is not itself an executable authorization; a declined or invalid proposal executes nothing and the execution report traces to its proposal.
5. Verify that Skill consumes declared capability interfaces and that capability repositories do not depend on Skill.
6. Add contract-level examples and reviewable evidence for the criteria that M1 owns.
7. Record any criteria that require M2 implementation gates as deferred to M2; do not claim unimplemented gates pass.

**M1 boundary:** deliver and review the manifest and execution contract. Full manifest validation and lifecycle conformance implementation belongs to the planned M2 work; Control Plane exposure belongs to M3; simulated runtime execution belongs to M5. M1 acceptance must not pull those later implementation scopes forward.

**Acceptance evidence:**

- Owner-approved acceptance-criteria revision and review reference.
- Merged manifest/execution contract and immutable commit.
- Traceable approved dependency references, or an explicit owner-approved disposition for any dependency not yet available.
- Dependency-direction review and proposal authorization/traceability examples.
- Exact closing-commit CI results for implemented required checks. Any `NOT_IMPLEMENTED` gate remains visible and cannot be counted as PASS.
- Repository task acceptance record and status update.

## 6. Integrated cross-repository review

After the four task packages are ready, conduct one integrated review. The review should confirm:

1. The Community architecture and contract inventory describe the same component ownership and dependency direction.
2. The compatibility checker enforces the policy documented by the inventory; fixtures cover both valid and invalid combinations.
3. Skill consumes the approved contracts and does not introduce reverse dependencies.
4. Skill proposal handling separates proposal, validation, authorization and execution, with traceable disposition.
5. The M1 contract set is internally consistent and version references resolve to immutable evidence.
6. Planned M2/M3/M5 implementation is clearly deferred and is not represented as delivered.
7. The formal milestone exit conditions in section 3 are independently evidenced.

Any discrepancy that changes scope, contract meaning, ownership or an approved decision must be resolved through the appropriate repository review or program decision process. The integrated review cannot waive an owner decision.

## 7. Evidence, review and status rules

Apply the approved V2 Acceptance Standard and each repository's own required checks.

For every task, retain:

- Stable task ID and accepted criteria revision.
- PR URL and merge commit SHA.
- Required review references tied to the closing commit.
- Required CI check names, run IDs and results for the exact closing commit.
- Test/fixture evidence and documentation/changelog updates.
- Immutable contract references and any approved decision/waiver references.
- Canonical repository status update.

Use immutable commit SHAs and CI run IDs, not branch names or mutable links, as acceptance evidence. A merge, tag, passing CI run, or status label alone does not close a task or milestone.

A waiver must be explicit, scoped, approved and traceable under the program's waiver process. A waiver is never reported as PASS. Unimplemented gates are never passes. Software evidence does not imply hardware, safety or physical validation.

## 8. Program tracking and baseline controls

- This document is a planning/coordination artifact only.
- Do not edit the frozen baseline, approval ledger, gate-closure ledger or generated status views to make progress appear complete.
- Do not change task IDs, weights, milestone allocation or credit through this plan.
- Before claiming weighted credit for approved-plan work, follow the separate owner-approved baseline amendment process; then satisfy the task DoD and evidence rules.
- Update source repository task/status records through their normal PR process. Regenerate program status outputs using the program's prescribed tooling after approved source changes.
- If execution reveals that a task's scope or acceptance criteria need material change, stop and propose the change to the owner; do not silently expand this plan.

## 9. Milestone completion record

M1 closes only when an approved `COMPLETION_RECORD.md` exists at the authoritative location specified by the program milestone process and `closure_record` is set in `v2/planning/milestones.json` through the owner-approved process.

The completion record must identify:

- Milestone ID `V2-M1` and scope.
- Exact merge/release commits and tag, or an explicit "none" where no release artifact is produced.
- Task-level acceptance disposition and links to immutable evidence.
- P0 exit review evidence (DEP-001).
- Reviewed/tagged `v0.1.0` evidence for contract task 001 of each capability repository, as required by the milestone definition.
- Studio ownership decision reference.
- Required CI run IDs, reviews and approvals.
- Deferred work and its milestone/decision disposition.
- Any approved waiver, clearly marked WAIVED rather than PASS.

Do not create or approve a completion record while any required exit condition is unsupported. The status generator, not a manual edit to `STATUS_VIEW.md`, reports the milestone as closed after the authoritative closure record is approved and recorded.

## 10. Risks and escalation triggers

| Risk | Trigger | Required response |
|---|---|---|
| Architecture and contract inventory disagree | Ownership, interface or dependency direction differs | Stop dependent inventory/checker work; reconcile against decisions and source repositories |
| A capability contract is not approved or pinned | No reviewed immutable reference exists | Mark unresolved; request owner disposition; do not invent a pin |
| Skill criteria remain proposed | No approval record exists | Do not claim task acceptance; obtain owner approval first |
| Skill acceptance depends on unimplemented M2 gates | Unit/integration/regression gates are still NOT_IMPLEMENTED | Keep those gates visible; limit M1 claim to contract deliverable; track implementation in M2 |
| Checker policy is ambiguous | Matrix does not define unknown/missing version behaviour | Resolve policy before implementation; default to fail/report unresolved, never assume compatibility |
| M1 exit conditions lack evidence | P0 review, contract tags/reviews or Studio ownership decision cannot be verified | Keep M1 open and escalate; task completion does not substitute for exit evidence |
| Baseline/credit confusion | Planning task completion is reported as weighted credit | Correct status/reporting; use separate baseline amendment and acceptance process |

## 11. Owner decisions and confirmations required

The following are explicit checkpoints for the owner; this plan does not make these decisions:

- Approve the task acceptance criteria for KOS-SKILL-001.
- Confirm the interpretation and evidence location for DEP-001 (P0 exit review) and the contract task-001 `v0.1.0` exit condition.
- Confirm the authoritative record for the Studio ownership decision, or record the decision if still open.
- Approve any needed baseline amendment separately before planning-only tasks can earn credit.
- Approve the final M1 completion record and milestone closure.

## 12. Proposed working sequence

1. Acknowledge this plan and confirm owner checkpoints.
2. Start Community-002 architecture reconciliation; run Skill-001 criteria/contract design in parallel.
3. Review and merge Community-002.
4. Build and review Community-018-01 from the reconciled architecture and authoritative contract sources.
5. Reconcile Skill-001 final pins and contract against the accepted inventory; complete its task review.
6. Implement Community-018-02 only against the reviewed inventory/rules; validate positive and negative fixtures in CI.
7. Perform the integrated cross-repository review and verify all formal M1 exit conditions.
8. Complete task acceptance and any separate baseline amendment/credit process that the owner authorizes.
9. Prepare, review and approve the M1 completion record; record `closure_record` through the owner-approved process.
10. Regenerate and inspect program status outputs; verify M1 is shown closed only from the recorded completion record.

## 13. References

- [M1 status view](../tracking/STATUS_VIEW.md)
- [Detailed status](../tracking/STATUS_DETAIL.md)
- [Seven-repository plan register](SEVEN_REPO_PLAN_REGISTER.md)
- [V2 milestone definitions](milestones.json)
- [V2 acceptance standard](ACCEPTANCE_STANDARD.md) (pointer to the current common standard is at the top of that file)
- [Completion record template](templates/COMPLETION_RECORD.template.md)
- [Community architecture](https://github.com/KritvaOS/kritvaos-community/blob/main/ARCHITECTURE.md)
- [Skill task inventory](https://github.com/KritvaOS/kritva-skill/blob/main/planning/TASKS.md)
- [Skill acceptance criteria](https://github.com/KritvaOS/kritva-skill/blob/main/ACCEPTANCE_CRITERIA.md)
