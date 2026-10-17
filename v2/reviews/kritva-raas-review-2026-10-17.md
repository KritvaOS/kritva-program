# kritva-raas review for the program (2026-10-17)

Basis: local clone at `main` = `20e8905` (same as remote `main`, checked with `git ls-remote`). I read the README, Makefile, handoff, planning entry points, the backend security gate, the B-INC-001 task register, tracking files and both CI workflows. I did not read B-INC-002 to B-INC-004, the 11,000 lines of `docs/tracking/`, or `apps/backend` source. No tests or checks were run.

## Verdict

RaaS is not ready to be a status source, but it is closer than the actuator repos and stricter than Core and Community on acceptance honesty. It needs a generator, a workstream record and an agent-instruction file. Its tasks should go into the planning inventory now and into a baseline version later.

## What fits the engineering contract

- Commit subject `<type>(backend): <summary> [<TASK-ID>]` already matches `type(scope): description [TASK-ID]`, and a checker enforces the task trailers.
- Required checks `source-header-check` and `docs-check` run on every push and pull request, with a ruleset on `main` (no deletion, no force-push, pull request required, 0 approvals).
- Planning docs state that a merged PR, a passing check or a status change is not acceptance, and that owner or AI review is not independent human review. That matches program rule D-005.
- Task IDs are stable and namespaced (`KR-BE-1-nnn` kept from B-M01, `KR-BINC-001-nnn` new).

## Gaps against the program

| # | Finding | Why it matters | Suggested fix |
|---|---|---|---|
| 1 | No `status/status.json`, `workstream.json` or generator | The consolidator cannot read RaaS; onboarding steps 1 and 2 are not started | Copy Core's generator; emit schema 2.0 from increment `TASKS.md`, failing closed on missing or unknown status |
| 2 | 16 of 29 B-INC-001 tasks have no `Status:` line in `TASKS.md` | A generator would have to guess; the program rule is fail closed | Add an explicit status to every task (Proposed is acceptable) before generating |
| 3 | Three tasks are Accepted (KR-BE-1-001, KR-BINC-001-018, KR-BINC-001-019), all by the owner; ten are In Review | Owner acceptance is not a program approval PASS and has no approved commit plus CI run attached | Do not pre-credit. Review each Accepted task through the normal chain once RaaS is a source |
| 4 | No `AGENTS.md` or `CLAUDE.md`; agent rules are in `planning/AGENT_RULES.md` and `claude/Handoff.md` | The contract expects the standard files so any agent finds the rules | Add a short `AGENTS.md` that points to `planning/AGENT_RULES.md`; `CLAUDE.md` imports it |
| 5 | The handoff is stale: it says `main` is `4ab6402` (PR #42) and uses the path `kritvaOS` with a capital O; real `main` is `20e8905` | Anyone resuming from it starts from wrong facts | Refresh at the next handoff update |
| 6 | `make test`, `make build` and `make lint` fail on purpose until decisions KR-BINC-001-001 to 004 are made, yet `apps/backend` exists (Node 24.21.0, Fastify 5.12.5) and tasks are In Review | L2 and L3 test levels cannot be reported; "linked tests NOT RUN" stays true for every task | Settle the toolchain decisions, then wire `make test` so CI can run it |
| 7 | No secret scanning in CI (KR-BINC-001-008 to 010 have no status); SEC-GATE-001 historical credential-shaped finding has no Security Owner disposition | The repo's own invariant is "no secrets"; the control that proves it is not yet in place | Put these tasks first in the next increment of work |
| 8 | `RAAS` and `CONTROL_PLANE` are separate program workstreams, but RaaS milestone B-M01 is "CONTROL PLANE" | Risk of double counting or a gap | Dinesh decides: is the backend control plane part of RAAS, or its own workstream? |
| 9 | The program's `workstreams.json` still says RaaS has "no verified task IDs" | No longer true for B-INC-001 | Update the note when D-026 is recorded |
| 10 | Milestone Task Register for B-M01 shows KR-BE-1-001 unchecked while the increment says Accepted (listed in the repo's own CURRENT_PLAN) | Two records disagree | Owner decides which view to update |
| 11 | Remote branch `refactor/move-planning-root` (`b789a04`) still exists | A leftover branch can mislead readers about what is current | Confirm it is merged, then delete |
| 12 | The ruleset is named `main-protectionain` | Cosmetic typo | Rename |

## Not verified

- Whether `apps/backend` code matches the task records.
- Status of B-INC-002 to B-INC-004 (all shown as Proposed in the task register).
- Actual CI results on `20e8905` (I did not read check runs).
- Ruleset bypass actors: the API output I could read did not show any; the handoff says none.
