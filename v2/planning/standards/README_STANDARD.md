# Kritva Repository README Standard

| Property | Value |
|---|---|
| Document ID | KOS-STD-README |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Standard |
| Status | PROPOSED (pilot in kritva-program, D-055); becomes APPROVED when the owner records it |
| Owner | Dinesh (program owner) |
| Authority | AUTHORITATIVE for README layout; ChatGPT review is advisory only |
| Related | [README_TEMPLATE_PUBLIC.md](README_TEMPLATE_PUBLIC.md), [README_TEMPLATE_PRIVATE.md](README_TEMPLATE_PRIVATE.md), [DOCUMENT_HEADER_STANDARD.md](DOCUMENT_HEADER_STANDARD.md), [README_REVIEW_CHECKLIST.md](README_REVIEW_CHECKLIST.md), [README_MIGRATION_PLAN.md](README_MIGRATION_PLAN.md) |

## 1. Purpose

Every KritvaOS repository has a root `README.md` that works as its entry point and navigation map. A developer, intern, reviewer or automated agent who opens any repository should reach its purpose, architecture, owner, dependencies, plans, tasks, acceptance rules, tools, status reporting and Git rules from that one file.

The README explains the repository and links to the documents that own the detail. It does not copy architecture specifications, task lists, status numbers or acceptance criteria. A second copy of a fact goes stale; a link does not.

## 2. Rules

1. **Navigation hub.** Link to the authoritative document; do not duplicate it.
2. **Existing files only.** A link points to a file or directory that exists on the default branch. A document that is planned but not written is listed as `Not yet defined` with no link. `scripts/docs/check_readme.py` fails on a link that does not resolve.
3. **Real commands only.** Every command in the README exists in that repository and has been run. A command is never copied from another repository without being checked.
4. **No stale numbers.** Task counts, progress percentages, test counts and gate states are not written into the README. Point to the generated status view.
5. **Execution is not acceptance.** The README never implies that work is done because code exists, a commit exists, a PR merged, a local test passed or a status file says PASS. The repository's acceptance process decides. Where the repository reports into kritva-program, the README keeps reported execution, evidence, accepted progress and release readiness apart.
6. **Unknown stays unknown.** An unverified fact is labelled `UNVERIFIED`, `PROPOSED`, `PLANNED` or `ATTESTED`. It is not written as established. A test that is not implemented is not shown as passing.
7. **Safety is not software.** A repository that moves hardware states its open safety gates and says that software tests and simulation do not prove physical safety.
8. **No secrets.** Private visibility does not make credentials, tokens or keys safe to commit.
9. **Stricter rule wins.** A repository's own approved rule (for example its `AGENTS.md`, an acceptance standard or a safety gate) takes precedence over this standard when it is stricter. A conflict is resolved in writing, in section 9, never by silently replacing an approved rule.

## 3. Document classification

Each important file or directory in the README's structure and document tables carries one of these labels.

| Label | Meaning | Edit by hand? |
|---|---|---|
| AUTHORITATIVE | Owns a decision, requirement or process | Yes, under the change rules of that document |
| INPUT | Read by a tool or workflow (records, task files, configuration) | Yes, then regenerate |
| GENERATED | Written by a tool from inputs | No: change the inputs or the tool |
| SNAPSHOT | A committed copy of facts owned by another repository | No: refresh from the source |
| EVIDENCE | Supports a test, review, acceptance or release claim | Append only |
| REFERENCE | Background or navigation; governs nothing | Yes |

A label does not approve anything. A document marked PROPOSED stays proposed until the authorised approval process changes it.

## 4. Repository metadata block

The README starts with the title, a one-sentence description and this table. Fields are the same in every repository.

| Field | Values and rule |
|---|---|
| Project | `KritvaOS` |
| Repository | `KritvaOS/<name>` |
| Repository Type | Program, Platform, Library, Capability, Service, Firmware, Mechanical, Tooling or Documentation |
| Current Visibility | `PUBLIC` or `PRIVATE`: the GitHub setting as last verified, with the date |
| Target Visibility | `PUBLIC` or `PRIVATE`: the approved end state, with the decision ID |
| Lifecycle Status | `PLANNING`, `ACTIVE`, `ON_HOLD` or `ARCHIVED`. Independent of visibility |
| Repository Owner | Person or team |
| Architecture | Link, or `Not yet defined` |
| Milestones | Link, or `Not yet defined` |
| Tasks | Link, or `Not yet defined` |
| Acceptance Criteria | Link, or `Not yet defined` |
| Status Reporting | Link, or `Not yet defined` |
| License | Link to `LICENSE` and the license's real name. Do not copy a license identifier from another repository |

Visibility rules:

- Current and Target are separate fields so a repository can be public today and private later without rewriting its README.
- The header is documentation. It is not proof of the GitHub setting, which tooling in this program cannot read. The owner attests the setting, and the readiness record shows it as ATTESTED.
- **Temporary public review (D-028, D-037).** Every repository is currently public so the architecture can be reviewed and aligned, including by external audit. This also holds for a repository that is private by design: it is made temporarily public for alignment and review, then returned to private. Such a repository records `Current Visibility: PUBLIC`, `Target Visibility: PRIVATE` and the planned return date. Making a repository private or public again is an owner action recorded in the decision log.
- Planned end state at the time of writing: kritva-program, kritva-raas and the five kritva-actuator repositories return to private. Other repositories use their own approved target. A repository with no approved target writes `Target Visibility: Not yet decided` and links the pending decision.

## 5. Section order

The common baseline for every repository. A section that does not apply says `Not applicable` and why; do not delete it and do not write an empty section.

| # | Section | Public | Private |
|---|---|---|---|
| 1 | Title, summary and metadata block | required | required |
| 2 | Purpose and scope (what it owns, what it does not) | required | required |
| 3 | Position in the KritvaOS ecosystem | required | required |
| 4 | Architecture overview, with links to the detailed documents | required | required |
| 5 | Documents to read first | required | required |
| 6 | Repository structure and file responsibilities (with classification) | required | required |
| 7 | Tool and development workflow (toolchain table, setup, build) | required | required |
| 8 | Dependencies and interfaces (upstream, downstream, status of each) | required | required |
| 9 | Milestones and implementation plan | link to roadmap | required |
| 10 | Tasks and acceptance criteria | link | required |
| 11 | Status reporting and program integration | summary | required |
| 12 | Build, test, regression and validation | required | required |
| 13 | Git workflow and contribution rules (commit format, PR, merge) | required | required |
| 14 | Safety and security | required where it applies | required where it applies |
| 15 | Release and versioning | required | required |
| 16 | Ownership and support | required | required |
| 17 | Related repositories and references | required | required |
| 18 | License | required | required |

A public README helps an outside user understand and use the project. It does not expose internal planning detail, private infrastructure, confidential assessments or credentials. A private README may carry more internal navigation.

## 6. Compliance levels

| Level | Applies to | Adds |
|---|---|---|
| 1. Common | Every repository | Sections 1 to 18 above |
| 2. Domain | By repository type | Software: APIs, data formats, service dependencies. Firmware: MCU, toolchain, fault handling, hardware validation. Mechanical: requirements, BOM, sizing, verification. Each lists its open safety gates |
| 3. Program | kritva-program only | Baseline, approvals, gates, source snapshots, consolidated status, program-level acceptance |

kritva-program uses a program layout in its own README (it adds governance, program architecture, gates and generated-report sections and still covers every topic of section 5) and keeps `v2/README.md` as the detailed dashboard. The root README does not duplicate the dashboard.

## 7. Source and document headers

- Source files keep the header each repository's lint already enforces (for example the SPDX block checked by `check_source_headers.py` in core, community and raas). This standard adds no second source-header block.
- Detailed Markdown documents use the document header in [DOCUMENT_HEADER_STANDARD.md](DOCUMENT_HEADER_STANDARD.md).

## 8. Automated check

`python3 scripts/docs/check_readme.py README.md` (also `make readme_check`) verifies the structure that a machine can verify:

- the metadata block has every field in section 4;
- every topic in section 5 appears as a heading (matched by keyword, not exact title); order is a review item;
- every relative link resolves to a file or directory;
- no placeholder text such as `<repository-name>` or `TODO` remains.

It cannot judge whether an architecture is right or an acceptance criterion is adequate. That is review work ([README_REVIEW_CHECKLIST.md](README_REVIEW_CHECKLIST.md)).

## 9. Exceptions

A repository that cannot follow this standard records the deviation here, with the repository, the rule, the reason, the approving decision and a review date. No exception is recorded yet.

| Repository | Rule | Reason | Decision | Review date |
|---|---|---|---|---|
| (none) | | | | |
