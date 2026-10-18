<!-- KritvaOS README template, PRIVATE repositories.
     Use it for every repository whose approved Visibility Class is PRIVATE, whatever its GitHub setting is today
     (a temporary public setting does not change the template). The class of each repository is recorded in the
     visibility decision and in v2/tracking/repo_readiness.json in kritva-program, not in this comment.
     Standard: v2/planning/standards/README_STANDARD.md in kritva-program.
     Copy below the line. Replace every <placeholder>. Link existing files only; write "Not yet defined" otherwise.
     Delete these comments. Check with: python3 scripts/docs/check_readme.py README.md -->

---

# <Repository name>

> <One sentence: what this repository is for. It is a private repository.>

| Property | Value |
|---|---|
| Project | KritvaOS |
| Repository | `KritvaOS/<name>` |
| Repository Type | <Program / Platform / Library / Capability / Service / Firmware / Mechanical / Tooling / Documentation> |
| Visibility Class | <PRIVATE> (<decision ID>) |
| GitHub Setting | <PUBLIC or PRIVATE> (verified <YYYY-MM-DD>; <temporary, decision ID, if it differs from the class>) |
| Lifecycle Status | <PLANNING / ACTIVE / ON_HOLD / ARCHIVED> |
| Repository Owner | <person or team> |
| Technical Owner | <optional: person, team or link; required when it differs from the owner> |
| Security Owner | <optional: person, team or link; required for hardware safety, credentials, private data or security gates> |
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

Short overview and a diagram if it helps. Link the detailed documents and show each one's status (a skeleton is not an architecture). Do not copy them.

## 4. Documents to Read First

| Document | Label, status | What it answers |
|---|---|---|
| <link> | <AUTHORITATIVE, APPROVED> | <question> |

A label names a role, not an approval. Show the document's status (DRAFT, SKELETON, PROPOSED, APPROVED) beside it.

## 5. Repository Structure and File Responsibilities

| Path | Responsibility | Label, status | Edit by hand? |
|---|---|---|---|
| <path> | <what it controls or records> | <AUTHORITATIVE / INPUT / GENERATED / SNAPSHOT / EVIDENCE / REFERENCE / MIXED> | <yes / no> |

A directory with files of several labels is MIXED: list its principal files. Mark each principal capability and tree entry with its implementation state (IMPLEMENTED, PLANNED, PROPOSED, REFERENCE-ONLY, EVIDENCE or NOT YET IMPLEMENTED); a scaffold-only folder says so.

## 6. Toolchain and Development Workflow

| Tool | Purpose | Version | Check |
|---|---|---|---|
| <tool> | <purpose> | <version> | `<command>` |

| Command | Effect | Needs | Preview |
|---|---|---|---|
| `<command>` | <check / generate / modify / merge / deploy / publish> | <permission or credential, never the secret> | <dry-run option or none> |

Put a one-line warning before any command that modifies, merges, deploys or publishes.

## 7. Dependencies and Interfaces

| Dependency | Direction | Kind | Contract | State |
|---|---|---|---|---|
| <repository or component> | upstream / downstream | build / runtime / governance | <interface document> | <ESTABLISHED / PROPOSED / PLANNED / UNVERIFIED> |

## 8. Milestones and Implementation Plan

| Item | Document | Status and meaning of dates |
|---|---|---|
| Roadmap | <link> | <for example: DRAFT, proposed targets, not approved delivery commitments> |
| Milestones | <link> | <status> |

## 9. Tasks and Acceptance Criteria

Where tasks live, how an ID is registered, and where the acceptance criteria are. Work is not accepted because code, a commit, a merged PR or a local test exists.

## 10. Status Reporting and Program Integration

Status file and schema version, the tool that writes it, how kritva-program consumes it. State the four things apart: execution (what the repository reports), evidence (commit, result and scope), acceptance (decided by the acceptance authority, not by this repository's report) and release readiness (the gates). A generated view is a derived snapshot that can lag its inputs. A repository that reports to kritva-program sends facts only and claims no approval or credit.

## 11. Build, Test, Regression and Validation

| Check | Command | Effect | Runs in CI? | Expected |
|---|---|---|---|---|
| <check> | `<command>` | check | <yes / no> | <result> |

A test that is not implemented is listed as not implemented, never as passing.

## 12. Git Workflow and Review

This repository's approved convention: branch rule, commit format, PR requirements, required checks, merge method. If the Kritva commit standard has been formally adopted for this repository, say so and follow its current specification (see kritva-program v2/planning/ACCEPTANCE_STANDARD.md section 4); if not, say that and give the rule that applies.

## 13. Safety and Security

Safety requirements and open gates (hardware repositories). The route for reporting a vulnerability (link SECURITY.md, or write `Not yet defined` and name the owner who will define it); never ask for details of an unfixed vulnerability in a public issue or PR. Secrets. State that software tests do not prove physical safety.

For a hardware, firmware or mechanical repository add: the statement that software checks, calculations and simulation do not prove physical safety or design acceptance; an open-gate summary table (gate, activity controlled, authority and status, evidence required, approver, prohibited while open); and the evidence scope for any validation claim (README_STANDARD section 8). Do not call a device or design validated or safe from software evidence; describe a future validated unit as conditional on the physical tests and gates. If the reporting route has not been verified, write `Reporting route: not yet verified`, name the owner and give the minimal safe first-contact instruction.

## 14. Release and Versioning

Version scheme, tags, required checks and approvals, changelog, known limitations.

## 15. Ownership and Escalation

Owner, reviewers, how a blocker is raised.

## 16. Related Repositories and References

Upstream, downstream and integration repositories.

## 17. License

<License name>. See [LICENSE](LICENSE).
