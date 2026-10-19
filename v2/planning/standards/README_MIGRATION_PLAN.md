# Kritva README Migration Plan

| Property | Value |
|---|---|
| Document ID | KOS-STD-README-MIGRATION |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | APPROVED with the README standard (D-066, 2026-10-19); revised by audit rounds 1 to 6 (D-056 to D-060) |
| Owner | Dinesh (program owner) |
| Authority | INPUT: the owner updates the table as each repository finishes |
| Related | [README_STANDARD.md](README_STANDARD.md) |

## Method

One repository at a time. For each: read its current README and files, restructure it to the standard (keeping its local governance and safety rules), run `check_readme.py`, open a PR, then have ChatGPT audit it through an access path the owner approves. The audit is advisory. The owner decides. Findings that belong in the shared standard or templates are fixed once there and reach every repository; findings about one repository are fixed in that repository. Do not copy a template over an existing README without reading it first: it may hold local rules.

Visibility is separate from this work. Today the owner has made the repositories listed in D-028 and D-037 temporarily public, which gives ChatGPT access. kritva-core, kritvaos-community and the four capability repositories are the exception: they are PUBLIC and stay public (D-063). A future-private repository is still written up as private. Temporary exposure and the return to private are owner actions recorded in the decision log, not steps of this plan, and no repository needs to be public for its README to be done.

A repository is marked DONE only when its PR is merged, `check_readme.py` passes on `main` and the owner has accepted the audit result. Copying a template in is not DONE.

**Register.** The table below is the maintained migration register. Owner: Dinesh. Last reviewed: 2026-10-19. The roster and each repository's visibility class come from `v2/planning/repo-pipeline.json` and `v2/tracking/repo_readiness.json`, not from this table. A new repository, or a change of a visibility class, is added here through the decision process. The numbers are a sequencing aid, not a repository count.

## Order

| # | Repository | Domain level | Why here | State |
|---|---|---|---|---|
| 1 | kritva-program | Program | Reference implementation | PILOT MERGED (D-055); audit round 1 applied (D-056), awaiting owner acceptance; aligned to D-057 |
| 2 | kritva-raas | Service | Software example | MERGED; audit round 2 applied |
| 3 | kritva-actuator | Hardware interface | Parent of the actuator family | MERGED; audit round 3 applied (D-057) |
| 4 | kritva-actuator-embedded | Firmware | Tests the standard on firmware and hardware validation | MERGED; audit round 4 applied (D-058) |
| 5 | kritva-actuator-s, -m, -l | Mechanical | Same template, three variants | MERGED; audit round 5 PARTIAL (D-059): S and L not yet audited |
| 6 | kritva-core | Library | Strict source-header lint applies | MERGED; audit round 6 applied (D-060, PARTIAL) |
| 7 | kritvaos-community | Platform integration | Source-header lint applies; parent of the core submodule | MERGED; audit round 7 applied |
| 8 | kritva-sense, -motion, -mind, -skill | Capability | Each carries a PR gate | MERGED; audit round 8 applied (PARTIAL; sense audited in full, the others by variant check) |

After repositories 2 to 4 the standard is reviewed against a service, a firmware and a mechanical repository, and changed if it did not fit. Later repositories use the revised standard.

## Later

- Done in the round after D-067: each repository has a `readme-check` workflow (a separate workflow, not a required check). Make it a required check only after it has run cleanly on a few pull requests; that is a separate owner decision per repository.
- Close the audit gap recorded in D-066: full audits of kritva-actuator-s, -m and -l, and a complete pass of the rounds that were PARTIAL, in small batches.
- Fill the exceptions table (section 11 of the standard) for any repository that needs a deviation.
