# Status Reporting and Ingestion: Stage 1 Implementation Plan

| Property | Value |
|---|---|
| Document ID | KOS-PLAN-STATUS-INGESTION-001 |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | APPROVED as a planning scope (D-077; confirmed by Dinesh, 2026-10-29, as stated in chat by Sangeetha) |
| Owner | Dinesh (program owner) |
| Reviewer / Approver | Dinesh |
| Version | 0.3 |
| Last Updated | 2026-10-29 |
| Authority | REFERENCE: it governs no baseline, weight, approval or gate |
| Related Tasks / Milestones | SI-01..SI-07 (planning identifiers only; not baseline tasks) |
| Related Documents | [ONBOARDING.md](../tracking/ONBOARDING.md), [ACCEPTANCE_STANDARD.md](ACCEPTANCE_STANDARD.md), [sources.json](../tracking/sources.json) |

## Purpose

Stage 1 gives the program a repeatable, validated way to ingest a workstream status report, using Sense as the first new source after Core and Community. Repository reports state facts; the central baseline alone decides credit. Stage 1 does not implement the Sense data contract, approve KOS-SENSE-001, create KOS-SENSE-002, or change any baseline task, weight, approval, gate or accepted progress.

## Scope

In scope: the Sense report at `status/status.json` in kritva-sense; the Sense entry in `v2/tracking/sources.json` and the repository name in `workstreams.json`; the Sense snapshot and manifest entry under `sources/`; consolidation; the operating procedure in [ONBOARDING.md](../tracking/ONBOARDING.md).

Out of scope: the Sense architecture and contract, baselining KOS-SENSE-001, further Sense tasks, automated reconciliation in CI, and a read-only token for scheduled live ingestion. Each needs separate planning and approval.

## Rules

1. A source entry with an empty `tasks` list is a statement that no approved task is reported yet. It earns no credit.
2. Existing CORE, COMMUNITY and CI_DEV_INFRA sources stay unchanged.
3. An ingestion, identity or ancestry error is reported as such and is never turned into an empty successful report.
4. The registration and the engineering report go through each repository's own pull-request process.
5. A green CI run is not task acceptance.

## Work items

| ID | Work item | Repository | Depends on | Exit condition | State |
|---|---|---|---|---|---|
| SI-01 | Confirm the Sense status PR is merged | kritva-sense | none | `status/status.json` on `main` (PR #8, merge commit `a700a1d`) | DONE (checked in a clone of `main`, 2026-10-28) |
| SI-02 | Validate the Sense report | kritva-sense | SI-01 | schema 2.0, `SENSE`, `KritvaOS/kritva-sense`, full 40-character SHA, `tasks: []` | DONE: checked by the consolidator on ingestion |
| SI-03 | Register the Sense source | kritva-program | SI-02 | `sources.json` entry, `workstreams.json` repo, example file | DONE (PR #7, merge commit `64f88bd`) |
| SI-04 | Refresh the source snapshot | kritva-program | SI-03 | `sources/SENSE.json` and its manifest entry | DONE: live refresh run by the owner, see Evidence |
| SI-05 | Run consolidation | kritva-program | SI-04 | `consolidate_status.py --sources-dir sources` passes | DONE: `--check` passes; the 248 program tests pass (see Evidence) |
| SI-06 | Audit the invariants | kritva-program | SI-05 | baseline, approvals, gates, weights and Core/Community data unchanged | DONE: see Evidence |
| SI-07 | Document the procedure | kritva-program | SI-01..SI-06 | [ONBOARDING.md](../tracking/ONBOARDING.md) updated | DONE (PR #7; the gap rule corrected in the follow-up) |

The SI identifiers are not baseline task IDs. They carry no weight and no credit.

## Acceptance criteria

| ID | Criterion | Evidence |
|---|---|---|
| AC-01 | Sense report merged into `main` | PR #8, merge commit `a700a1d` |
| AC-02 | Report conforms to schema 2.0 | accepted by the consolidator |
| AC-03 | Sense registered centrally | PR #7, merge commit `64f88bd` |
| AC-04 | Sense source fetched and validated | `sources/SENSE.json` identical to the Sense report; manifest entry FETCHED by a live refresh |
| AC-05 | Snapshot and manifest correct | fetched head `36ac1db`, report commit `2448708`, 4 commits ahead, gap OTHER_FILES; the changed files are `README.md`, `planning/CHANGELOG.md`, `planning/MILESTONE_STATUS.md` and `status/status.json`, all reviewed documentation or the report (kritva-sense PRs #8 and #9). See the gap rule below |
| AC-06 | Consolidation succeeds | command output |
| AC-07 | Sense reports no tasks | `tasks: []` |
| AC-08 | KOS-SENSE-001 stays outside the baseline | baseline file unchanged |
| AC-09 | Accepted progress and other workstreams unchanged | `baseline.json`, `approvals.json` and `gate_closures.json` are not in the PR #7 diff; the generated status changed only by the Sense source and one fewer warning |
| AC-10 | Failure handling and procedure documented | ONBOARDING.md |

## Gap rule

The manifest compares the report's own commit with the head that was fetched. A report can only name its parent commit, so any later commit leaves a gap. STATUS_ONLY (changes under `status/` only) and STATUS_TOOLING are accepted as they are. OTHER_FILES is accepted when each listed file is reviewed and is only documentation, a planning record or the status report; any other file, such as source code or a workflow, needs a reviewer to read the change and record the result here. The manifest value is never edited to fit a rule.

## Source reference policy

SENSE tracks `main` (a live source), like CORE and COMMUNITY. The committed copy under `sources/` and the manifest entry (fetched head, report commit, fetch time) are the reproducible record of each refresh. A source may instead be pinned to a commit or tag, and a pinned reference is advanced only by a reviewed change.

## Evidence and limits

- **Live refresh.** The owner ran `python3 tools/refresh_sources.py` with GitHub access on 2026-10-28 (PR #7 commit `bbfb874`). SENSE was FETCHED, 4 commits ahead, OTHER_FILES as above. Its snapshot is identical to `status/status.json` in kritva-sense.
- **CI_DEV_INFRA.** In the public repository its fetch fails: its report names a commit from the earlier private history, which is not an ancestor of the public history (see D-075). Its committed snapshot was not changed. This is not caused by Stage 1.
- **Consolidation.** `python3 tools/consolidate_status.py --sources-dir sources --check` passes and the program test suite passes.
- **Independent check.** An external review on 2026-10-29 confirmed the Sense and program commits, the identical report and snapshot, and no Sense task in the public baseline. It could not read the private program record.

## Open items

1. The private program record must carry the same Sense registration, and the result is then republished (D-075). Until then the public and private records differ.
2. KOS-SENSE-001 stays proposed. Its approval and central baselining are a separate decision (scope, owner and reviewer, weight, milestone, gates, evidence).

## Completion

Stage 1 is complete when every criterion has evidence and the change is reviewed and merged. Completion approves no Sense architecture, no release and no credit.
