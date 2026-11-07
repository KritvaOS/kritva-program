# M0 FOUNDATION: task definitions (proposed for owner approval)

**Status:** PROPOSED. Planning only: no weight is baselined, no credit, no approval. Weights are the owner-approved planning weights in [SEVEN_REPO_PLAN_REGISTER.md](SEVEN_REPO_PLAN_REGISTER.md) (D-109).
**Source of the outcomes:** `v2/planning/milestones.json` (`V2-M0` outcome and exit conditions, and the `V2-M0-*` repository milestones). The acceptance criteria below are drafted from those outcomes and need the owner's review before any repository copies them into its own `planning/TASKS.md`.
**Why this file exists:** M0 shows 0 of 34 accepted weight. Each task below says what has to be true for it to be accepted, so that it can be baselined, completed and credited. Credit still needs a baselined task, a central PASS approval, a COMPLETE task and CI evidence on the approved commit.

M0 outcome: governance contracts, status schemas, repository ownership, CI and PR conventions and evidence requirements are consistent and checked in every repository.

M0 exit conditions: (1) frozen baseline unchanged and reconciled; (2) acceptance standard, commit and tag policy approved and enforced in CI; (3) Core engineering contract pinned (`contract_pin`).

Common to every task: owner Dinesh; initial status as recorded in the register; evidence is a merged pull request in the owning repository and a passing CI run on the merged commit; no task changes another repository's records.

## Tasks

| Repository | Task ID | Title | Weight | Status | Depends on |
|---|---|---|---|---|---|
| Program | PROPOSED-NEW-PROGRAM-001 | Program governance and planning foundation | 5 | NOT_STARTED | none recorded |
| Program | PROPOSED-NEW-PROGRAM-003 | Program register and planning controls | 4 | NOT_STARTED | none recorded |
| Program | PROPOSED-NEW-PROGRAM-004 | Program approval and decision records | 3 | NOT_STARTED | none recorded |
| Program | PROPOSED-NEW-PROGRAM-005 | Program validation and governance checks | 3 | NOT_STARTED | none recorded |
| Core | PROPOSED-NEW-CORE-001 | Core engineering contract and version pin | 5 | IN_PROGRESS | PD-015 decided (D-113); contract merged and pinned; waits for baseline v11, approval and CI evidence |
| Community | PROPOSED-NEW-COMMUNITY-001 | Security reporting path and mailbox verification | 2 | NOT_STARTED | none recorded |
| Sense | PROPOSED-NEW-SENSE-001 | Sense governance and acceptance review | 3 | NOT_STARTED | none recorded |
| Mind | PROPOSED-NEW-MIND-GOV-001 | Mind governance and acceptance review | 3 | NOT_STARTED | none recorded |
| Motion | PROPOSED-NEW-MOTION-001 | Motion governance and acceptance review | 3 | NOT_STARTED | none recorded |
| Skill | PROPOSED-NEW-SKILL-GOV-001 | Skill governance and acceptance review | 3 | NOT_STARTED | none recorded |
| **Total** | | | **34** | | |

## Proposed acceptance criteria

### Program (kritva-program), V2-M0-PROGRAM-001: plan, registry, schemas, acceptance standard and pipeline manifest approved; status views generated from them

- PROPOSED-NEW-PROGRAM-001 (5): the V2 plan, repository registry, status schema and pipeline manifest are approved by the owner and consistent with each other; the frozen baseline is unchanged and reconciled to the plan (exit condition 1); STATUS_VIEW.md and STATUS_DETAIL.md are generated from those records and `tools/consolidate_status.py --check` passes in CI.
- PROPOSED-NEW-PROGRAM-003 (4): the planning register and milestone records have automated validation (unique IDs, non-zero weights, totals that reconcile, sequencing check D-112) that runs in CI and fails the build on error; every counted plan row has an owner, a milestone and dependencies recorded.
- PROPOSED-NEW-PROGRAM-004 (3): approvals and decisions follow one documented procedure (append-only decision log, approvals ledger, who may approve, how a baseline is re-approved); a sample approval and a sample baseline amendment are shown to follow it end to end.
- PROPOSED-NEW-PROGRAM-005 (3): the acceptance standard, commit message policy and tag policy are approved and enforced by CI checks on pull requests (exit condition 2); a pull request that breaks each rule is shown to fail.

### Core (kritva-core), V2-M0-CORE-001: engineering contract approved and pinned; contract_pin check closed

- PROPOSED-NEW-CORE-001 (5): the Core engineering contract is drafted and approved; a pin file records the contract's exact commit SHA and SHA-256; a CI check fails when the pin and the contract differ; the readiness check `contract_pin` passes (exit condition 3). PD-015 is decided (D-113); the contract is merged and pinned in kritva-core.

### Community (kritvaos-community), V2-M0-COMMUNITY-001: security reporting path working

- PROPOSED-NEW-COMMUNITY-001 (2): SECURITY.md names a reporting contact; a test message to that contact is received and recorded (date and who received it); the readiness check `security_policy` passes.

### Sense, Mind, Motion, Skill: repository governance baseline merged (one task each)

- PROPOSED-NEW-SENSE-001, PROPOSED-NEW-MIND-GOV-001, PROPOSED-NEW-MOTION-001 and PROPOSED-NEW-SKILL-GOV-001 (3 each): the repository has merged acceptance criteria for its tasks, the CI checks required by the program (commit message check and pull request acceptance gate), a CODEOWNERS file and an AGENTS.md; the repository's readiness checks for these items pass; its status report is generated and matches the program's records.

## Open points for the owner

- Confirm or edit the criteria above. Once approved, each repository adds its task to its own `planning/TASKS.md` through a pull request in that repository (initial status NOT_STARTED, no weight, no credit).
- PD-015 is decided (D-113), so PROPOSED-NEW-CORE-001 is no longer blocked.
- Dependencies between M0 tasks are not recorded anywhere yet; none are assumed here.
- The M0 target date 2026-10-30 has passed with M0 not closed (see the Sequence column in STATUS_VIEW.md). Re-confirm or move the date.
