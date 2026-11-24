## Summary
Adds D-148 to `v2/DECISIONS.md`: a provisional, non-blocking working direction for the Control Plane. RaaS remains the owner of the capability and its implementation responsibility, and the separate repository planned in D-144 remains the planned code location, pending confirmation during V2-M3 planning. D-144 is not superseded. PD-020 stays open for that confirmation: its action text now carries the working direction, V2-M3 joins its scope and D-148 its evidence. `PENDING_DECISIONS.md` is regenerated.

## Scope and exclusions
`v2/DECISIONS.md`, `v2/planning/decisions.json`, `v2/planning/PENDING_DECISIONS.md`. No repository is created or registered, no `repo-pipeline.json` entry, no D-109 register row moves, no task is reassigned. No change to `baseline.json`, `approvals.json`, `gate_closures.json`, `planning_inventory.json`, weights, estimates, task IDs or credit. Public record: names no private repository, register or decision.

## Tasks and milestone
None (record keeping; no task is started or completed).

## Commits
One commit.

## Architecture impact
None.

## Security impact
None. The Security Owner review of the Control Plane authorisation boundary stays a prerequisite for accepting the authorisation design at V2-M3.

## Testing
`python3 tools/planning.py --root . --check` and `make verify` passed on a copy with the change. The status files are unchanged by it (PD-020 stays PROPOSED), so they are not regenerated. `make preflight` runs in `run.sh` and was not run by the author. The commit format check passed.

## Risks
D-148 uses the next ID after D-147 in the checkout this was built from; `run.sh` stops if it is already taken.
