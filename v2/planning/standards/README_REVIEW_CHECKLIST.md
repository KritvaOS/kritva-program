# Kritva README Review Checklist

| Property | Value |
|---|---|
| Document ID | KOS-STD-README-CHECK |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Checklist |
| Status | PROPOSED (pilot in kritva-program, D-055, revised by audit round 1, D-056) |
| Authority | REFERENCE: applies [README_STANDARD.md](README_STANDARD.md) |

Run the machine check first, then review the rest by hand.

```bash
python3 scripts/docs/check_readme.py README.md      # or: make readme_check
```

A PASS means the implemented structural checks passed (metadata fields, section keywords, local file links, leftover placeholders). It does not show semantic completeness, that a command works, that an external URL is reachable, that a `#anchor` exists, that a link is relevant, that anything is approved, or that the content is accurate. The manual review below is a separate mandatory step.

## Identity and scope

- [ ] Name, purpose and repository type are accurate.
- [ ] Visibility Class and GitHub Setting are separate fields. The class is backed by a decision and a future-private repository says PRIVATE. The GitHub setting is dated, and a temporary difference says why.
- [ ] The right template was used for the class (private template for a PRIVATE class, whatever the GitHub setting).
- [ ] Technical Owner and Security Owner are shown, or linked, where they differ or where hardware safety, credentials, private data or security gates apply.
- [ ] What the repository owns and does not own is stated.
- [ ] Owner is named.

## Architecture and documents

- [ ] The architecture overview matches the detailed document it links.
- [ ] Milestones, tasks and acceptance criteria are linked, or say `Not yet defined`.
- [ ] Structure and document tables show each file's label and, where known, its status (DRAFT, SKELETON, PROPOSED, APPROVED). A skeleton or draft is not presented as finished. A mixed directory is labelled MIXED.
- [ ] Dependencies say whether each is ESTABLISHED, PROPOSED, PLANNED or UNVERIFIED.

## Tools and validation

- [ ] Every command was run in this repository and works.
- [ ] Each command is labelled by effect; any that modifies, merges, deploys or publishes has a warning and a preview option where one exists.
- [ ] Important external links and `#anchor` fragments were checked by hand (the script does not).
- [ ] Which checks run in CI, and which need hardware or an external service, is stated.
- [ ] A test that is not implemented is not shown as passing.

## Status and governance

- [ ] Status reporting and schema are described.
- [ ] Execution, evidence, acceptance and release readiness are not merged into one claim (standard section 7). Evidence scope is stated; a generated view is called a snapshot.
- [ ] Roadmap and milestone pointers state the plan's status and what its dates mean.
- [ ] A repository that reports to kritva-program sends facts only and claims no approval or credit.
- [ ] Proposed and approved decisions are not confused.
- [ ] Open safety gates are visible (hardware repositories).

## Git

- [ ] Commit format and merge method are this repository's approved rules. The Kritva commit standard is described as adopted only where it is.
- [ ] No weaker rule replaces a stricter approved one.

## Quality

- [ ] No stale numbers (counts, percentages, gate states).
- [ ] No duplicate of a document that owns the detail.
- [ ] No secrets, private infrastructure or confidential assessments (public README).
- [ ] A vulnerability reporting route is given, or marked `Not yet defined` with its owner.
- [ ] License matches the repository's real license.

## Result

Reviewer, date, repository and commit reviewed, and findings go in the pull request. Checking this list does not approve the repository: the owner records approval.
