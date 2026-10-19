# Kritva README Review Checklist

| Property | Value |
|---|---|
| Document ID | KOS-STD-README-CHECK |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Checklist |
| Status | PROPOSED (pilot in kritva-program, D-055, revised by audit rounds 1 to 4, D-056, D-057 and D-058) |
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
- [ ] Dependencies say whether each is ESTABLISHED, PROPOSED, PLANNED or UNVERIFIED, and which kind each is (program ordering, submodule, build or runtime, governance or status reporting). An ordering in a plan is not an integration.
- [ ] Principal capabilities and significant tree entries carry an implementation state (IMPLEMENTED, PLANNED, PROPOSED, REFERENCE-ONLY, EVIDENCE, NOT YET IMPLEMENTED). The labels were cross-checked against the source files, scripts, submodule pointers, CI and test results. A target architecture or a folder map does not read as an inventory of what exists.
- [ ] AUTHORITATIVE says what the document is authoritative for, and each row shows the role first and the status the document itself declares after it; an AUTHORITATIVE label on a PROPOSED or OPEN document was not read as an approved baseline.

## Tools and validation

- [ ] Every command was run in this repository and works.
- [ ] Each command is labelled by effect; any that modifies, merges, deploys or publishes has a warning and a preview option where one exists. The labels were compared with the real Makefile or task runner, including cleanup and generate targets. A blanket claim such as "none modifies state" covers only a stated, inspected set of commands.
- [ ] CI checks are documented by workflow with trigger and command, apart from the local Makefile targets, and every umbrella claim ("checks cover X", "runs on every change") was compared with the workflow definitions. `make check` is not treated as shorthand for all of CI.
- [ ] The repository's own checker has regression tests at the audited commit (fenced blocks, inline code, relative links, placeholders, metadata), or demonstrably uses the common implementation; the invocation and test paths exist.
- [ ] Important external links and `#anchor` fragments were checked by hand (the script does not).
- [ ] Which checks run in CI, and which need hardware or an external service, is stated.
- [ ] A test that is not implemented is not shown as passing.

## Status and governance

- [ ] Status reporting and schema are described.
- [ ] Execution, evidence, acceptance and release readiness are not merged into one claim (standard section 7). Evidence scope is stated; a generated view is called a snapshot.
- [ ] Roadmap and milestone pointers state the plan's status and what its dates mean.
- [ ] A repository that reports to kritva-program sends facts only and claims no approval or credit.
- [ ] Proposed and approved decisions are not confused.
- [ ] Open safety gates are visible (hardware repositories) in an open-gate summary: the activity each gate controls, its authority and status, the evidence it requires, who approves it and what is prohibited while it is open. Lifting a hold is not a design approval.
- [ ] Hardware repositories state that software checks, calculations and simulation do not prove physical safety, and none of the wording calls a device or design "validated" or "safe" on the strength of software, calculation or simulation. A future validated unit is described as conditional on the physical tests and gates.
- [ ] Evidence is stated by type (software test, calculation, simulation, bench measurement, independently accepted physical test) with revision or configuration, procedure or command, result and scope. A generated report or a passing subset of tests does not approve a gate or release.
- [ ] A submodule or child repository is described by its real state: configured, pointer recorded, checked out, verified. A pointer is not described as verified unless the README names the commit that was checked.
- [ ] For a child repository, each gate-summary row names the controlling parent record, says whether it is the child's contribution or the complete gate, matches that record's prohibited activities, and does not imply that a child-level check closes the parent gate.

## Git

- [ ] Commit format and merge method are this repository's approved rules, with one controlling contract named, the validator or workflow that enforces it (or a statement that none does) and the adoption status of the Kritva commit standard. A non-adopted rule is advisory and is not offered as a second mandatory format. The README, AGENTS.md and CONTRIBUTING.md agree. Where more than one subject form is allowed, one controlling statement names them, what CI enforces and that local style checks are advisory.
- [ ] No weaker rule replaces a stricter approved one.

## Quality

- [ ] No stale numbers (counts, percentages, gate states).
- [ ] No duplicate of a document that owns the detail.
- [ ] No secrets, private infrastructure or confidential assessments (public README).
- [ ] A vulnerability reporting route is given and was verified as monitored and usable, or is marked `not yet verified` (or `Not yet defined`) with its owner and the minimal safe first-contact instruction. A platform feature such as private vulnerability reporting is not described as available until its setting has been checked.
- [ ] License matches the repository's real license.

## Result

The pull request reports two results separately: the structural check (a machine result) and the manual review (this list, including the hardware items for a hardware repository).

Reviewer, date, repository and commit reviewed, and findings go in the pull request. Checking this list does not approve the repository: the owner records approval.
