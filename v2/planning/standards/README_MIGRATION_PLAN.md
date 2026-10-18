# Kritva README Migration Plan

| Property | Value |
|---|---|
| Document ID | KOS-STD-README-MIGRATION |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | PROPOSED (pilot in kritva-program, D-055, revised by audit round 1, D-056) |
| Owner | Dinesh (program owner) |
| Authority | INPUT: the owner updates the table as each repository finishes |
| Related | [README_STANDARD.md](README_STANDARD.md) |

## Method

One repository at a time. For each: read its current README and files, restructure it to the standard (keeping its local governance and safety rules), run `check_readme.py`, open a PR, then have ChatGPT audit it through an access path the owner approves. The audit is advisory. The owner decides. Findings that belong in the shared standard or templates are fixed once there and reach every repository; findings about one repository are fixed in that repository. Do not copy a template over an existing README without reading it first: it may hold local rules.

Visibility is separate from this work. Today the owner has made the repositories listed in D-028 and D-037 temporarily public, which gives ChatGPT access. A future-private repository is still written up as private. Temporary exposure and the return to private are owner actions recorded in the decision log, not steps of this plan, and no repository needs to be public for its README to be done.

A repository is marked DONE only when its PR is merged, `check_readme.py` passes on `main` and the owner has accepted the audit result. Copying a template in is not DONE.

**Register.** The table below is the maintained migration register. Owner: Dinesh. Last reviewed: 2026-10-18. The roster and each repository's visibility class come from `v2/planning/repo-pipeline.json` and `v2/tracking/repo_readiness.json`, not from this table. A new repository, or a change of a visibility class, is added here through the decision process. The numbers are a sequencing aid, not a repository count.

## Order

| # | Repository | Domain level | Why here | State |
|---|---|---|---|---|
| 1 | kritva-program | Program | Reference implementation | PILOT MERGED (D-055); audit round 1 applied (D-056), awaiting owner acceptance |
| 2 | kritva-raas | Service | Software example | NOT STARTED |
| 3 | kritva-actuator | Hardware interface | Parent of the actuator family | NOT STARTED |
| 4 | kritva-actuator-embedded | Firmware | Tests the standard on firmware and hardware validation | NOT STARTED |
| 5 | kritva-actuator-s, -m, -l | Mechanical | Same template, three variants | NOT STARTED |
| 6 | kritva-core | Library | Strict source-header lint applies | NOT STARTED |
| 7 | kritvaos-community | Library | Source-header lint applies | NOT STARTED |
| 8 | kritva-sense, -motion, -mind, -skill | Capability | Each carries a PR gate | NOT STARTED |

After repositories 2 to 4 the standard is reviewed against a service, a firmware and a mechanical repository, and changed if it did not fit. Later repositories use the revised standard.

## Later

- Add `check_readme.py` to each repository's CI once its README passes (a workflow change, so an owner decision per repository).
- Fill the exceptions table (section 11 of the standard) for any repository that needs a deviation.
