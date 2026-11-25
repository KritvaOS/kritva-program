# Risk Register

**Owner of:** program risks, impact, likelihood, mitigation, owner and disposition.
**Status:** DRAFT — initial risks derived from the planning discussion. Owners and scores TBD.

Scale: Likelihood and Impact = Low / Medium / High.

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| RISK-001 | Existing repository state is misjudged, leading to duplicated or missed work | Medium | High | Reconcile against GitHub commits, tags, tests before replanning | TBD | Open |
| RISK-002 | Integration ownership and contracts between workstreams are undefined | Medium | High | Define versioned contracts and owners in P0 FOUNDATION | TBD | Open |
| RISK-003 | Mechanical HOLD delays P6 LAB & ROBOT | High | High | Explicit reopen decision and entry criteria; keep software on mocks/sim | TBD | Open |
| RISK-004 | Simulated acceptance is mistaken for physical safety validation | Medium | High | Separate software vs physical gates; label evidence type | TBD | Open |
| RISK-005 | Conflicting status/phase terminology across documents | Medium | Medium | Frozen phase names; one owning document per fact | TBD | Open |
| RISK-006 | Effort estimated from commit counts | Medium | Medium | Evidence-backed effort logs only | TBD | Open |
| RISK-007 | Scope creep by removing unfinished tasks to inflate progress | Low | Medium | Preserve baselines; record scope changes | TBD | Open |
| RISK-008 | Six D-109 Community SDK planning rows (26 weight) overlap kritva-sdk scope, so ownership or credit could be duplicated or transferred without a decision | Medium | High | PD-021 accepted (D-151): re-home to kritva-sdk approved in principle; no weight, ownership or credit moves until the row mapping and baseline change are separately approved | TBD | Open |
| RISK-009 | SDK work for Control Plane and Sim is planned before any approved upstream API or interface exists | High | Medium | SDK milestones M3 and M5 are conditional; no adapter is built or pinned against a draft contract (DEP-007, DEP-008) | TBD | Open |
| RISK-010 | Vendored SDK contract schemas drift from the upstream contract | Medium | Medium | Pinned tag and commit SHA with provenance and a CI drift check (DEP-006); updates only by reviewed change | TBD | Open |

Add technical risks per workstream as reconciliation proceeds.
