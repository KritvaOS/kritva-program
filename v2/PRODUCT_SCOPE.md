# Product Scope

**Owner of:** product boundaries, users, capabilities, in/out-of-scope features and release expectations.
**Status:** DRAFT — boundaries below come from the planning discussion; capability detail is to be completed in P0.

## 1. Scope posture

| Area | Posture |
|---|---|
| Core (R1.0) | **Closed / released.** Referenced as evidence; no duplicate implementation tasks. *(UNVERIFIED against repo — see REPOSITORY_BASELINE.md)* |
| Community (KOS-I2/I3/I4) | Completed work preserved with original identifiers; remaining safety reviews to be reconciled. *(UNVERIFIED)* |
| Sense, Motion, Skill, Mind, Sim, SDK, Studio, Control Plane, education applications, integration, software validation | **Continue** (non-mechanical software workstreams) |
| Simulation, mocks, versioned software interfaces | **Allowed** — acceptance is software-only |
| Mechanical CAD, actuator selection, mechanical BOM, manufacturing quotations, procurement, fabrication, physical prototype, mechanical design freeze | **HOLD** until explicitly reopened |

## 2. In scope (current baseline)

- Program planning, governance, tracking and evidence reconciliation.
- Software workstreams listed above, using simulation, mocks and versioned interfaces.
- Integration ownership, contracts and development infrastructure (P0 FOUNDATION).

## 3. Out of scope (current baseline)

- Any mechanical or physical-hardware work listed under HOLD.
- Physical safety approval based on simulation/mock evidence.
- Re-implementation of completed Core R1.0 or Community work.
- Detailed plans for P2–P8 before their prerequisites are met.

## 4. Users and capabilities

To be defined in [PRS.md](PRS.md). Do not add speculative capabilities here.

## 5. Release expectations

Defined per phase by gates in [GATE_REGISTER.md](GATE_REGISTER.md). Software and physical acceptance are separate gates.

## 6. Reopening HOLD items

Only by an explicit, recorded decision in [DECISIONS.md](DECISIONS.md) that updates this file and [ROADMAP.md](ROADMAP.md).
