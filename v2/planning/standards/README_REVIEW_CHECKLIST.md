# Kritva README Review Checklist

| Property | Value |
|---|---|
| Document ID | KOS-STD-README-CHECK |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Checklist |
| Status | PROPOSED (pilot in kritva-program, D-055) |
| Authority | REFERENCE: applies [README_STANDARD.md](README_STANDARD.md) |

Run the machine check first, then review the rest by hand.

```bash
python3 scripts/docs/check_readme.py README.md      # or: make readme_check
```

A PASS from the script means the structure is present and the links resolve. It does not mean the content is right.

## Identity and scope

- [ ] Name, purpose and repository type are accurate.
- [ ] Current and Target Visibility are separate, dated and, for Target, backed by a decision.
- [ ] What the repository owns and does not own is stated.
- [ ] Owner is named.

## Architecture and documents

- [ ] The architecture overview matches the detailed document it links.
- [ ] Milestones, tasks and acceptance criteria are linked, or say `Not yet defined`.
- [ ] Structure table labels the important files (AUTHORITATIVE, INPUT, GENERATED, SNAPSHOT, EVIDENCE, REFERENCE).
- [ ] Dependencies say whether each is ESTABLISHED, PROPOSED, PLANNED or UNVERIFIED.

## Tools and validation

- [ ] Every command was run in this repository and works.
- [ ] Which checks run in CI, and which need hardware or an external service, is stated.
- [ ] A test that is not implemented is not shown as passing.

## Status and governance

- [ ] Status reporting and schema are described.
- [ ] Execution, evidence, acceptance and release readiness are not merged into one claim.
- [ ] Proposed and approved decisions are not confused.
- [ ] Open safety gates are visible (hardware repositories).

## Git

- [ ] Commit format and merge method match the repository's actual rules.
- [ ] No weaker rule replaces a stricter approved one.

## Quality

- [ ] No stale numbers (counts, percentages, gate states).
- [ ] No duplicate of a document that owns the detail.
- [ ] No secrets, private infrastructure or confidential assessments (public README).
- [ ] License matches the repository's real license.

## Result

Reviewer, date, repository and commit reviewed, and findings go in the pull request. Checking this list does not approve the repository: the owner records approval.
