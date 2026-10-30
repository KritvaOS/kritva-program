# KOS-SENSE-001 Approval and Baselining Plan

| Property | Value |
|---|---|
| Document ID | KOS-PLAN-SENSE-BASELINE-001 |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | APPROVED to proceed (D-078, 2026-10-30); baseline v3 frozen by pull request #13 (2026-10-30) |
| Owner | Dinesh (program owner) |
| Reviewer / Approver | Dinesh |
| Version | 0.3 |
| Last Updated | 2026-10-30 |
| Authority | REFERENCE: it governs no baseline, weight, approval or gate |
| Related Tasks / Milestones | KOS-SENSE-001, KOS-SENSE-002 (DRAFT), V2-M1-SENSE-001, V2-M2-SENSE-001 |
| Related Documents | [baseline_v3_proposal.json](../tracking/baseline_v3_proposal.json), [STATUS_INGESTION_PLAN.md](STATUS_INGESTION_PLAN.md), [ACCEPTANCE_STANDARD.md](ACCEPTANCE_STANDARD.md), [PENDING_DECISIONS.md](PENDING_DECISIONS.md) |

## Purpose

Describe how KOS-SENSE-001 (Sense architecture and data contract) and KOS-SENSE-002 (contract validation and synthetic-data tests) move from PROPOSED to approved, weighted baseline tasks. Decision D-078 approves both to proceed with initial weights 5 and 4. This plan still does not edit `baseline.json`, `approvals.json` or `gate_closures.json`: the baseline changes only through the owner-run freeze below, and no credit follows from approval.

## Current state (updated 2026-10-30)

Update: baseline v3 was frozen on 2026-10-30 (pull request #13; 33 tasks, total weight 113; the 30 effective approvals re-approved on v3 under D-027). The Sense source gap that now contains code and tests is an accepted exception (D-079). Since version 0.1: kritva-sense merged the KOS-SENSE-002 task row and criteria AC-201..AC-206, the draft contract 0.1.0 with its schema, and the reference validator with 31 synthetic fixtures and `make test-unit` (PRs #11, #12, #13). The statements below describe the state when the plan was first written; findings 1 and 2 are now resolved (see the outcome column).

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

| # | Decision | Recommendation | Outcome (D-078, 2026-10-30) |
|---|---|---|---|
| 1 | Approve KOS-SENSE-001 as a baseline task | Approve once criteria AC-001..AC-005 are accepted as written, or amended | Approved to proceed; criteria stay PROPOSED until reviewed |
| 2 | Weight for KOS-SENSE-001 | 5, with a rationale recorded in the proposal | 5, initial, revisable |
| 3 | Include KOS-SENSE-002 in this baseline | Only after its task row and criteria exist in kritva-sense | Included: the row and criteria are merged (PR #11) |
| 4 | Weight for KOS-SENSE-002 | 4 | 4, initial, revisable |
| 5 | Pin Core and Community contract versions in the criteria | Yes, or record "none required" with a reason | "None required": contract 0.1.0 has no normative dependency; recorded in the contract and criteria |
| 6 | Interim reviewer independence | Accept D-047 and record it | Accepted; still not independent review |
| 7 | PD-004, PD-005, PD-006 | Resolve PD-005 first; PD-004 and PD-006 before the v0.1.0 tag | Still open; they gate the tag and milestone closure, not the baseline entry |
| 8 | V2-M1 date | Leave unset until the owner states one | Unchanged: the V2-M1 date approved in D-076 applies; no new date |

## Step sequence

1. DONE. Sense repo: KOS-SENSE-002 task row and criteria, dependency statement, TASKS.md (PR #11, with audit fixes in #12 and the validator in #13).
2. This pull request. Program repo: decision D-078 in `v2/DECISIONS.md` and the updated plan and proposal. `PENDING_DECISIONS.md` is unchanged because PD-004, PD-005 and PD-006 stay open.
3. Owner-run freeze, in one commit:
   - add milestones `V2-M1-SENSE-001` and `V2-M2-SENSE-001` and the approved tasks to `baseline.json` with weights left null;
   - run the dry run, then the approved freeze (commands below);
   - re-approve the 30 effective approvals on v3 with `tools/record_approvals.py` (D-027, D-078); without this every approval is bound to v2 and accepted progress falls to 0;
   - first refresh the sources. The CORE and COMMUNITY reports must be inside the 14-day freshness window (the Community report is dated 2026-10-13), or the regenerated status drops their credit; refresh the Community report in kritvaos-community first;
   - update the test that hard-codes `101/104` to `101/113`;
   - commit the frozen `baseline.json`, regenerated baseline hash and any frozen outputs together.
4. Regenerate the Sense status snapshot and run consolidation. Credit stays zero until a task has passing evidence.
5. Implement KOS-SENSE-001 in kritva-sense through normal PRs. Closure needs the approved COMPLETION_RECORD.md and an annotated SemVer tag.

## Draft baseline entry

Source: [baseline_v3_proposal.json](../tracking/baseline_v3_proposal.json).

| Item | Value |
|---|---|
| Milestones | `V2-M1-SENSE-001`, `V2-M2-SENSE-001` |
| KOS-SENSE-001 | Sense architecture and data contract, weight 5 |
| KOS-SENSE-002 | Contract validation and synthetic-data tests, weight 4 (depends on KOS-SENSE-001) |
| Existing 31 tasks | weights and rationales unchanged |
| Total weight | 104 to 113 (33 tasks) |
| Baseline version | 2 to 3 |

The proposal must cover exactly the baseline tasks, so the two Sense tasks are added to `baseline.json` (weight left null) in the same owner-run step.

## Owner-run freeze procedure

Run from the repository root, by the owner only, after the pull request carrying D-078 is merged. The freeze is anchored to that merged commit (`--commit "$(git rev-parse HEAD)"`).

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
