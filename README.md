# kritva-program

Program-level planning, governance and status reporting for **Kritva OS**: the decision log, the frozen baseline, approvals, release gates, risks, roadmap and the consolidated status view.

This repository records program-level truth. It does **not** contain engineering source code. The engineering repositories remain authoritative for their own code, tests and releases, and report facts to this one. Dinesh (owner and Security Owner) decides; advice from AI tools is advisory only.

> Visibility: all nine repositories are temporarily public (D-028) and are planned to return to private on 2026-11-15 (D-037).

## 1. Program planning

| Concept | What it is | Where it lives |
|---|---|---|
| Phases P0-P8 | Frozen sequence: FOUNDATION, STUDIO, BUILD & ARTIFACT, CONTROL PLANE, BOOKING & COMMERCIAL, EXECUTION, LAB & ROBOT, LIVE & RESULTS, PRODUCTION | [v2/PROGRAM_PLAN.md](v2/PROGRAM_PLAN.md), [v2/ROADMAP.md](v2/ROADMAP.md) |
| Workstreams | Registered areas of work, each owned by a repository where one exists | [v2/tracking/workstreams.json](v2/tracking/workstreams.json) |
| Baseline | The approved, frozen set of tasks and weights that progress is measured against (v2: 31 tasks, weight 104) | [v2/tracking/baseline.json](v2/tracking/baseline.json), [baselines/](v2/tracking/baselines/) |
| Approvals | Append-only ledger of review and acceptance records; a repository can never accept its own work | [v2/tracking/approvals.json](v2/tracking/approvals.json) |
| Gates | Open safety and release gates that give zero credit to the tasks in their scope | [v2/GATE_REGISTER.md](v2/GATE_REGISTER.md), [gate_closures.json](v2/tracking/gate_closures.json) |
| Planning inventory | Tasks that are planned but not baselined (RaaS and actuators). Planning only: no weights, no credit | [v2/tracking/planning_inventory.json](v2/tracking/planning_inventory.json) |
| Decisions | Append-only log with rationale and status (D-001 onward) | [v2/DECISIONS.md](v2/DECISIONS.md) |
| Dependencies, risks | Provider/consumer map, critical path, risk register | [DEPENDENCY_MAP](v2/DEPENDENCY_MAP.md), [CRITICAL_PATH](v2/CRITICAL_PATH.md), [RISK_REGISTER](v2/RISK_REGISTER.md) |

Phase dates are **not approved** (see the roadmap); no schedule is implied anywhere in this repository. Mechanical work is on HOLD (D-003) until the owner reopens it. The program dashboard and document index are in [v2/README.md](v2/README.md).

## 2. Repository layout

### The nine Kritva repositories

| Repository | Role |
|---|---|
| [kritva-program](https://github.com/KritvaOS/kritva-program) | This repository: plan, baseline, decisions, approvals, gates, source snapshots, consolidated reporting |
| [kritva-core](https://github.com/KritvaOS/kritva-core) | Kritva Core implementation and its engineering evidence (baselined) |
| [kritvaos-community](https://github.com/KritvaOS/kritvaos-community) | Community implementation, integration and evidence (baselined) |
| [kritva-raas](https://github.com/KritvaOS/kritva-raas) | Robotic-as-a-Service backend planning; not a baseline source, planning only |
| [kritva-actuator](https://github.com/KritvaOS/kritva-actuator) | Parent actuator repository: shared interface, requirements and integration |
| [kritva-actuator-embedded](https://github.com/KritvaOS/kritva-actuator-embedded) | Firmware and electronics for the actuator family |
| [kritva-actuator-s](https://github.com/KritvaOS/kritva-actuator-s), [-m](https://github.com/KritvaOS/kritva-actuator-m), [-l](https://github.com/KritvaOS/kritva-actuator-l) | Mechanical design of the S, M and L variants (HOLD) |

Repositories report implementation facts and evidence. This repository owns program-level acceptance, baseline credit and approvals. A repository edit never creates credit.

### This repository

| Path | Purpose |
|---|---|
| [v2/](v2/) | Program documents: plan, scope, roadmap, gates, risks, decisions, reviews |
| [v2/tracking/](v2/tracking/) | Machine-readable program records and the generated status view |
| [sources/](sources/) | Committed copies of each repository's `status/status.json`, with provenance in `MANIFEST.json` |
| [status/](status/) | This repository's own status report (workstream CI_DEV_INFRA) |
| [schema/](schema/) | `status.schema.json`, the status report schema (version 2.0) |
| [tools/](tools/) | The consolidator and helpers (see below) |
| [tests/](tests/) | Unit tests for the tools |
| [scripts/security/](scripts/security/) | Commit-message check used by CI |
| [.github/](.github/) | Workflows and CODEOWNERS |

## 3. Status reporting

```text
  each repo: status/status.json (schema 2.0)
                    |
                    v
          sources/  (committed snapshots)
                    |
                    v
   tools/consolidate_status.py  <---  baseline, approvals, gates
              |             |
              v             v
  consolidated_status.json   STATUS_VIEW.md (summary)   STATUS_DETAIL.md (full tables)
```

1. **Repositories report facts.** Each repository's generator writes `status/status.json` (schema 2.0): per task, `execution`, `git_sync`, `readiness` and `evidence`. Reports never contain review or acceptance.
2. **Snapshots.** The `refresh-sources` workflow proposes daily pull requests that update `sources/` from each repository; a human reviews and merges.
3. **Consolidation.** `tools/consolidate_status.py` validates every report against the baseline and approvals and computes progress. Stale, missing or unverified inputs earn no credit and are never silently passed.
4. **Generated views.** [v2/tracking/STATUS_VIEW.md](v2/tracking/STATUS_VIEW.md) is the short summary: owner actions and blockers, what changed since the previous snapshot, the three measures, progress by workstream, the readiness matrix, dated milestones, phase order and a data-quality summary. [v2/tracking/STATUS_DETAIL.md](v2/tracking/STATUS_DETAIL.md) holds the full tables (workstreams, tasks, gates, effort, per-repo readiness, evidence health, warnings). Both are plain Markdown, generated: edit the inputs or the tools, never the output.

### Three measures, never combined

| Measure | Definition | Source |
|---|---|---|
| Accepted engineering progress | Accepted weight / baseline weight of the frozen baseline (currently 48/104 = 46.15%). Credit needs an approval and verified CI evidence | baseline, approvals, status reports |
| Estimated effort | Owner-estimated person-months done and remaining. Not timesheets, not progress, not a schedule | [effort_estimates.json](v2/tracking/effort_estimates.json) |
| Capability completion | Owner estimate of delivered scope per workstream; no formal inventory exists yet | effort estimates |

None of these is a delivery date, and they are not averaged into a "health" figure. Charts in the status view are snapshots, not approvals or schedule commitments.

### Repository readiness

[v2/tracking/repo_readiness.json](v2/tracking/repo_readiness.json) holds a per-repository checklist for the return to private (D-037, D-039). It is **display only**: it adds no credit and does not change the baseline. A repository is READY only when every check is PASS, ATTESTED (owner-stated, not verified) or NA. Owner sign-off is recorded per repository (D-042); it is not a waiver of open checks. GitHub settings such as rulesets cannot be read by tooling, so they stay ATTESTED.

## 4. Update and validate

```bash
python3 -m unittest discover -s tests
python3 tools/consolidate_status.py --sources-dir sources            # regenerate JSON, STATUS_VIEW.md and STATUS_DETAIL.md
python3 tools/consolidate_status.py --sources-dir sources --check    # fail if committed output is out of date
python3 tools/check_planning_inventory.py .                          # planning inventory rules
```

Change an input (baseline, approvals, gates, sources, effort, readiness, planning inventory), regenerate, and commit the generated files in the same pull request. CI runs the same checks, plus `secret-scan` and `commit-message-check`.

## 5. Rules

1. Engineering repositories stay authoritative for implementation; reconcile against them before planning.
2. Use the frozen phase names exactly ([v2/PROGRAM_PLAN.md](v2/PROGRAM_PLAN.md)).
3. Mechanical work is on HOLD until explicitly reopened.
4. Status is evidence-backed. A commit is not acceptance.
5. Do not create empty future plans.
6. Never edit `baseline.json`, `approvals.json`, `gate_closures.json` or the generated status files by hand; the decision log is append-only. See [AGENTS.md](AGENTS.md) and [SECURITY.md](SECURITY.md).

## Where to start

[v2/README.md](v2/README.md) (dashboard and document index), [v2/tracking/STATUS_VIEW.md](v2/tracking/STATUS_VIEW.md) (generated summary; detail in [STATUS_DETAIL.md](v2/tracking/STATUS_DETAIL.md)), [v2/DECISIONS.md](v2/DECISIONS.md) (decisions).
