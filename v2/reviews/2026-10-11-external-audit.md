# External Audit Record - 2026-10-11

**Source:** ChatGPT review of `KritvaOS/kritva-program` (main), run via the owner's Kritva Product Planning thread. Findings are advisory input, not verified facts. Related decisions: D-008, D-009 in [../DECISIONS.md](../DECISIONS.md).

## Findings and disposition

| Priority | Finding | Disposition |
|---|---|---|
| P0 | Repo was public while D-001 says private | Owner set repo to private; recorded as D-008. Exposure review still open (UNVERIFIED) |
| P0 | Dynamic status duplicated across STATUS, WORKSTREAM_STATUS, ROADMAP, GATE/RISK registers, README snapshot, milestone TASKS/COMPLETION_RECORD | Addressed by D-009 (generated views); manual tables stay until generation is proven |
| P0 | Provisional P0/P1 IDs; no approved P0 task weights | Open (D-007). `baseline.json` intentionally empty; progress reports N/A |
| P0 | `REPOSITORY_BASELINE.md` cites an initial commit SHA not verified against GitHub | Open |
| P1 | P1 has no task baseline but shows 0% | Report N/A until baseline exists |
| P1 | Two different workstream lists in use | Resolved: roster = 14 in WORKSTREAM_STATUS.md (`v2/tracking/workstreams.json`). Nexus Edge, Electrical, Actuation, Manufacturing remain reconciliation questions |

## Consolidation design agreed
Per-repo `status/status.json` (schema v1.0) -> `tools/consolidate_status.py` (validate, merge with approved registry and baseline) -> `v2/tracking/consolidated_status.json` and `STATUS_VIEW.md`. Engineering repos cannot change baseline weights or tasks. CI: `status-validate` and `status-generated-check` (workflow template at `tools/ci/status.yml`; copy to `.github/workflows/` to enable).

## Open design items
Task-level vs milestone-level records; waiver representation; freshness policy; pinned-ref strategy; per-repo status path confirmation.
