# Acceptance Criteria: <repository>

Standard: kritva-program `v2/planning/ACCEPTANCE_STANDARD.md`. Criteria are objective and uniquely identified. Replace every angle-bracket field; a criterion that cannot be tested yet is listed under "Known limitations", not invented.

## 1. Purpose and scope
What the repository owns, and what it explicitly does not own.

## 2. Normative dependencies
Contract or repository IDs with exact versions or commit SHAs.

## 3. Functional criteria
| ID | Criterion (testable) | Verified by |
|---|---|---|
| AC-001 | <criterion> | <test or review> |

## 4. Interface and API compatibility
Types, units, timestamps, error handling, versioning and lifecycle.

## 5. Test gates
| Gate | Command | Required result |
|---|---|---|
| Unit | `make test-unit` | all pass |
| Integration | `make test-integration` | all pass |
| Regression | `make test-regression` | all pass, unchanged suite |

## 6. Specialised gates
Security, timing, determinism, simulation, hardware-in-loop, performance or safety, as applicable.

## 7. Evidence requirements
Immutable commit SHAs, CI run IDs, logs, test reports and review records.

## 8. Definition of Done
As in the standard, section 1, plus anything stricter this repository requires.

## 9. Known limitations and exclusions
Each with the approving decision ID.

## 10. Change control
How these criteria change without rewriting accepted evidence: new criteria versions, never edits to accepted ones.
