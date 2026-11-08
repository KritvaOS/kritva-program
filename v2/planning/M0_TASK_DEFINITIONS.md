# M0 FOUNDATION: task definitions (proposed for owner approval)

**Status:** BASELINED in v11 once the owner freezes it (D-117); until then proposed. Baselining awards no credit and no approval. Weights are the owner-approved planning weights in [SEVEN_REPO_PLAN_REGISTER.md](SEVEN_REPO_PLAN_REGISTER.md) (D-109). Baseline IDs replace the former register IDs `PROPOSED-NEW-*` (mapping in section 9 of the register).
**Source of the outcomes:** `v2/planning/milestones.json` (`V2-M0` outcome and exit conditions, and the `V2-M0-*` repository milestones). The acceptance criteria below are drafted from those outcomes and need the owner's review before any repository copies them into its own `planning/TASKS.md`.
**Why this file exists:** M0 had 34 baseline weight; D-119 descoped KOS-COMMUNITY-M0-001 (2), leaving 32. Each task below says what has to be true for it to be accepted, so that it can be baselined, completed and credited. Credit still needs a baselined task, a central PASS approval, a COMPLETE task and CI evidence on the approved commit.

M0 outcome: governance contracts, status schemas, repository ownership, CI and PR conventions and evidence requirements are consistent and checked in every repository.

M0 exit conditions: (1) frozen baseline unchanged and reconciled; (2) acceptance standard, commit and tag policy approved and enforced in CI; (3) Core engineering contract pinned (`contract_pin`).

Common to every task: owner Dinesh; initial status as recorded in the register; evidence is a merged pull request in the owning repository and a passing CI run on the merged commit; no task changes another repository's records.

## Tasks

| Repository | Task ID | Title | Weight | Status | Depends on |
|---|---|---|---|---|---|
| Program | KRP-M0-001 | Program governance and planning foundation | 5 | NOT_STARTED | none recorded |
| Program | KRP-M0-002 | Program register and planning controls | 4 | NOT_STARTED | none recorded |
| Program | KRP-M0-003 | Program approval and decision records | 3 | NOT_STARTED | none recorded |
| Program | KRP-M0-004 | Program validation and governance checks | 3 | NOT_STARTED | none recorded |
| Core | KF-CORE-M0-001 | Core engineering contract and version pin | 5 | IN_PROGRESS | PD-015 decided (D-113); contract merged and pinned; waits for completion, approval and CI evidence on the baselined task |
| Sense | KOS-SENSE-M0-001 | Sense governance and acceptance review | 3 | NOT_STARTED | none recorded |
| Mind | KOS-MIND-M0-001 | Mind governance and acceptance review | 3 | NOT_STARTED | none recorded |
| Motion | KOS-MOTION-M0-001 | Motion governance and acceptance review | 3 | NOT_STARTED | none recorded |
| Skill | KOS-SKILL-M0-001 | Skill governance and acceptance review | 3 | NOT_STARTED | none recorded |
| **Total** | | | **32** | | |

## Proposed acceptance criteria

### Program (kritva-program), V2-M0-PROGRAM-001: plan, registry, schemas, acceptance standard and pipeline manifest approved; status views generated from them

- KRP-M0-001 (5): the V2 plan, repository registry, status schema and pipeline manifest are approved by the owner and consistent with each other; the frozen baseline is unchanged and reconciled to the plan (exit condition 1); STATUS_VIEW.md and STATUS_DETAIL.md are generated from those records and `tools/consolidate_status.py --check` passes in CI.
- KRP-M0-002 (4): the planning register and milestone records have automated validation (unique IDs, non-zero weights, totals that reconcile, sequencing check D-112) that runs in CI and fails the build on error; every counted plan row has an owner, a milestone and dependencies recorded.
- KRP-M0-003 (3): approvals and decisions follow one documented procedure (append-only decision log, approvals ledger, who may approve, how a baseline is re-approved); a sample approval and a sample baseline amendment are shown to follow it end to end.
- KRP-M0-004 (3): the acceptance standard, commit message policy and tag policy are approved and enforced by CI checks on pull requests (exit condition 2); a pull request that breaks each rule is shown to fail.

### Core (kritva-core), V2-M0-CORE-001: engineering contract approved and pinned; contract_pin check closed

- KF-CORE-M0-001 (5): the Core engineering contract is drafted and approved; a pin file records the contract's exact commit SHA and SHA-256; a CI check fails when the pin and the contract differ; the readiness check `contract_pin` passes (exit condition 3). PD-015 is decided (D-113); the contract is merged and pinned in kritva-core.

### Community (kritvaos-community), V2-M0-COMMUNITY-001: DESCOPED by D-119 (baseline v12)

The owner waived the mailbox test (PD-017) and the task was removed from the baseline on 2026-11-08. It was not tested, accepted or credited. The criterion below is kept for the record only.

- KOS-COMMUNITY-M0-001 (2): SECURITY.md names a reporting contact; a test message to that contact is received and recorded (date and who received it); the readiness check `security_policy` passes.

### Sense, Mind, Motion, Skill: repository governance baseline merged (one task each)

- KOS-SENSE-M0-001, KOS-MIND-M0-001, KOS-MOTION-M0-001 and KOS-SKILL-M0-001 (3 each): the repository has merged acceptance criteria for its tasks, the CI checks required by the program (commit message check and pull request acceptance gate), a CODEOWNERS file and an AGENTS.md; the repository's readiness checks for these items pass; its status report is generated and matches the program's records.

## Open points for the owner

- Freezing baseline v11 approves these criteria and weights. Each repository then adds its task to its own `planning/TASKS.md` through a pull request in that repository (initial status NOT_STARTED, no credit), and reports it in `status/status.json` (the program rejects a task ID it has not baselined).
- PD-015 is decided (D-113), so KF-CORE-M0-001 is no longer blocked.
- Dependencies between M0 tasks are not recorded anywhere yet; none are assumed here.
- The M0 target date was 2026-10-30; the owner moved it to 2026-11-08 and closed V2-M0 in D-118.
