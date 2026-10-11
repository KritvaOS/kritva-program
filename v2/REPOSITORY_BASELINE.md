# Repository Baseline

**Owner of:** existing repositories, branch/tag/commit evidence, implementation state and authoritative source locations.
**Status:** TEMPLATE — **not yet reconciled.** No repository facts have been verified. Fill only from actual GitHub/repo inspection.

## Reconciliation procedure

For each repository: record default branch, latest commit, release tags, test results, open PRs/reviews, outstanding safety gates; then classify work as complete / partial / not started with a link to evidence.

## Repositories

| Repository | Purpose | Default branch | Latest commit | Release/tag | Tests | Open reviews/gates | State |
|---|---|---|---|---|---|---|---|
| kritva-program (this) | Program planning | main | 33b8a61 (initial commit) | — | n/a | — | Initialised |
| Core | Core platform | TBD | TBD | R1.0 (reported released/closed — verify) | TBD | TBD | UNVERIFIED |
| Community | Community platform | TBD | TBD | KOS-I2/I3/I4 reported done — verify | TBD | Safety reviews outstanding (verify) | UNVERIFIED |
| Other workstream repos (Sense, Motion, Skill, Mind, Sim, SDK, Studio, Control Plane, RaaS, education) | TBD | TBD | TBD | TBD | TBD | TBD | UNKNOWN — inventory needed |

## Rules

- Existing engineering identifiers (e.g. KOS-I2/I3/I4) are preserved, never renamed.
- Evidence types are labelled: software/simulation vs physical.
- Findings feed [WORKSTREAM_STATUS.md](WORKSTREAM_STATUS.md) and [REQUIREMENT_TRACEABILITY.md](REQUIREMENT_TRACEABILITY.md).
