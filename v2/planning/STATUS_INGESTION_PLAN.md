# Status Reporting and Ingestion: Stage 1 Implementation Plan

| Property | Value |
|---|---|
| Document ID | KOS-PLAN-STATUS-INGESTION-001 |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | APPROVED as a planning scope (D-077; approval relayed in chat, owner confirmation of record pending) |
| Owner | Dinesh (program owner) |
| Reviewer / Approver | Dinesh |
| Version | 0.2 |
| Last Updated | 2026-10-28 |
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
| SI-03 | Register the Sense source | kritva-program | SI-02 | `sources.json` entry, `workstreams.json` repo, example file | IN REVIEW (this change) |
| SI-04 | Refresh the source snapshot | kritva-program | SI-03 | `sources/SENSE.json` and its manifest entry | DONE with a limit, see Evidence |
| SI-05 | Run consolidation | kritva-program | SI-04 | `consolidate_status.py --sources-dir sources` passes | See Evidence |
| SI-06 | Audit the invariants | kritva-program | SI-05 | baseline, approvals, gates, weights and Core/Community data unchanged | See Evidence |
| SI-07 | Document the procedure | kritva-program | SI-01..SI-06 | [ONBOARDING.md](../tracking/ONBOARDING.md) updated | IN REVIEW (this change) |

The SI identifiers are not baseline task IDs. They carry no weight and no credit.

## Acceptance criteria

| ID | Criterion | Evidence |
|---|---|---|
| AC-01 | Sense report merged into `main` | PR #8, merge commit `a700a1d` |
| AC-02 | Report conforms to schema 2.0 | accepted by the consolidator |
| AC-03 | Sense registered centrally | the merged version of this change |
| AC-04 | Sense source fetched and validated | `sources/SENSE.json`, `sources/MANIFEST.json` |
| AC-05 | Snapshot and manifest correct | STATUS_ONLY gap, two commits ahead, one changed file |
| AC-06 | Consolidation succeeds | command output |
| AC-07 | Sense reports no tasks | `tasks: []` |
| AC-08 | KOS-SENSE-001 stays outside the baseline | baseline file unchanged |
| AC-09 | Accepted progress and other workstreams unchanged | before-and-after diff of generated files |
| AC-10 | Failure handling and procedure documented | ONBOARDING.md |

## Evidence and limits

The sandbox that prepared this change cannot call the GitHub API, so `tools/refresh_sources.py` could not fetch live. It was run for the Sense entry only, with its API calls answered from a clone of `KritvaOS/kritva-sense` at `a700a1d`. The fetched head, ahead count and changed-file list come from that clone's git history. The owner should rerun `python3 tools/refresh_sources.py` with GitHub access before merging; only the fetch time should differ. Until then AC-04 and AC-05 are not independently verified.

## Completion

Stage 1 is complete when every criterion has evidence and the change is reviewed and merged. Completion approves no Sense architecture, no release and no credit.
