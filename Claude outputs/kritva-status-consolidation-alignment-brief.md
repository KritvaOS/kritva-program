# Kritva Program: Status & Tracking Consolidation — Alignment Brief

Purpose: paste this into ChatGPT (the tool that produced the original v2 planning baseline) so both assistants work from the same model. Claude cannot talk to ChatGPT directly, so this brief carries the context. Ask ChatGPT to confirm, critique, or correct the proposal in section 4 and answer the questions in section 5.

## 1. Current state (as of 2026-10-09, repo `KritvaOS/kritva-program`, private, branch `main`)

- Umbrella repo for program management only. No engineering source code. Engineering repos (Core, Community, etc.) stay authoritative for code, tests and releases.
- Layout: `README.md`, `v2/` (dashboard, 16 planning docs, `tracking/STATUS.md`, `milestones/P0/P0-M01-PROVISIONAL`, `milestones/P1/P1-M01-PROVISIONAL`).
- Frozen phases: P0 FOUNDATION, P1 STUDIO, P2 BUILD & ARTIFACT, P3 CONTROL PLANE, P4 BOOKING & COMMERCIAL, P5 EXECUTION, P6 LAB & ROBOT, P7 LIVE & RESULTS, P8 PRODUCTION.
- Status model (PROGRAM_PLAN §6): five separate dimensions per item. Execution (NOT_STARTED / IN_PROGRESS / BLOCKED / COMPLETE), Review, Acceptance (NOT_RUN / PASS / FAIL / WAIVED), Git sync, Readiness (PLANNABLE / IMPLEMENTABLE / HARDWARE-BLOCKED). Progress is `accepted weight / total baseline weight`. Schedule (baseline, forecast, variance, trend) and effort (evidence-backed only) are tracked separately.
- Real status today: P0 IN_PROGRESS, 0% accepted, no dates approved, mechanical HOLD, repo reconciliation not done (all Core/Community facts UNVERIFIED), git sync NOT_COMMITTED, milestone IDs still placeholders (D-007).

## 2. The problem

Status facts are spread across several hand-edited markdown tables, and several of them restate the same facts:

| Fact | Where it currently appears |
|---|---|
| Current phase, health, accepted %, HOLD | `v2/README.md` snapshot AND `tracking/STATUS.md` summary |
| Per-phase execution/review/acceptance | `tracking/STATUS.md` phase table AND `ROADMAP.md` "State" column |
| Per-workstream status | `WORKSTREAM_STATUS.md` (14 rows, mostly TBD) |
| Gate pass/fail | `GATE_REGISTER.md` (plus P0 `COMPLETION_RECORD.md`) |
| Risk status | `RISK_REGISTER.md` |
| Task-level status | `milestones/*/TASKS.md` and `ACCEPTANCE_CRITERIA.md` |

The README itself says "do not duplicate status numbers here", but the dashboard already carries a snapshot. Manual sync across these files will drift, and the repo's own rule ("one document, one responsibility; link instead of copying") will be broken the first time a task is accepted.

## 3. Constraints to preserve

1. Evidence-backed: a commit is not acceptance. Every PASS must link to evidence.
2. Frozen phase names; no renaming or renumbering.
3. Scope changes keep the prior baseline so progress cannot improve by deleting tasks.
4. Software acceptance (sim/mocks) is never represented as physical or safety validation.
5. No empty future plans; P2–P8 folders are created on demand.
6. Mechanical work stays on HOLD; engineering repos stay authoritative.

## 4. Proposed consolidation (for ChatGPT to confirm or critique)

**A. One machine-readable source of truth** for status data: `v2/tracking/status.yaml` (or per-milestone `status.yaml`, rolled up). Records:
- `tasks[]`: id, milestone, phase, title, baseline_weight, execution, review, acceptance, git_sync, readiness, evidence[] (repo, commit/tag/test link, evidence_type = software | simulation | physical), owner.
- `milestones[]`: id, phase, baseline/forecast dates, gate refs.
- `gates[]`: id, criterion, evidence, approval, status.
- `risks[]`: id, likelihood, impact, owner, status.
- `workstreams[]`: name, posture, repo link, last_reconciled_commit.
- `baseline_version` plus an append-only `changes[]` log so scope changes are visible.

**B. Generated views, not hand-edited.** `README.md` snapshot, `tracking/STATUS.md`, `WORKSTREAM_STATUS.md`, and the status columns of `ROADMAP.md`, `GATE_REGISTER.md` and `RISK_REGISTER.md` are rendered from the YAML by a small script (e.g., `tools/render_status.py`) with a generated-file header. Narrative docs (PROGRAM_PLAN, PRODUCT_SCOPE, PRS, architecture, DECISIONS) stay hand-written.

**C. Computed, never typed:** accepted progress % at task, milestone, phase and program level; schedule variance; gate readiness. A validation step fails if acceptance = PASS has no evidence link, or if an evidence_type of `simulation` is used to close a `physical` gate.

**D. Ownership rule per fact** (single owner): task/acceptance status → YAML; dates → ROADMAP fields in YAML; dependencies → DEPENDENCY_MAP (hand-written, referenced by ID); decisions → DECISIONS.md.

**E. Sequencing:** reconcile repos first (REPOSITORY_BASELINE), then finalise P0 task list and weights, then seed the YAML. Do not build the renderer until at least P0 tasks exist.

## 5. Questions for ChatGPT

1. Do you agree YAML-as-source with generated markdown views is the right fit, or did you intend markdown tables to stay the source of truth (and if so, how should drift be prevented)?
2. Are the five status dimensions meant to be tracked at task level only, or also at milestone/phase level (versus computed roll-ups)?
3. How were baseline weights meant to be assigned (per task, per milestone, equal, effort-based)?
4. What is the intended rule for a scope change: new `baseline_version`, or a change log against a fixed baseline?
5. Which of the 14 workstreams are tracked inside this repo versus only linked to their own repos?
6. Should P0-M01-PROVISIONAL / P1-M01-PROVISIONAL IDs be finalised before any YAML is seeded (D-007)?
7. Any part of the original planning discussion (e.g., the superseded M0–M12 roadmap estimates) that should feed effort baselines after review?

## 6. Requested output from ChatGPT

A short reply with: agree / disagree on each of A–E, answers to the questions above, and the intended weighting scheme. Claude will then update the repo accordingly (schema, renderer, seeded P0 data) and record the outcome as a new decision (D-008) in `DECISIONS.md`.
