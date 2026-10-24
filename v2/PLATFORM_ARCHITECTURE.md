# Platform Architecture

**Owner of:** platform decomposition and software/hardware deployment boundaries.
**Status:** SKELETON — complete after [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) and repository reconciliation.

## Scope

- Decomposition of the platform into deployable units (Studio, Control Plane, Sim, SDK, Lab Agent, robot runtime, etc.).
- Which units run in cloud/server, on lab agents, or on robots.
- Mock/simulated versus physical deployment targets, so simulated acceptance is never conflated with physical validation.

## To complete

| Section | Content |
|---|---|
| Deployment units | Name, owning repository, runtime location |
| Environments | Dev, simulation, staging, production (P8) |
| Boundaries | Network, trust and ownership boundaries between units |
| Hardware dependency | Which units depend on physical hardware (HARDWARE-BLOCKED while mechanical HOLD) |

No content is asserted until verified.
