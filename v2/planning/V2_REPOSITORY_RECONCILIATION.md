# V2 Repository Reconciliation

| Property | Value |
|---|---|
| Document ID | KOS-PLAN-REPO-RECONCILIATION-001 |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan (hand-written, not generated) |
| Status | DRAFT, pending owner review |
| Owner | Dinesh (program owner) |
| Reviewer / Approver | Dinesh |
| Version | 0.1 |
| Last Updated | 2026-11-01 |

## 1. Purpose and authority

This document reconciles the participating repositories with the V2 program milestones (V2-M0 to V2-M8) and lists what is still open. It is a reading aid for the owner. It does not approve anything, add credit, change a weight or close a milestone.

- It holds no counts, weights or percentages. Task counts, baselined weight, accepted weight and closure state per milestone are in the generated Milestone alignment section of [tracking/STATUS_DETAIL.md](../tracking/STATUS_DETAIL.md). If a number here ever disagrees with that file, that file is right.
- Authority follows D-011. Repositories report facts. The program decides baseline task IDs, weights and credit. A milestone closes only through an approved `COMPLETION_RECORD.md` (ACCEPTANCE_STANDARD section 2). A merge, a CI run or a tag does not close one.
- The milestone alignment rules are D-093 (the join lives in `consolidate_status.py`, `planning.py` stays isolated, repo milestone `tasks` stays empty), D-094 (historical milestones are PRE_V2 by default, no weight or credit transfer), D-095 (optional `historical_milestones` section) and D-096 (`depends_on` stays at program level). Those four rows are marked "Approved (conveyed; owner confirmation pending)" until the owner confirms them in the pull request.
- Decision authority is the owner. Everything under "Open owner decisions" is a question, not a recommendation.

## 2. How to read the repository records

| Question | Where the answer lives |
|---|---|
| Which repositories exist, their kind, their dependencies, whether they are baselined or on hold | `v2/planning/repo-pipeline.json` (rendered in [V2_REPO_PLAN.md](V2_REPO_PLAN.md)) |
| Which workstream a repository or task belongs to | `v2/tracking/workstreams.json` (D-009) |
| Which program milestone a repository milestone serves | `v2/planning/milestones.json`, field `repo_milestones[].milestone_id` (rendered in [V2_MILESTONE_PLAN.md](V2_MILESTONE_PLAN.md)) |
| Which baselined task sits in which milestone | `v2/tracking/baseline.json`, joined by `consolidate_status.py` |
| Whether a task has credit, and a milestone has a closure record | [tracking/STATUS_DETAIL.md](../tracking/STATUS_DETAIL.md) |

A repository milestone ID has the form `V2-M<n>-<REPO>-<seq>`. It encodes its program milestone, so the mapping is one to one. A cross-milestone dependency is expressed at program level only (D-096).

## 3. Repository matrix

Source: `repo-pipeline.json` and `milestones.json` as of the date above. "Planned repository milestones" lists the program milestones for which a PROPOSED repository milestone exists. It says nothing about whether work has started.

| Code | Workstream | GitHub repository | Kind | Planned repository milestones | Baselined | On hold | Notes |
|---|---|---|---|---|---|---|---|
| PROGRAM | CI_DEV_INFRA | KritvaOS/kritva-program | program | V2-M0, V2-M8 | yes | no | Control plane for governance. Its historical milestone is KRP-ENG. |
| CORE | CORE | KritvaOS/kritva-core | library | V2-M0, V2-M2, V2-M8 | yes | no | Historical milestone KF-CORE-R10 (Core R1.0). No planned milestone in V2-M1, V2-M3, V2-M5 or V2-M7. |
| COMMUNITY | COMMUNITY | KritvaOS/kritvaos-community | library | V2-M0, V2-M1, V2-M3, V2-M7, V2-M8 | yes | no | Historical milestones KOS-I2, KOS-I3, KOS-I4. |
| SENSE | SENSE | KritvaOS/kritva-sense | capability | V2-M0, V2-M1, V2-M2, V2-M5, V2-M7, V2-M8 | no (partly baselined through V2-M1/M2/M5/M7/M8-SENSE-001) | no | Only repository whose baselined tasks roll up to V2 milestones today. |
| MOTION | MOTION | KritvaOS/kritva-motion | capability | V2-M0, V2-M1, V2-M2, V2-M5, V2-M8 | no | no | See gap G-08 (workstream record has no repository). |
| MIND | MIND | KritvaOS/kritva-mind | capability | V2-M0, V2-M1, V2-M2, V2-M5, V2-M8 | no | no | See gap G-08. |
| SKILL | SKILL | KritvaOS/kritva-skill | capability | V2-M0, V2-M1, V2-M2, V2-M3, V2-M5, V2-M8 | no | no | See gap G-08. |
| ACTUATOR | ACT_INT | KritvaOS/kritva-actuator | hardware-interface | V2-M5, V2-M6 | no | no | See gap G-06. |
| EMBEDDED | ACT_EMB | KritvaOS/kritva-actuator-embedded | firmware | V2-M6 | no | yes | Planned milestone is under the V2-M6 HOLD. |
| ACTS | ACT_S | KritvaOS/kritva-actuator-s | mechanical | V2-M6 | no | yes | Same. |
| ACTM | ACT_M | KritvaOS/kritva-actuator-m | mechanical | V2-M6 | no | yes | Same. |
| ACTL | ACT_L | KritvaOS/kritva-actuator-l | mechanical | V2-M6 | no | yes | Same. |

Not verified here: the state of any repository other than what the program records report. This document was written from `kritva-program` only. The current state of each repository is whatever its status source says in STATUS_DETAIL. A workstream with no status source is UNVERIFIED, not zero.

## 4. Historical baseline milestones

Five baseline milestones predate the V2 milestone plan and have no program milestone. Under D-094 they are PRE_V2 and recorded in `milestones.json` under `historical_milestones` (D-095).

| Baseline milestone | Repository | Classification | Related program milestone | Credit transfer |
|---|---|---|---|---|
| KF-CORE-R10 | CORE (kritva-core) | PRE_V2 | none | no |
| KOS-I2 | COMMUNITY (kritvaos-community) | PRE_V2 | none | no |
| KOS-I3 | COMMUNITY | PRE_V2 | none | no |
| KOS-I4 | COMMUNITY | PRE_V2 | none | no |
| KRP-ENG | PROGRAM (kritva-program) | PRE_V2 | none | no |

Consequences, stated once:

- Their weight stays where it is in the baseline. It is not part of V2-M0 or any other V2 milestone, and no V2 milestone closes by reference to it.
- If the owner later decides that one of them is accepted foundation work that a V2 milestone depends on, the change is to classify it `V2_FOUNDATION` with a related program milestone in `milestones.json`. `baseline.json` stays untouched.
- The consolidator reports any historical baseline milestone that is not classified as UNCLASSIFIED, and any V2-prefixed baseline milestone missing from `repo_milestones` as an error.

## 5. Gap register

Each gap is a statement about the records, with the action that closes it and who decides. Closing a gap that edits a program record needs the owner's instruction.

| ID | Gap | Evidence | Closes with | Decides |
|---|---|---|---|---|
| G-01 | V2-M4 (booking, credits, commercial flows) has no repository milestone. | No `repo_milestones` entry with `milestone_id` V2-M4. | Name the owning repository or workstream, then add a PROPOSED repository milestone. | Owner |
| G-02 | V2-M3 has repository milestones for Skill and Community only. The Control Plane has none. | CONTROL_PLANE workstream has no repository and no pipeline entry. | PD-003 (where Control Plane lives), then a PROPOSED milestone for it. | Owner (PD-003) |
| G-03 | Sim, SDK and Studio have workstreams but no repository, no pipeline entry and no milestone. | SIM, SDK, STUDIO have `repo: null` in `workstreams.json`. | PD-003. Until it is decided, no pipeline entry is created. | Owner (PD-003) |
| G-04 | Nexus and Edge board work is one workstream with no repository and no pipeline entry. | NEXUS_EDGE has `repo: null`. | Decide whether it splits into separate Nexus and Edge workstreams and whether each has a repository. Do not guess a repository name. | Owner |
| G-05 | Core has planned milestones in V2-M0, V2-M2 and V2-M8 only. | `repo_milestones` for CORE. | Confirm that Core has nothing to deliver in the other program milestones, or add PROPOSED milestones. | Owner |
| G-06 | The actuator interface repository has a V2-M5 milestone while every actuator repository milestone in V2-M6 is on hold. | `repo-pipeline.json` phase_milestones for ACTUATOR and the HOLD flags on the other four. | PD-002 and the D-052 confirmation (see G-07). | Owner (PD-002) |
| G-07 | The central record disagrees with itself about the actuator HOLD. D-052 lifted the D-003 HOLD for the actuator repositories (owner confirmation pending), while `MECHANICAL` still has `hold: true`, V2-M6 reads "mechanical scope is not reopened (D-003)" and has no date, and PD-002 is open. | `decisions.json`, `workstreams.json`, `milestones.json`. | Owner confirms D-052, then decides whether the MECHANICAL hold and the V2-M6 wording change. No V2-M6 date unless the owner approves one. | Owner (PD-002) |
| G-08 | `workstreams.json` records no repository for MOTION, SKILL and MIND, while `repo-pipeline.json` registers kritva-motion, kritva-skill and kritva-mind. | The two registries differ on these three workstreams. | PD-014 (register the repositories on their workstreams). Recording a repository changes a program record, so it needs the owner's approval. | Owner (PD-014) |
| G-09 | The program source report for Core (`sources/CORE.json`) may still hold the earlier report. The Core status report was regenerated from a clean checkout in kritva-core. | `sources/` is protected. | The refresh-sources workflow, or an owner-approved change. | Owner |
| G-10 | The effort figure used as a planning reference has no recorded breakdown under `v2/`. | No source file for it. | Locate or re-derive the breakdown before it enters any effort register. Effort stays separate from weights. | Owner |
| G-11 | Review records REV-001 to REV-007 have no reviewer. | PENDING_REVIEWS.md. | Assign reviewers. | Owner |

## 6. Open owner decisions

These are the decisions the gaps wait on. IDs in the first column are existing pending decisions where they exist. The others are not yet numbered. Each receives the next free `D-0xx` ID when the owner records it, checked against `v2/DECISIONS.md` at that time.

| Reference | Decision needed | Options | Unblocks |
|---|---|---|---|
| PD-002 | Reopening criteria for V2-M6 and confirmation of D-052 | Confirm D-052 only / confirm and define reopening criteria | G-06, G-07 |
| PD-003 | Where Sim, SDK, Studio and Control Plane live | Per component: own repository, inside another repository, planned | G-02, G-03 |
| PD-014 | Register the MOTION, SKILL and MIND repositories on their workstreams | Approve as the pipeline records them / amend | G-08 |
| Not yet numbered | Nexus and Edge ownership | Split inside an existing repository / split with new repositories / keep one workstream | G-04 |
| Not yet numbered | Owner of V2-M4 | Name a repository or workstream | G-01 |
| Not yet numbered | V2 program boundary: kritva-raas, manufacturing and fleet operations are outside kritva-program V2 and belong to the enterprise program | Approve as stated / approve with a shared-dependency list | Boundary text in the plans |
| Not yet numbered | Custom Nexus and Edge SoC work (FPGA or ASIC) is outside V2 | Approve / defer | Effort policy |
| Not yet numbered | Effort register policy (effort unit separate from weights, source of the planning figure) | Re-derive from per-task effort / adopt with the original breakdown / drop | G-10 |

## 7. What this document does not do

- It does not create or change a registry, a milestone, a task or an approval.
- It does not state progress. Progress, credit and closure are in STATUS_DETAIL.
- It does not replace `V2_MILESTONE_PLAN.md` or `V2_REPO_PLAN.md`, which are generated from the JSON records and must not be edited by hand.

## 8. Maintenance

Update this file by hand when a gap closes or a decision is recorded, and keep the decision references current. When a decision creates a record (a new repository, a new milestone), the record is added through its own pull request and this file then points at it. Keep numbers out. If a figure is needed, link to STATUS_DETAIL.
