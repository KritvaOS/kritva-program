# Kritva README Migration Plan

| Property | Value |
|---|---|
| Document ID | KOS-STD-README-MIGRATION |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Plan |
| Status | PROPOSED (pilot in kritva-program, D-055) |
| Owner | Dinesh (program owner) |
| Authority | INPUT: the owner updates the table as each repository finishes |
| Related | [README_STANDARD.md](README_STANDARD.md) |

## Method

One repository at a time. For each: read its current README and files, restructure it to the standard (keeping its local governance and safety rules), run `check_readme.py`, open a PR, then give the repository to ChatGPT for an external audit while it is public. The audit is advisory. The owner decides. Do not copy a template over an existing README without reading it first: it may hold local rules.

A repository that is private by design is made temporarily public for alignment and review (D-028, D-037) and returned to private afterwards. Return dates are tracked in the visibility decisions, not here.

A repository is marked DONE only when its PR is merged, `check_readme.py` passes on `main` and the owner has accepted the audit result. Copying a template in is not DONE.

## Order

| # | Repository | Domain level | Why here | State |
|---|---|---|---|---|
| 1 | kritva-program | Program | Reference implementation | IN PROGRESS (D-055) |
| 2 | kritva-raas | Service | Software example; future private | NOT STARTED |
| 3 | kritva-actuator | Hardware interface | Parent of the actuator family; future private | NOT STARTED |
| 4 | kritva-actuator-embedded | Firmware | Tests the standard on firmware and hardware validation | NOT STARTED |
| 5 | kritva-actuator-s, -m, -l | Mechanical | Same template, three variants | NOT STARTED |
| 6 | kritva-core | Library | Public; strict source-header lint applies | NOT STARTED |
| 7 | kritvaos-community | Library | Public | NOT STARTED |
| 8 | kritva-sense, -motion, -mind, -skill | Capability | Public; each carries a PR gate | NOT STARTED |

After repositories 2 to 4 the standard is reviewed against a service, a firmware and a mechanical repository, and changed if it did not fit. Later repositories use the revised standard.

## Later

- Add `check_readme.py` to each repository's CI once its README passes (a workflow change, so an owner decision per repository).
- Fill the exceptions table (section 9 of the standard) for any repository that needs a deviation.
