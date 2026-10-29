# KOS-SENSE-001 Approval and Baselining Plan

| Property | Value |
|---|---|
| Document ID | KOS-PLAN-SENSE-BASELINE-001 |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | PROPOSED: not approved, not frozen |
| Owner | Dinesh (program owner) |
| Reviewer / Approver | Dinesh |
| Version | 0.1 |
| Last Updated | 2026-10-29 |
| Authority | REFERENCE: it governs no baseline, weight, approval or gate |
| Related Tasks / Milestones | KOS-SENSE-001, KOS-SENSE-002 (DRAFT), V2-M1-SENSE-001, V2-M2-SENSE-001 |
| Related Documents | [baseline_v3_proposal.json](../tracking/baseline_v3_proposal.json), [STATUS_INGESTION_PLAN.md](STATUS_INGESTION_PLAN.md), [ACCEPTANCE_STANDARD.md](ACCEPTANCE_STANDARD.md), [PENDING_DECISIONS.md](PENDING_DECISIONS.md) |

## Purpose

Describe how KOS-SENSE-001 (Sense architecture and data contract) moves from PROPOSED to an approved, weighted baseline task, and what the owner must decide first. This plan authorizes nothing. It does not edit `baseline.json`, `approvals.json` or `gate_closures.json`, and no credit follows from it.

## Current state

- kritva-sense is a planning-only repository. Its report (`status/status.json`, schema 2.0) lists no tasks and is ingested as a live source (D-077).
- `planning/TASKS.md` lists one task, KOS-SENSE-001 (NOT_STARTED, proposed, milestone V2-M1-SENSE-001). `ACCEPTANCE_CRITERIA.md` AC-001..AC-005 are PROPOSED.
- The baseline is version 2: 31 tasks, total weight 104. It contains no SENSE task or milestone.
- `v2/planning/milestones.json` already carries `V2-M1-SENSE-001` as PROPOSED with an empty task list.
- Test gates in kritva-sense exit 3 (NOT_IMPLEMENTED) until KOS-SENSE-002.

## Findings that affect the plan

1. KOS-SENSE-002 (contract validation and synthetic-data tests) has no task row or acceptance criteria in kritva-sense. It cannot be frozen until both exist. The draft proposal carries it, marked DRAFT, so the owner can see the weight impact, but freezing must wait for those files.
2. The criteria pin no versions of kritva-core or kritvaos-community. A task that depends on an unpinned contract is hard to close with evidence.
3. Architecture and safety review is held by the owner on an interim basis (D-047). The author and the approver are the same person until an independent reviewer exists.
4. PD-004 (task ID registry), PD-005 (acceptance and test policy) and PD-006 (tag policy) are PROPOSED. KOS-SENSE-001 closure depends on the acceptance standard and an annotated v0.1.0 tag.
5. Editing `baseline.json` alone breaks the hash check and leaves null weights. A scratch dry run confirmed the consolidator reports both errors. The amendment must be one owner-run step (below).

## Decisions needed from Dinesh, in order

| # | Decision | Recommendation |
|---|---|---|
| 1 | Approve KOS-SENSE-001 as a baseline task | Approve once criteria AC-001..AC-005 are accepted as written, or amended |
| 2 | Weight for KOS-SENSE-001 | 5, with a rationale recorded in the proposal |
| 3 | Include KOS-SENSE-002 in this baseline | Only after its task row and criteria exist in kritva-sense; otherwise baseline it in a later version |
| 4 | Weight for KOS-SENSE-002 | 4 (conditional on decision 3) |
| 5 | Pin Core and Community contract versions in the criteria | Yes, before approval, or record "none required" with a reason |
| 6 | Interim reviewer independence | Accept D-047 for KOS-SENSE-001 and record it in the decision entry |
| 7 | PD-004, PD-005, PD-006 | Resolve PD-005 first; PD-004 and PD-006 before the v0.1.0 tag |
| 8 | V2-M1 date | Leave unset until the owner states one; no date is invented |

## Step sequence

1. Sense repo, docs PR: add KOS-SENSE-002 task row and criteria, pin dependency versions, update TASKS.md. Dinesh merges.
2. Program repo, decision PR: record decisions 1 to 8 as one decision entry in `v2/DECISIONS.md` and update `PENDING_DECISIONS.md`.
3. Owner-run freeze, in one commit:
   - add milestones `V2-M1-SENSE-001` and `V2-M2-SENSE-001` and the approved tasks to `baseline.json` with weights left null;
   - run the dry run, then the approved freeze (commands below);
   - commit the frozen `baseline.json`, regenerated baseline hash and any frozen outputs together.
4. Regenerate the Sense status snapshot and run consolidation. Credit stays zero until a task has passing evidence.
5. Implement KOS-SENSE-001 in kritva-sense through normal PRs. Closure needs the approved COMPLETION_RECORD.md and an annotated SemVer tag.

## Draft baseline entry

Source: [baseline_v3_proposal.json](../tracking/baseline_v3_proposal.json).

| Item | Value |
|---|---|
| Milestones | `V2-M1-SENSE-001`, `V2-M2-SENSE-001` |
| KOS-SENSE-001 | Sense architecture and data contract, weight 5 |
| KOS-SENSE-002 | Contract validation and synthetic-data tests, weight 4 (DRAFT, conditional) |
| Existing 31 tasks | weights and rationales unchanged |
| Total weight | 104 to 113 (33 tasks); 109 if KOS-SENSE-002 is deferred |
| Baseline version | 2 to 3 |

If KOS-SENSE-002 is deferred, remove it from the proposal before the freeze; the proposal must cover exactly the baseline tasks.

## Owner-run freeze procedure

Run from the repository root, by the owner only. Do not run the second command until the decisions above are recorded.

```
python3 tools/freeze_baseline.py --root . --proposal v2/tracking/baseline_v3_proposal.json
python3 tools/freeze_baseline.py --root . --proposal v2/tracking/baseline_v3_proposal.json --approve
```

The first is a dry run that writes nothing. Check the stated task count, total weight and hash before approving.

## Invariants and verification

- No agent edits `baseline.json`, `approvals.json` or `gate_closures.json` without an owner decision.
- Credit comes only from approved baseline tasks with passing evidence; weights are never derived from effort claims in this plan.
- After the freeze: `python3 -m unittest discover -s tests` and `python3 tools/consolidate_status.py --sources-dir sources --check` pass.

## Risks

- Freezing KOS-SENSE-002 without criteria creates a weighted task that cannot be closed.
- The Community report is near the 14-day freshness limit, so regenerated status may drop its credit; refresh it first.
- Self-approval under D-047 is a known limitation, not independent review.
- The private program record also needs the SENSE registration (D-075) and, later, this amendment.

## What this plan does not authorize

Approval of KOS-SENSE-001 or KOS-SENSE-002, any weight, any baseline change, any gate closure, implementation of the Sense contract, hardware or safety claims, or a release tag.
