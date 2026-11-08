# Approval procedure (decisions, approvals, baseline freezes)

**Task:** KRP-M0-003 (PROGRAM-004). **Owner:** Dinesh. **Status:** PROPOSED for owner review; it describes what the tools in `tools/` already enforce and adds no new rule.
**Related:** [ACCEPTANCE_STANDARD.md](ACCEPTANCE_STANDARD.md) (definition of done, section 1; PR sequence, section 6), `v2/DECISIONS.md`, `v2/tracking/approvals.json`, `v2/tracking/baseline.json`.

## 1. What is recorded where

| Record | File | Written by | Rule |
|---|---|---|---|
| Decision log | `v2/DECISIONS.md` (and `v2/planning/decisions.json`) | a PR from the owner or Claude | Append-only. A decision is never edited to change its meaning. A changed decision is a new D-number that names the one it replaces. |
| Baseline (task IDs, weights, ownership) | `v2/tracking/baseline.json` and `v2/tracking/baselines/baseline_v<N>.json` | `tools/freeze_baseline.py --approve`, owner only | A frozen version is immutable. The file carries an `approval` block with the approver, UTC time, commit and SHA-256 of the data. The consolidator re-checks the hash on every run. |
| Approvals ledger | `v2/tracking/approvals.json` | `tools/record_approvals.py --approve` and `tools/carry_forward_approvals.py --approve`, owner only | Append-only. Records are never edited or deleted. A changed decision adds a record whose `supersedes` names the old `approval_id`. |
| Task evidence | `v2/tracking/evidence_map_proposal.json` | a PR | One row per task: evidence commit and the CI run on it. It is input to approvals, not an approval. |
| Repository status | each repository's `status/status.json` | that repository's generator | Reported, never inferred. The program reads it through `sources/` (`tools/refresh_sources.py`). |

Claude prepares proposals and scripts. Only the owner runs the `--approve` commands. Nothing here runs without `--approve`: the default of every tool is a dry run.

## 2. Who may approve

`authorized_approvers` in `approvals.json` lists the people allowed to record an approval; today it is `Dinesh`. A record whose `approver` is not on the list is refused, and the value must match exactly. Reviews are owner-held under the interim roles of D-047, so they are not independent reviews; that gap is recorded in the M0 completion record and stays open.

## 3. When a task earns credit

All of these must hold. Missing any one means no credit, and the status view shows why.

1. The task is in the frozen baseline with a positive integer weight and a rationale.
2. The owning repository reports it `COMPLETE` (its own tasks file and generated `status.json`).
3. Evidence points to a commit SHA and a CI run ID on that commit, never a branch.
4. The owner has recorded an effective `APPROVED` / `PASS` record bound to the current `baseline_version` and the same evidence commit.
5. No open credit gate applies to the task.

`python3 tools/consolidate_status.py --verify-runs` re-checks the cited runs against GitHub.

## 4. Procedure: approving completed tasks

1. In the owning repository, merge the PR that completes the task. CI must be green on the merge commit.
2. In `kritva-program`, add the task's row to `v2/tracking/evidence_map_proposal.json` (commit, task commit, CI run ID and URL, workflow, result).
3. Refresh the reports: `python3 tools/refresh_sources.py`. It requires each report's `source.commit` to be an ancestor of that repository's `main`; if it refuses, update the report's source commit first and merge that.
4. Dry run: `python3 tools/record_approvals.py --tasks <IDs>`. Read the review flags it prints (`MILESTONE`, `RERUN`).
5. Record: `python3 tools/record_approvals.py --tasks <IDs> --approver Dinesh --reason "<what you checked>" --approve`. The reason states that the acceptance criteria were met on the evidence commit, not only that CI was green.
6. Regenerate and verify: `python3 tools/consolidate_status.py`, then `--check` and `--verify-runs`.
7. Open a PR with the changed ledger and views. Merge it. The headline moves only after this merge.

A task already approved on the same commit is refused (nothing is duplicated). A task approved on an earlier commit gets a new record that names the old one in `supersedes`.

## 5. Procedure: changing the baseline

1. A proposal file `v2/tracking/baseline_v<N>_proposal.json` is prepared and reviewed in a PR.
2. The owner freezes it: `python3 tools/freeze_baseline.py --proposal <file> --approver Dinesh --commit "$(git rev-parse HEAD)" --reason "<why>" --approve`. It writes `v2/tracking/baselines/baseline_v<N>.json`, makes `baseline.json` identical, and appends the reason to `v2/tracking/baselines/CHANGELOG.json`.
3. Immediately after, with the same time, the owner carries approvals forward: `python3 tools/carry_forward_approvals.py --approver Dinesh --at <freeze time> --reason "<why>" --approve` (D-027). An approval is bound to one baseline version, so a freeze leaves every effective approval stale until this runs. It copies the evidence commit and run, names the old record in `supersedes`, and makes no new judgement. New tasks get nothing.
4. Record the decision as a new D-number and merge.

Editing `baseline.json` by hand after a freeze is reported as an error until a new version is frozen.

## 6. Worked examples from this program

- **Baseline v11 (D-117).** The ten V2-M0 tasks (weight 34) were added to the baseline; the ten rows left the counted plan register so no weight was counted twice (59 rows 275 to 49 rows 241; total plan weight stayed 446, V2 baseline 67 to 101). Approvals were carried forward onto v11 without new judgement.
- **M0 task approvals.** Sense, Mind, Motion and Skill were completed in their repositories, got CI evidence, then were recorded as the owner's PASS in one `record_approvals.py` run. Core followed once its `contract-pin-check` run on the merge commit passed. Credit appeared only after each recording PR merged.
- **Refresh refusal.** `refresh_sources.py` refused with "report source.commit is not an ancestor of main" for Program's own report. The fix was a PR moving `status/status.json` `source.commit` to the current `main` SHA, then re-running the approval. This is the intended behaviour: stale reports never feed credit.
- **Milestone closure (D-118).** V2-M0 closed through `v2/milestones/V2-M0/COMPLETION_RECORD.md` and `closure_record` in `milestones.json`. Closure is a separate act from credit: closing M0 awards no weight by itself.

## 7. Changing a decision or an approval

Never edit the old line or record. Add a new D-number or a new ledger record that names the old one. If an approval was wrong, record a superseding decision explaining it; the consolidator reports the effective record only.

## 8. Checks that protect this procedure

`tests/test_record_approvals.py`, `tests/test_baseline_reapproval.py` and `tests/test_credit_gating.py` cover the refusals above. CI runs them in the `status` workflow and in the `unit-tests` workflow (KRP-M0-004).
