# V2 Acceptance Standard (approved)

**Owner of:** the common acceptance, test, commit, tag and merge rules for every Kritva repository in the V2 plan.
**Status:** APPROVED. PD-005 (acceptance and test policy) and PD-006 (tag policy) by D-080, PD-007 (reviewer roles, interim) by D-047, PD-010 (merge method) by D-053. No coverage threshold is set. Repository CI checks below are enforced only where a repository has adopted them.
**Relation to D-023:** the approved engineering contract (D-023) remains the controlling lifecycle, branch, commit and tag convention. Where this standard and the pinned contract text differ, the contract wins and this file is corrected. The contract text is not yet committed here (readiness check `contract_pin`).

The frozen baseline is not touched by anything in this file. V2 milestones and repository tasks added under this standard are planning inventory: no weight, no credit, until a separately approved baseline amendment.

## 1. Task definition of done

A task is done only when all of these hold:

1. It has a stable ID (section 4) and testable acceptance criteria in the repository's `ACCEPTANCE_CRITERIA.md`.
2. The change merged through the approved pull request process (the repository's required approvals in [repo-pipeline.json](repo-pipeline.json)).
3. Every required check passed on the exact closing commit.
4. Required reviews, including any security or safety approval, are recorded against that commit.
5. Documentation and the changelog are updated.
6. Evidence points to immutable references: commit SHAs and CI run IDs, never branch names.
7. No blocking issue was converted into a pass. A waiver is a structured record (approver, scope, rationale, expiry or review condition) and is never reported as PASS.
8. Status is reported from the repository's canonical status record, not from commit counts.

Software acceptance (unit tests, simulation, mocks, versioned interfaces) is never reported as hardware or safety validation.

## 2. Milestone closure

A milestone closes only through an approved `COMPLETION_RECORD.md` in the repository (template: [templates/COMPLETION_RECORD.template.md](templates/COMPLETION_RECORD.template.md)). It names the milestone ID, scope, exact merge and release commits, test runs, the tag if one exists, the disposition of each criterion, deferred work, approvals and evidence. A merge, a passing CI run, a tag, or a task marked complete does not close a milestone.

## 3. Test gates

Every repository exposes the same make targets. A target that is not yet implemented must say so and exit non-zero (exit code 3, `NOT_IMPLEMENTED`); an unimplemented gate is never a pass. A gate may be `NOT_APPLICABLE` only through a structured, approved disposition.

| Target | Meaning |
|---|---|
| `make check` | Repository structure and planning files are valid; commit format checker self-test |
| `make lint` | Static checks for the repository's languages |
| `make test-unit` | Unit tests; command and required result stated in `ACCEPTANCE_CRITERIA.md`; coverage threshold only if approved |
| `make test-integration` | Real dependency boundaries, contract compatibility, failure paths |
| `make test-regression` | Regression suite: prior defects and compatibility guarantees. A fixed defect adds a test here |
| `make test` | Unit, integration and regression together |
| `make docs-check` | Links and generated documents are current |
| `make acceptance` | All criteria in `ACCEPTANCE_CRITERIA.md` that are automatable |

Required gates per repository kind are in `repo-pipeline.json` (`local_gates`) and are listed in [V2_REPO_PLAN.md](V2_REPO_PLAN.md). Hardware-in-loop tests may be unavailable before hardware exists: the software tests can pass, while the missing physical evidence stays visible and is never described as hardware acceptance.

Regression policy: the regression suite must pass unchanged before and after every change to a public interface. A breaking change needs a MAJOR version, a changelog entry and an approved decision.

## 4. Commit format

```text
type(scope): summary of at most 90 characters [TASK-ID]

Optional body.

Task: KOS-SENSE-001
```

- Types: feat, fix, docs, refactor, test, build, ci, chore, perf, revert, security. Scope is lower-case and free-form; the vocabulary in use is `backend` (backend code), `repo`, `planning`, `governance`, `docs`, `security` and the repository's own area names.
- Exactly one footer line, `Task:` or `Tasks:`, with one or more comma-separated IDs (`Tasks: KOS-X-1-044, KOS-X-1-045`). An ID is upper-case segments joined by hyphens, from the repository's task record (examples: KOS-SENSE-001, KRP-ENG-001, KF-CORE-R10-001, I2-001, KOS-X-1-044).
- A commit that implements no task (a record correction, a docs-only change) is a `docs` or `chore` commit with `Tasks: None (reason)`. The reason is mandatory and no other type may use it.
- The subject suffix `[TASK-ID]` is optional and not enforced. If present it must be one of the footer IDs and cannot go with `Tasks: None`.
- The ID should exist in the repository's task record; `scripts/security/check_commit_format.py --registry` rejects unknown IDs.
- Other trailers are allowed; a repository may require more under its own checker, which is a repository rule on top of this standard.
- No AI-session trailer or link (`Claude-Session:`, claude.ai session URLs); the existing `commit-message-check` already rejects these. Ordinary Git metadata, `Co-Authored-By` and `Signed-off-by` are allowed.
- The merge method is a merge commit (D-053, resolving PD-010), so the checked commits are the PR's own commits. The PR title follows the same `type(scope): summary` style.
- Every other commit needs a task. If a change belongs to no existing task, create the task in the repository's task record first; do not reuse an unrelated ID and do not invent one.

Checker: `python3 scripts/security/check_commit_format.py --range origin/main..HEAD`. Enforcement in CI starts only after dry runs on representative PRs.

### PR description

Every repository carries `.github/PULL_REQUEST_TEMPLATE.md`, the template in [templates/PULL_REQUEST_TEMPLATE.md](templates/PULL_REQUEST_TEMPLATE.md). It combines a README list (summary, scope and exclusions, commits, task and test table, validation, what is pending) with the ten BRANCHING_STRATEGY headings. A heading that does not apply says "Not applicable". The body is not checked by the gate.

## 5. Git tags

- Release tags are annotated SemVer: `vMAJOR.MINOR.PATCH` (v0.1.0 first preview, v0.2.0 compatible preview increment, v1.0.0 approved stable boundary, v1.1.0 compatible feature, v2.0.0 breaking).
- A milestone prerelease artifact may use `vX.Y.Z-milestone.v2-mN`. The product version stays X.Y.Z; the suffix is metadata. Use it only for an actual prerelease artifact, not for documentation-only checkpoints.
- Phase numbers are program metadata, not SemVer; no `v0.<phase>.<n>` tags and no tag per program milestone when nothing versionable shipped.
- Create the tag only after the approved merge and required checks. The tag message names the completion record and the exact commit.
- `ship-prs.sh --tag vX.Y.Z` validates the tag with `scripts/pipeline/manifest.py tag-ok`, requires the repository's COMPLETION_RECORD.md when the manifest says so, and creates an annotated tag. A tag is evidence, not closure authority.

## 6. PR approval sequence

The sequence, dependencies, required approvals and required checks per repository are in [repo-pipeline.json](repo-pipeline.json) and rendered in [V2_REPO_PLAN.md](V2_REPO_PLAN.md). `ship-prs.sh --manifest v2/planning/repo-pipeline.json` reads the order from it, never from a hard-coded list. A downstream PR is merged only after its declared dependencies are merged; independent repositories can proceed in parallel. Approvals made before the PR head changed are stale and are not accepted.

## 7. Required files per repository

```text
ACCEPTANCE_CRITERIA.md  planning/{TASKS,MILESTONE,MILESTONE_STATUS,REVIEW_CHECKLIST,GIT_COMMIT_STEP,CHANGELOG}.md
AGENTS.md  SECURITY.md  CONTRIBUTING.md  LICENSE  Makefile  .github/CODEOWNERS
.github/workflows/{secret-scan,commit-message-check}.yml
COMPLETION_RECORD.md    only when a milestone is closing
tasks/<TASK-ID>/TASK.md only when a real task exists
```

No empty folders and no placeholder tasks. Template for `ACCEPTANCE_CRITERIA.md`: [templates/ACCEPTANCE_CRITERIA.template.md](templates/ACCEPTANCE_CRITERIA.template.md).

## 8. Status contract

Each repository adopts the program status contract (`status/status.json`, schema 2.0, generated and checked in CI) once the shared template and schema version are confirmed. Until then its workstream stays UNVERIFIED in the program status view, which is accurate: no source means no evidence and no credit.
