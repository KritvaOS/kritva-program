# System Architecture

**Owner of:** system-level components, boundaries and interactions.
**Status:** SKELETON — to be completed during P0 FOUNDATION from reconciled repository evidence. No architecture is asserted beyond what the planning discussion established.

## 1. Known components (names only, from planning discussion)

Core, Community, Sense, Motion, Skill, Mind, Sim, SDK, Studio, Control Plane, RaaS, education applications, Lab Agent, robots.

Relationships and interfaces between these are **not yet documented** and must be derived from the repositories, not assumed.

## 2. To complete

| Section | Content | Source |
|---|---|---|
| Context diagram | Actors and external systems | PRS, PRODUCT_SCOPE |
| Component map | Components, owning repository, responsibility | REPOSITORY_BASELINE |
| Interfaces | Versioned contracts between components (P0 integration contracts) | Engineering repos |
| Data flows | Control, telemetry, video, results, booking/commercial | P3–P7 planning |
| Safety boundary | Software vs physical acceptance boundary | PROGRAM_PLAN rule 4 |

## 3. Rules

- Architecture changes that alter a phase boundary or interface require an entry in [DECISIONS.md](DECISIONS.md).
- Platform deployment decomposition lives in [PLATFORM_ARCHITECTURE.md](PLATFORM_ARCHITECTURE.md).
