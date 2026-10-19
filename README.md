# kritva-program

> Program-level planning, governance and status reporting for the Kritva OS ecosystem: the decision log, the frozen baseline, approvals, release gates, risks, roadmap and the consolidated status view. This is a private repository.

| Property | Value |
|---|---|
| Project | KritvaOS |
| Repository | `KritvaOS/kritva-program` |
| Repository Type | Program governance |
| Visibility Class | PRIVATE (future private; D-037, D-039) |
| GitHub Setting | PUBLIC (verified 2026-10-18; temporary, D-028: owner action returns it to private) |
| Lifecycle Status | ACTIVE |
| Repository Owner | Dinesh (owner) |
| Security Owner | Dinesh ([SECURITY.md](SECURITY.md), D-032) |
| Architecture | [v2/SYSTEM_ARCHITECTURE.md](v2/SYSTEM_ARCHITECTURE.md) and [v2/PLATFORM_ARCHITECTURE.md](v2/PLATFORM_ARCHITECTURE.md) (both SKELETON: no architecture is asserted yet) |
| Milestones | [v2/planning/V2_MILESTONE_PLAN.md](v2/planning/V2_MILESTONE_PLAN.md) (PROPOSED targets, not approved delivery commitments) |
| Tasks | [v2/tracking/baseline.json](v2/tracking/baseline.json) (baselined) and [v2/tracking/planning_inventory.json](v2/tracking/planning_inventory.json) (planning only) |
| Acceptance Criteria | [v2/planning/ACCEPTANCE_STANDARD.md](v2/planning/ACCEPTANCE_STANDARD.md) (PROPOSED) |
| Status Reporting | [v2/tracking/STATUS_VIEW.md](v2/tracking/STATUS_VIEW.md) (generated snapshot) and [schema/status.schema.json](schema/status.schema.json) |
| License | [LICENSE](LICENSE) (proprietary, all rights reserved) |

This README follows the [Kritva README standard](v2/planning/standards/README_STANDARD.md) (D-055). It is the entry point; the documents it links own the detail.

## 1. Purpose and Scope

This repository records program-level truth. It owns the plan, the frozen baseline, approvals, gates, risks, decisions, committed snapshots of each repository's status, and the consolidated progress view.

It does **not** contain engineering source code, and it is not the authority for any repository's implementation, tests or releases. Those stay in the engineering repositories, which report facts to this one. Dinesh (owner and Security Owner) decides; advice from AI tools is advisory only.

## 2. Program Governance

| Topic | Rule | Where |
|---|---|---|
| Decision authority | The owner decides. The log is append-only: add a row or update a row's status and consequences with evidence; never rewrite a decision's meaning | [v2/DECISIONS.md](v2/DECISIONS.md) |
| Agent rules | What an agent may and may not change; status semantics; validation before a PR | [AGENTS.md](AGENTS.md) |
| Approvals | A repository can never accept its own work. Approvals are an append-only ledger | [v2/tracking/approvals.json](v2/tracking/approvals.json) |
| Code ownership | Single code owner; a second reviewer is a program decision (D-025) | [.github/CODEOWNERS](.github/CODEOWNERS) |
| Pending owner input | Open decisions and reviews, generated from structured records | [PENDING_DECISIONS.md](v2/planning/PENDING_DECISIONS.md), [PENDING_REVIEWS.md](v2/planning/PENDING_REVIEWS.md) |

## 3. KritvaOS Ecosystem Overview

The repositories of the program, for navigation. The roster, the dependency order, the approval roles and the required checks are owned by [repo-pipeline.json](v2/planning/repo-pipeline.json) (read by `scripts/pipeline/ship-prs.sh`), not by this table. kritva-program, kritva-raas and the kritva-actuator repositories are future private repositories and are written up as private. Each repository's visibility class and readiness are in [repo_readiness.json](v2/tracking/repo_readiness.json); the temporary public arrangement and its end are decided in D-028 and D-037, not restated here.

| Repository | Role |
|---|---|
| [kritva-program](https://github.com/KritvaOS/kritva-program) | This repository: plan, baseline, decisions, approvals, gates, source snapshots, consolidated reporting |
| [kritva-core](https://github.com/KritvaOS/kritva-core) | Kritva Core implementation and its engineering evidence (baselined) |
| [kritvaos-community](https://github.com/KritvaOS/kritvaos-community) | Community implementation, integration and evidence (baselined) |
| [kritva-motion](https://github.com/KritvaOS/kritva-motion), [kritva-sense](https://github.com/KritvaOS/kritva-sense), [kritva-mind](https://github.com/KritvaOS/kritva-mind), [kritva-skill](https://github.com/KritvaOS/kritva-skill) | Capability repositories: motion, perception, reasoning and skills (planning only; each runs the PR acceptance gate) |
| [kritva-raas](https://github.com/KritvaOS/kritva-raas) | Robotics-as-a-Service backend (planning only, not a baseline source) |
| [kritva-actuator](https://github.com/KritvaOS/kritva-actuator) | Parent actuator repository: shared interface, requirements and integration (planning only) |
| [kritva-actuator-embedded](https://github.com/KritvaOS/kritva-actuator-embedded) | Firmware and electronics for the actuator family (planning only; HOLD lifted by D-052) |
| [kritva-actuator-s](https://github.com/KritvaOS/kritva-actuator-s), [-m](https://github.com/KritvaOS/kritva-actuator-m), [-l](https://github.com/KritvaOS/kritva-actuator-l) | Mechanical design of the S, M and L variants (planning only; HOLD lifted by D-052) |

The generated view of that roster, with order, approval roles and required checks, is [V2_REPO_PLAN.md](v2/planning/V2_REPO_PLAN.md).

Two kinds of relationship are kept apart. An **implementation dependency** is one repository consuming another's code, artifact or interface. A **governance dependency** is a repository reporting status and evidence to this one under the program schema. A dependency that is not yet established is labelled PROPOSED or PLANNED in [DEPENDENCY_MAP](v2/DEPENDENCY_MAP.md).

## 4. Program Architecture

```text
  each repo: status/status.json (schema 2.0)       engineering repositories report facts
                    |
                    v
          sources/  (committed snapshots)           this repository stores copies, never edits them
                    |
                    v
   tools/consolidate_status.py  <---  baseline, approvals, gates     this repository owns credit
              |             |
              v             v
  consolidated_status.json   STATUS_VIEW.md (summary)   STATUS_DETAIL.md (full tables)
```

| Layer | Responsibility | Where |
|---|---|---|
| Program plan (DRAFT) | Goals, scope, phases, governance | [v2/PROGRAM_PLAN.md](v2/PROGRAM_PLAN.md) |
| System and platform architecture (SKELETON) | Component names only; relationships and interfaces are not documented yet | [SYSTEM_ARCHITECTURE](v2/SYSTEM_ARCHITECTURE.md), [PLATFORM_ARCHITECTURE](v2/PLATFORM_ARCHITECTURE.md), [PRODUCT_SCOPE](v2/PRODUCT_SCOPE.md) |
| Baseline and approvals | Approved tasks, weights and acceptance records | [v2/tracking/](v2/tracking/) |
| Evidence | Committed snapshots of repository status | [sources/](sources/) |
| Status computation | Validation and consolidated progress | [tools/](tools/) |
| Status presentation | Generated snapshots of the inputs above; they can lag them | [STATUS_VIEW.md](v2/tracking/STATUS_VIEW.md), [STATUS_DETAIL.md](v2/tracking/STATUS_DETAIL.md) |

Engineering repositories report implementation facts. This repository owns baseline credit and approvals. A repository edit never creates credit.

## 5. Planning Model and Milestones

| Concept | What it is | Where it lives |
|---|---|---|
| Phases P0-P8 | Frozen sequence: FOUNDATION, STUDIO, BUILD & ARTIFACT, CONTROL PLANE, BOOKING & COMMERCIAL, EXECUTION, LAB & ROBOT, LIVE & RESULTS, PRODUCTION | [v2/PROGRAM_PLAN.md](v2/PROGRAM_PLAN.md), [v2/ROADMAP.md](v2/ROADMAP.md) |
| Workstreams | Registered areas of work, each owned by a repository where one exists | [v2/tracking/workstreams.json](v2/tracking/workstreams.json) |
| Baseline | The approved, frozen set of tasks and weights that progress is measured against | [v2/tracking/baseline.json](v2/tracking/baseline.json), [baselines/](v2/tracking/baselines/) |
| Planning inventory | Tasks planned but not baselined (RaaS, actuators, capability repositories). Planning only: no weights, no credit | [v2/tracking/planning_inventory.json](v2/tracking/planning_inventory.json) |
| V2 milestone plan | Nine proposed phase milestones (V2-M0 to V2-M8) with per-repository milestones and proposed target dates. PROPOSED planning targets, not a committed delivery schedule; the start and horizon are owner answers recorded in D-044. A planning layer: no tasks, weights or credit, separate from the baseline | [v2/planning/V2_MILESTONE_PLAN.md](v2/planning/V2_MILESTONE_PLAN.md) |

Planning is not acceptance. Proposed milestones, newly drafted tasks, finished implementation and passing tests do not by themselves change the baseline or earn credit. Phase baseline dates are **not approved** ([ROADMAP](v2/ROADMAP.md)); the dates in the milestone plan are proposed targets and are not delivery commitments. Mechanical work is on HOLD (D-003); D-052 lifts it for the actuator workstreams, and the actuator local gates still apply.

## 6. Repository Structure and Responsibilities

| Path | Responsibility | Label | Edit by hand? |
|---|---|---|---|
| [README.md](README.md) | Entry point and navigation | REFERENCE | yes |
| [AGENTS.md](AGENTS.md) | Rules for agents working here | AUTHORITATIVE | owner decision |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting and secrets policy | AUTHORITATIVE | owner decision |
| [Makefile](Makefile) | Program helpers: `pr_check`, `ship`, `merge`, `readme_check` | INPUT | yes, with tests |
| [v2/](v2/) | Program documents: plan, scope, roadmap, gates, risks, decisions, reviews | MIXED: each document has its own label (section 7) | per document |
| [v2/tracking/](v2/tracking/) | Baseline, approvals, gate closures, effort, readiness (INPUT: the JSON files); the status view and `consolidated_status.json` (GENERATED) | MIXED: INPUT and GENERATED, per file | see section 17 |
| [v2/planning/](v2/planning/) | Repository pipeline, milestones and decision records (INPUT: the JSON files); V2_MILESTONE_PLAN, V2_REPO_PLAN, PENDING_* (GENERATED); ACCEPTANCE_STANDARD (AUTHORITATIVE, PROPOSED) and the README standard (AUTHORITATIVE, APPROVED, D-066) | MIXED: INPUT, GENERATED and AUTHORITATIVE, per file | see section 17 |
| [sources/](sources/) | Copies of each repository's `status/status.json`, provenance in `MANIFEST.json` | SNAPSHOT | no: refresh |
| [status/](status/) | This repository's own status report (workstream CI_DEV_INFRA) | INPUT | via its generator |
| [schema/](schema/) | `status.schema.json`, the status report schema (version 2.0) | AUTHORITATIVE | owner decision |
| [tools/](tools/) | Consolidator and planning helpers | INPUT | yes, with tests |
| [scripts/security/](scripts/security/) | Commit-message check used by CI; commit-format checker | INPUT | yes, with tests |
| [scripts/pipeline/](scripts/pipeline/) | `ship-prs.sh`, `manifest.py`, `pr_gate.py` (report-only PR gate, D-045), `pr_check.py` (D-046) | INPUT | yes, with tests |
| [scripts/docs/](scripts/docs/) | `check_readme.py`, the README standard check | INPUT | yes, with tests |
| [tests/](tests/) | Unit tests for the tools | EVIDENCE | extend with changes |
| [.github/](.github/) | Workflows (`commit-message-check`, `readme-check`, `refresh-sources`, `secret-scan`, `status`), PR template and CODEOWNERS | AUTHORITATIVE | owner review |

## 7. Program-of-Record Documents

| Document | Label, status | What it answers |
|---|---|---|
| [v2/README.md](v2/README.md) | REFERENCE | Program dashboard and planning document index (not an alternative source of architecture) |
| [v2/PROGRAM_PLAN.md](v2/PROGRAM_PLAN.md) | AUTHORITATIVE, DRAFT | Scope, phases, operating model |
| [v2/ROADMAP.md](v2/ROADMAP.md) | AUTHORITATIVE; phase dates not approved | Phase order and forecast rules |
| [v2/DECISIONS.md](v2/DECISIONS.md) | AUTHORITATIVE, append-only | What was decided and why (D-001 onward) |
| [v2/tracking/baseline.json](v2/tracking/baseline.json) | INPUT, frozen baseline | Approved tasks and weights |
| [v2/tracking/approvals.json](v2/tracking/approvals.json) | EVIDENCE, append-only | Review and acceptance records |
| [v2/GATE_REGISTER.md](v2/GATE_REGISTER.md) | AUTHORITATIVE | Gates, entry and exit criteria, required evidence |
| [v2/planning/ACCEPTANCE_STANDARD.md](v2/planning/ACCEPTANCE_STANDARD.md) | AUTHORITATIVE role, PROPOSED | Definition of done, test gates, commit format, tags. Section 4 (commit text) is enforced in this repository (D-053); the standard is not approved for all repositories (PD-019) |
| [v2/REPOSITORY_BASELINE.md](v2/REPOSITORY_BASELINE.md) | REFERENCE | Reconciliation of repositories against evidence |
| [v2/REQUIREMENT_TRACEABILITY.md](v2/REQUIREMENT_TRACEABILITY.md) | REFERENCE | Requirement to task traceability |
| [v2/tracking/ONBOARDING.md](v2/tracking/ONBOARDING.md) | REFERENCE | How a repository starts reporting |

## 8. Workstream Dependencies and Critical Path

[v2/DEPENDENCY_MAP.md](v2/DEPENDENCY_MAP.md) lists provider and consumer relationships and [v2/CRITICAL_PATH.md](v2/CRITICAL_PATH.md) the chain that controls sequencing. The PR order of the repositories is in [V2_REPO_PLAN.md](v2/planning/V2_REPO_PLAN.md).

## 9. Status Reporting and Consolidation

1. **Repositories report facts.** Each repository's generator writes `status/status.json` (schema 2.0): per task, `execution`, `git_sync`, `readiness` and `evidence`. A report carries facts only: it never contains review, acceptance, approval or program credit. [v2/tracking/ONBOARDING.md](v2/tracking/ONBOARDING.md) describes how a repository joins.
2. **Snapshots.** The `refresh-sources` workflow proposes daily pull requests that update `sources/` from each repository; a human reviews and merges.
3. **Consolidation.** `tools/consolidate_status.py` validates every report against the baseline and approvals and computes progress. Stale, missing or unverified inputs earn no credit and are never silently passed.
4. **Generated views.** [STATUS_VIEW.md](v2/tracking/STATUS_VIEW.md) is the short summary (owner actions and blockers, changes since the last snapshot, the three measures, progress by workstream, readiness, dated milestones, data quality). [STATUS_DETAIL.md](v2/tracking/STATUS_DETAIL.md) holds the full tables.

A workstream's existence, or a task in the planning inventory, does not put it in the weighted baseline. Only tasks admitted through the baseline governance process (a decision and a baseline amendment) affect accepted progress.

Read the current numbers in the generated views. They are not copied here, and the views are derived snapshots: they can lag their inputs and they print their own warnings and freshness gaps.

## 10. Acceptance, Evidence and Approval

Four things are kept apart and never merged into one flag: **reported execution** (a repository says the work is done), **evidence** (commit and CI records, with their scope), **accepted progress** (an approval in the ledger) and **release readiness** (the gates). Code written, a commit, a merged PR, a passing local test or a status file saying PASS is not acceptance.

| Measure | Definition | Source |
|---|---|---|
| Accepted engineering progress | Accepted weight over baseline weight of the frozen baseline. Credit needs an approval and CI evidence under the program's evidence rule | baseline, approvals, status reports |
| Estimated effort | Owner-estimated person-months done and remaining. Not timesheets, not progress, not a schedule | [effort_estimates.json](v2/tracking/effort_estimates.json) |
| Capability completion | Owner estimate of delivered scope per workstream; no formal inventory yet | effort estimates |

None of these is a delivery date and they are not averaged into a health figure. Before reading a task as verified, read its evidence scope and commit in [STATUS_DETAIL.md](v2/tracking/STATUS_DETAIL.md): some evidence is a milestone-level run on a later commit, not a run on the task's own commit.

[v2/tracking/repo_readiness.json](v2/tracking/repo_readiness.json) holds a per-repository checklist for the return to private (D-037, D-039). It is display only and adds no credit. A check is READY only when PASS, ATTESTED (owner-stated, not verified) or NA. GitHub settings such as rulesets cannot be read by tooling, so they stay ATTESTED.

## 11. Gates, Risks and Decisions

Open safety and release gates give zero credit to the tasks in their scope: [GATE_REGISTER.md](v2/GATE_REGISTER.md) and [gate_closures.json](v2/tracking/gate_closures.json). Risks: [RISK_REGISTER.md](v2/RISK_REGISTER.md). Decisions: [DECISIONS.md](v2/DECISIONS.md). Independent reviews: [v2/reviews/](v2/reviews/).

## 12. Toolchain and Development Workflow

| Tool | Purpose | Check |
|---|---|---|
| Python 3 (standard library only) | Tools, tests and pipeline scripts | `python3 --version` |
| GitHub CLI `gh`, signed in | `pr_check`, `ship`, `merge` | `gh auth status` |
| GNU make | Front end for the helpers | `make help` |

Change an input (baseline, approvals, gates, sources, effort, readiness, planning inventory, v2/planning records), regenerate, and commit the generated files in the same pull request.

> **Privileged commands.** `make pr_check` submits an approving review as the signed-in `gh` user unless you add `DRY=1`. `make ship` and `make merge` merge pull requests with `--admin` and sync your local `main`. Run `DRY=1` first and check the repository and PR number. `generate` commands write files locally; `check` commands only read.

```bash
python3 tools/consolidate_status.py --sources-dir sources            # generate: regenerate JSON, STATUS_VIEW.md and STATUS_DETAIL.md
make pr_check all DRY=1                                              # check: report only, no review is submitted
make pr_check all                                                    # sweep the REPOS list in the Makefile; approves the clear ones (DRY=1 to only report)
make pr_check REPO=kritva-sense PR=7                                 # one PR
make ship TAR=~/Downloads/x.tar.gz BRANCH=feat/x                     # ship a patch tarball: PR, checks, merge, sync (DRY=1 to preview)
make merge REPO=kritva-sense PR=7                                    # merge a PR you pushed yourself (checks, gate, --admin, sync)
```

`make ship` opens the PR, waits for the required checks and merges in one run. Use `make merge` only for a PR you opened by hand or one that `ship` left open.

## 13. Validation and Regression

| Check | Command | Runs in CI? |
|---|---|---|
| Unit tests | `python3 -m unittest discover -s tests` | yes (`status`) |
| Generated status is current | `python3 tools/consolidate_status.py --sources-dir sources --check` | yes (`status`) |
| Planning inventory rules | `python3 tools/check_planning_inventory.py .` | yes (`status`) |
| V2 planning records and generated views | `python3 tools/planning.py --check` (also covered by `consolidate_status --check`) | yes (`status`) |
| PR pipeline manifest | `python3 scripts/pipeline/manifest.py validate` | no, run locally |
| README standard | `make readme_check` (the workflow runs the checker's tests and the same check) | yes (`readme-check`; not a required check yet, D-067) |
| Commit text | `python3 scripts/security/check_commit_messages.py` and `check_commit_format.py` | yes (`commit-message-check`) |
| Secrets | `secret-scan` workflow | yes |

Regression tests live in [tests/](tests/); a defect fixed in a tool gets a test there. This repository has no hardware, so there is no hardware validation. A check that is not run in CI is listed as such.

## 14. Git Workflow and Change Control

- Changes go through a pull request. Required checks and approval roles are in [V2_REPO_PLAN.md](v2/planning/V2_REPO_PLAN.md).
- **Commit text** (adopted and enforced in this repository, D-053; kritva-core and kritvaos-community adopted it under D-061, the other repositories adopt it one by one, PD-019; [ACCEPTANCE_STANDARD](v2/planning/ACCEPTANCE_STANDARD.md) section 4 is PROPOSED): header `type(scope): summary [optional TASK-ID]` of at most 90 characters; types feat, fix, docs, refactor, test, build, ci, chore, perf, revert, security; then one footer line `Task: ID` or `Tasks: ID, ID`; `Tasks: None (reason)` only on docs or chore commits. AI session trailers and claude.ai session links are rejected.
- **Merge method:** merge commit (D-053).
- **Releases:** annotated SemVer tags created only after the approved merge. A tag is evidence, not milestone closure.
- **PR text:** [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md).
- Never edit `baseline.json`, `approvals.json`, `gate_closures.json` or the generated status files by hand. See [AGENTS.md](AGENTS.md) and [SECURITY.md](SECURITY.md).

## 15. Security and Safety

- Vulnerabilities: report to the Security Owner as described in [SECURITY.md](SECURITY.md); its private reporting route is not yet verified, and it says so. Do not put details of an unfixed vulnerability in an issue, PR or commit.
- Secrets: never commit credentials, tokens, private keys or production data, public or private. The `secret-scan` workflow runs on every PR.
- This repository holds no hardware and runs no actuators. Safety is tracked here as gates: an open safety gate gives zero credit to its tasks (section 11), and software tests or simulation never close a physical safety gate. Mechanical HOLD (D-003) and its lift for the actuator workstreams (D-052) are decisions in the log.

## 16. Release and Versioning

This repository is not released as a product. Program baselines are frozen versions under [v2/tracking/baselines/](v2/tracking/baselines/), recorded by decision. Engineering repositories release with annotated SemVer tags created after the approved merge (D-044); a tag is evidence, not milestone closure. Compatibility between repositories is tracked in [DEPENDENCY_MAP](v2/DEPENDENCY_MAP.md).

## 17. Generated Reports and Data Integrity

| File | Label | Generated by | Change it by |
|---|---|---|---|
| [consolidated_status.json](v2/tracking/consolidated_status.json), [STATUS_VIEW.md](v2/tracking/STATUS_VIEW.md), [STATUS_DETAIL.md](v2/tracking/STATUS_DETAIL.md) | GENERATED | `tools/consolidate_status.py` | editing the inputs, then regenerating |
| [V2_MILESTONE_PLAN.md](v2/planning/V2_MILESTONE_PLAN.md), [V2_REPO_PLAN.md](v2/planning/V2_REPO_PLAN.md), [PENDING_DECISIONS.md](v2/planning/PENDING_DECISIONS.md), [PENDING_REVIEWS.md](v2/planning/PENDING_REVIEWS.md) | GENERATED | `tools/planning.py` from `v2/planning/*.json` | editing the JSON, then regenerating |
| [sources/](sources/) | SNAPSHOT | the `refresh-sources` workflow | refreshing from the source repository |

Editing a generated view is not changing the baseline, and editing a snapshot is not new evidence from the engineering repository.

## 18. Related Repositories

See section 3 for the list and [DEPENDENCY_MAP](v2/DEPENDENCY_MAP.md) for the relationships. Each engineering repository's README links its own architecture, milestones, tasks and acceptance documents, and follows the same [README standard](v2/planning/standards/README_STANDARD.md). The rollout order is in [README_MIGRATION_PLAN.md](v2/planning/standards/README_MIGRATION_PLAN.md).

## 19. Document Index

- Start here: [v2/README.md](v2/README.md) (dashboard and document index), [STATUS_VIEW.md](v2/tracking/STATUS_VIEW.md) (generated summary), [DECISIONS.md](v2/DECISIONS.md).
- Plans: [PROGRAM_PLAN](v2/PROGRAM_PLAN.md), [ROADMAP](v2/ROADMAP.md), [V2_MILESTONE_PLAN](v2/planning/V2_MILESTONE_PLAN.md), [V2_REPO_PLAN](v2/planning/V2_REPO_PLAN.md).
- Rules: [ACCEPTANCE_STANDARD](v2/planning/ACCEPTANCE_STANDARD.md), [AGENTS](AGENTS.md), [SECURITY](SECURITY.md).
- README rollout standards (one package): [README_STANDARD](v2/planning/standards/README_STANDARD.md), [README_TEMPLATE_PUBLIC](v2/planning/standards/README_TEMPLATE_PUBLIC.md), [README_TEMPLATE_PRIVATE](v2/planning/standards/README_TEMPLATE_PRIVATE.md), [DOCUMENT_HEADER_STANDARD](v2/planning/standards/DOCUMENT_HEADER_STANDARD.md), [README_REVIEW_CHECKLIST](v2/planning/standards/README_REVIEW_CHECKLIST.md), [README_MIGRATION_PLAN](v2/planning/standards/README_MIGRATION_PLAN.md).
- Other templates: [PR template](v2/planning/templates/PULL_REQUEST_TEMPLATE.md), [acceptance criteria](v2/planning/templates/ACCEPTANCE_CRITERIA.template.md), [completion record](v2/planning/templates/COMPLETION_RECORD.template.md).

## 20. License

Proprietary and confidential. Copyright (c) 2026 Kritvaos. All rights reserved. See [LICENSE](LICENSE).
