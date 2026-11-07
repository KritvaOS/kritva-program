# M0 FOUNDATION: closure plan by repository (proposed)

**Status:** PROPOSED planning note. It records what exists today in each repository (read from the committed files; CI results were not re-run for this note) and what is left to close V2-M0. It changes no weight, credit, approval or gate.

## How M0 closes

1. Every item that blocks V2-M0 is resolved: reviews REV-001 to REV-007 (all `blocks: V2-M0`; approved by D-114) (PD-015, the Core engineering contract, is decided: D-113).
2. The V2-M0 items in scope but not blocking are settled or consciously deferred: PD-014 (register Mind, Sense, Skill and Motion on their workstreams; decided, D-116), PD-017 (test the Community security mailbox), PD-009 (status schema ownership; decided, D-116).
3. An approved `COMPLETION_RECORD.md` for V2-M0 exists and `closure_record` is set in `v2/planning/milestones.json`. Only then does the status view show M0 as closed, and the sequencing check (D-112) stops treating M1 and later as starting early.

Closing M0 does not award weighted credit. The 10 M0 plan tasks (34 weight, see [M0_TASK_DEFINITIONS.md](M0_TASK_DEFINITIONS.md)) earn credit only after they are baselined, completed, approved and backed by CI evidence. The reviews above are the natural acceptance evidence for those tasks, so baselining the M0 tasks before the reviews are recorded lets closure and credit line up.

## Repository by repository

### kritva-sense (task PROPOSED-NEW-SENSE-001, weight 3; review REV-004)

- Exists: ACCEPTANCE_CRITERIA.md, AGENTS.md, CODEOWNERS, `.github/kritva-gate.json`, workflows for secret-scan, commit-message-check, pr-acceptance-gate, readme-check and unit-tests, `status/status.json`, `planning/TASKS.md` (nine of ten tasks ACCEPTED).
- Left: REV-004 review recorded against a pinned commit (the review record has no commit SHA yet); the review role is held by the owner on an interim basis (D-047), so it is not independent.
- Effort: review only. Sense is the reference repository for the other three.

### kritva-motion (PROPOSED-NEW-MOTION-001, weight 3; REV-005)

- Exists: ACCEPTANCE_CRITERIA.md, AGENTS.md, CODEOWNERS, `.github/kritva-gate.json`, the same five workflows, `status/`, `planning/TASKS.md` (KOS-MOTION-001 and 002 ACCEPTED).
- Left: REV-005 recorded against a pinned commit. Separately, `planning/TASKS.md` still has no row for KOS-MOTION-003 (baselined weight 8); that is not an M0 item.

### kritva-mind (PROPOSED-NEW-MIND-GOV-001, weight 3; REV-006)

- Exists: ACCEPTANCE_CRITERIA.md, AGENTS.md, CODEOWNERS, `.github/kritva-gate.json`, the same five workflows, governance baseline merged (pull requests 1 to 8, per its MILESTONE_STATUS.md).
- Left: REV-006 recorded against a pinned commit. The repository has no `status/status.json`, so the program has no status source for it; PD-014 (register the repository on its workstream) and a status report would give it one. That is recommended for the "status schemas consistent in every repository" outcome but is not stated as an acceptance condition of the review.

### kritva-skill (PROPOSED-NEW-SKILL-GOV-001, weight 3; REV-007)

- Exists: ACCEPTANCE_CRITERIA.md, AGENTS.md, CODEOWNERS, `.github/kritva-gate.json`, workflows for secret-scan, commit-message-check, pr-acceptance-gate and readme-check. No unit-tests workflow (not in its required checks), no `src/` and no `status/`.
- Left: REV-007 recorded against a pinned commit; the repository's own MILESTONE_STATUS.md still says "IN_REVIEW (this change)" and should be refreshed when the review is recorded; same status-source gap as Mind (PD-014).

### kritvaos-community (PROPOSED-NEW-COMMUNITY-001, weight 2; PD-017)

- Exists: SECURITY.md with the contact dinesh@kritvaos.in and GitHub private vulnerability reporting. The Security Owner states the route was tested on 18 October 2026 (D-068); that is an owner statement, not verified from the repository.
- Left: PD-017, a recorded test email to the Security Owner's mailbox so the readiness check `security_policy` can move from OPEN to ATTESTED; then the task evidence (date and who received it) is written down.

### kritva-core (PROPOSED-NEW-CORE-001, weight 5; PD-015 decided)

- Exists: AGENTS.md, CODEOWNERS, SECURITY.md, commit-message-check, secret-scan, readme-check, source-header-check, status-report and core CI workflows.
- Done (D-113): PD-015 decided; `docs/development/ENGINEERING_CONTRACT.md` merged and pinned at commit 71a82e9b6e2ec3c6155270391adaa30e7751c1b9 (SHA-256 b57e24ba…7021) with the `contract-pin-check` workflow.
- Left: the owner adds `contract-pin-check` to the main ruleset and confirms the pinned text when D-113 merges; the task earns no credit until it is baselined, approved and CI-evidenced.

### kritva-program (PROPOSED-NEW-PROGRAM-001, -003, -004, -005, weight 5, 4, 3 and 3; REV-001, REV-002, REV-003; PD-009)

- Exists: v2/planning (milestones.json, repo-pipeline.json, ACCEPTANCE_STANDARD.md, reviews and decisions records), the generator and its checks (`tools/planning.py --check`, `tools/consolidate_status.py --check`, the new sequencing check), commit-message-check, secret-scan and readme-check workflows, decision log and approvals ledger.
- Left: REV-001 (milestone plan), REV-002 (pipeline manifest and approval roles) and REV-003 (acceptance standard) recorded against pinned commits (all three show `NOT_YET_PINNED`); PD-009 (confirm where decision, review, gate and milestone records live).

## Suggested order

1. Owner approves the M0 task definitions (criteria) and decides PD-014 and PD-017 (PD-015 is decided: D-113).
2. Record REV-001 to REV-003 for the program, then REV-004 to REV-007 repository by repository starting with Sense (nothing missing except the review), then Motion, Mind, Skill.
3. Run the Community mailbox test (PD-017); start Core contract drafting.
4. Baseline the 10 M0 tasks together with the Core and Community plan tasks in baseline v11 (no credit on baselining).
5. Complete and credit each M0 task as its review or test is recorded and CI evidence exists.
6. Write the V2-M0 completion record, get it approved, set `closure_record`, and regenerate the status view.

## What this note does not claim

No review has been done, no item above is accepted, and nothing here was verified by running CI. File presence in a repository is not acceptance.
