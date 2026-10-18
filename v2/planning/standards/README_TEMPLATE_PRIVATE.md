<!-- KritvaOS README template, PRIVATE repositories (kritva-program, kritva-raas, kritva-actuator*).
     Standard: v2/planning/standards/README_STANDARD.md in kritva-program.
     Copy below the line. Replace every <placeholder>. Link existing files only; write "Not yet defined" otherwise.
     Delete these comments. Check with: python3 scripts/docs/check_readme.py README.md -->

---

# <Repository name>

> <One sentence: what this repository is for.>

| Property | Value |
|---|---|
| Project | KritvaOS |
| Repository | `KritvaOS/<name>` |
| Repository Type | <Program / Platform / Library / Capability / Service / Firmware / Mechanical / Tooling / Documentation> |
| Current Visibility | <PUBLIC / PRIVATE> (verified <YYYY-MM-DD>) |
| Target Visibility | <PRIVATE> (<decision ID>; planned return <date>) |
| Lifecycle Status | <PLANNING / ACTIVE / ON_HOLD / ARCHIVED> |
| Repository Owner | <person or team> |
| Architecture | <link or Not yet defined> |
| Milestones | <link or Not yet defined> |
| Tasks | <link or Not yet defined> |
| Acceptance Criteria | <link or Not yet defined> |
| Status Reporting | <link or Not yet defined> |
| License | <link to LICENSE> (<license name>) |

## 1. Purpose and Scope

What this repository owns. What it explicitly does not own.

## 2. Position in the KritvaOS Ecosystem

Where it sits, what it consumes, what it produces. Link [kritva-program](https://github.com/KritvaOS/kritva-program) for plan, baseline and status.

## 3. Architecture

Short overview and a diagram if it helps. Link the detailed documents; do not copy them.

## 4. Documents to Read First

| Document | Label | What it answers |
|---|---|---|
| <link> | AUTHORITATIVE | <question> |

## 5. Repository Structure and File Responsibilities

| Path | Responsibility | Label | Edit by hand? |
|---|---|---|---|
| <path> | <what it controls or records> | <AUTHORITATIVE / INPUT / GENERATED / SNAPSHOT / EVIDENCE / REFERENCE> | <yes / no> |

## 6. Toolchain and Development Workflow

| Tool | Purpose | Version | Check |
|---|---|---|---|
| <tool> | <purpose> | <version> | `<command>` |

Setup, build and generation commands that exist in this repository.

## 7. Dependencies and Interfaces

| Dependency | Direction | Kind | Contract | State |
|---|---|---|---|---|
| <repository or component> | upstream / downstream | build / runtime / governance | <interface document> | <ESTABLISHED / PROPOSED / PLANNED / UNVERIFIED> |

## 8. Milestones and Implementation Plan

| Item | Document | Purpose |
|---|---|---|
| Roadmap | <link> | Development sequence |
| Milestones | <link> | Milestones, deliverables, gates |

## 9. Tasks and Acceptance Criteria

Where tasks live, how an ID is registered, and where the acceptance criteria are. Work is not accepted because code, a commit, a merged PR or a local test exists.

## 10. Status Reporting and Program Integration

Status file and schema version, the tool that writes it, how kritva-program consumes it, what each state means.

## 11. Build, Test, Regression and Validation

| Check | Command | Runs in CI? | Expected |
|---|---|---|---|
| <check> | `<command>` | <yes / no> | <result> |

A test that is not implemented is listed as not implemented, never as passing.

## 12. Git Workflow and Review

Commit format (`type(scope): summary` and a `Task:` or `Tasks:` footer, see kritva-program ACCEPTANCE_STANDARD section 4), branch rule, PR requirements, required checks, merge method.

## 13. Safety and Security

Safety requirements and open gates (hardware repositories), security reporting, secrets. State that software tests do not prove physical safety.

## 14. Release and Versioning

Version scheme, tags, required checks and approvals, changelog, known limitations.

## 15. Ownership and Escalation

Owner, reviewers, how a blocker is raised.

## 16. Related Repositories and References

Upstream, downstream and integration repositories.

## 17. License

<License name>. See [LICENSE](LICENSE).
