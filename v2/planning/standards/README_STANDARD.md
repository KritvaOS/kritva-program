# Kritva Repository README Standard

| Property | Value |
|---|---|
| Document ID | KOS-STD-README |
| Repository | `KritvaOS/kritva-program` |
| Document Type | Standard |
| Status | PROPOSED (pilot in kritva-program, D-055, revised by audit round 1, D-056); becomes APPROVED when the owner records it |
| Owner | Dinesh (program owner) |
| Authority | AUTHORITATIVE role for README layout (role, not approval). ChatGPT review is advisory only |
| Related | [README_TEMPLATE_PUBLIC.md](README_TEMPLATE_PUBLIC.md), [README_TEMPLATE_PRIVATE.md](README_TEMPLATE_PRIVATE.md), [DOCUMENT_HEADER_STANDARD.md](DOCUMENT_HEADER_STANDARD.md), [README_REVIEW_CHECKLIST.md](README_REVIEW_CHECKLIST.md), [README_MIGRATION_PLAN.md](README_MIGRATION_PLAN.md) |

## 1. Purpose

Every KritvaOS repository has a root `README.md` that works as its entry point and navigation map. A developer, intern, reviewer or automated agent who opens any repository should reach its purpose, architecture, owner, dependencies, plans, tasks, acceptance rules, tools, status reporting and Git rules from that one file.

The README explains the repository and links to the documents that own the detail. It does not copy architecture specifications, task lists, status numbers or acceptance criteria. A second copy of a fact goes stale; a link does not.

## 2. Rules

1. **Navigation hub.** Link to the authoritative document; do not duplicate it.
2. **Existing files only.** A link points to a file or directory that exists on the default branch. A document that is planned but not written is listed as `Not yet defined` with no link.
3. **Real commands only.** Every command in the README exists in that repository and has been run. A command is never copied from another repository without being checked. A command that modifies state, merges, publishes or deploys says so and shows a safe preview option where one exists (section 6).
4. **No stale numbers.** Task counts, progress percentages, test counts and gate states are not written into the README. Point to the generated status view.
5. **Status invariants.** Where a README covers status, acceptance or release, it keeps four things apart and never merges them into one flag, badge or percentage (section 7).
6. **Unknown stays unknown.** An unverified fact is labelled `UNVERIFIED`, `PROPOSED`, `PLANNED` or `ATTESTED`. A document that is a skeleton or draft is linked with that status beside it. A test that is not implemented is not shown as passing.
7. **Safety is not software.** A repository that moves hardware states its open safety gates and says that software tests and simulation do not prove physical safety.
8. **No secrets.** Private visibility does not make credentials, tokens or keys safe to commit.
9. **Stricter rule wins.** A repository's own approved rule (its `AGENTS.md`, an acceptance standard, a safety gate) takes precedence when it is stricter. A conflict is resolved in writing, in section 11, never by silently replacing an approved rule.
10. **Rules of another repository are not imposed.** A README states the convention this repository has approved. Where the Kritva commit standard has been formally adopted for the repository, it says so and follows the current specification; where it has not (see PD-019 in kritva-program), it says that instead.

## 3. Document classification and status

Each important file or directory in the structure and document tables carries a label (its role) and, where known, its lifecycle status.

| Label | Meaning | Edit by hand? |
|---|---|---|
| AUTHORITATIVE | Owns a decision, requirement or process | Yes, under the change rules of that document |
| INPUT | Read by a tool or workflow (records, task files, configuration) | Yes, then regenerate |
| GENERATED | Written by a tool from inputs | No: change the inputs or the tool |
| SNAPSHOT | A committed copy of facts owned by another repository | No: refresh from the source |
| EVIDENCE | Supports a test, review, acceptance or release claim | Append only |
| REFERENCE | Background or navigation; governs nothing | Yes |
| MIXED | A directory with files of several labels | Per file; list the principal files |

A label names a responsibility, not an approval. Status is `DRAFT`, `SKELETON`, `PROPOSED`, `APPROVED` or `DEPRECATED`, and is shown beside the label wherever it is known (`AUTHORITATIVE, PROPOSED`). A document is not approved because it is authoritative for its subject.

## 4. Repository metadata block

The README starts with the title, a one-sentence description and this table. The required fields are the same in every repository.

| Field | Values and rule |
|---|---|
| Project | `KritvaOS` |
| Repository | `KritvaOS/<name>` |
| Repository Type | Program, Platform, Library, Capability, Service, Firmware, Mechanical, Tooling or Documentation |
| Visibility Class | `PRIVATE` or `PUBLIC`: the class the owner approved for this repository, with the decision ID. A future-private repository says `PRIVATE`. If no class is approved yet, write `Not yet decided` and link the pending decision |
| GitHub Setting | `PUBLIC` or `PRIVATE`: the actual GitHub setting as last verified, with the date. When it differs from the class, say so and why (for example `PUBLIC, temporary, D-028`) |
| Lifecycle Status | `PLANNING`, `ACTIVE`, `ON_HOLD` or `ARCHIVED`. Independent of visibility |
| Repository Owner | Person or team |
| Architecture | Link, or `Not yet defined` |
| Milestones | Link, or `Not yet defined` |
| Tasks | Link, or `Not yet defined` |
| Acceptance Criteria | Link, or `Not yet defined` |
| Status Reporting | Link, or `Not yet defined` |
| License | Link to `LICENSE` and the license's real name. Do not copy a license identifier from another repository |

Optional rows, required when they apply: **Technical Owner** and **Security Owner**. Add them when the owners differ from the Repository Owner, or when the repository handles hardware safety, credentials, private user or customer data, or security gates. Where ownership is established in one place (CODEOWNERS, SECURITY.md), link that place instead of repeating a name.

### Visibility rules

- **The class decides the wording and the template.** A repository whose approved class is PRIVATE is written up as a private repository in every document and uses the private template, whatever its GitHub setting is today. The public template is for repositories whose approved class is PUBLIC.
- **The GitHub setting is an operational fact, not the class.** It is documentation, not proof: tooling in this program cannot read it, so it is ATTESTED by the owner (see `repo_readiness.json` in kritva-program).
- **Temporary public exposure is an owner decision, scoped to the repositories it names.** D-028 and D-037 in kritva-program record the current arrangement and the return date. A README does not generalise it to the whole organisation and does not repeat the return date; it links the decision or the readiness record that owns it. Other repositories keep their own approved class.
- **Audit access.** A future-private repository is reviewed through whatever access the owner approves. Making it temporarily public for review, and returning it to private, are separate owner actions tracked in the decision log. A repository does not need to be public for its README to be written, reviewed or marked done.
- Planned classes at the time of writing: kritva-program, kritva-raas and the five kritva-actuator repositories are future private. The authoritative source for every repository's class is the visibility decision and `v2/tracking/repo_readiness.json` in kritva-program, not this list.

## 5. Section order

The common baseline for every repository. A section that does not apply says `Not applicable` and why; do not delete it and do not write an empty section.

| # | Section | Public | Private |
|---|---|---|---|
| 1 | Title, summary and metadata block | required | required |
| 2 | Purpose and scope (what it owns, what it does not) | required | required |
| 3 | Position in the KritvaOS ecosystem | required | required |
| 4 | Architecture overview, with links to the detailed documents | required | required |
| 5 | Documents to read first | required | required |
| 6 | Repository structure and file responsibilities (label and status) | required | required |
| 7 | Tool and development workflow (toolchain table, setup, build) | required | required |
| 8 | Dependencies and interfaces (upstream, downstream, status of each) | required | required |
| 9 | Milestones and implementation plan | link | required |
| 10 | Tasks and acceptance criteria | link | required |
| 11 | Status reporting and program integration | summary | required |
| 12 | Build, test, regression and validation | required | required |
| 13 | Git workflow and contribution rules (this repository's approved convention) | required | required |
| 14 | Safety and security (with a reporting route) | required where it applies | required where it applies |
| 15 | Release and versioning | required | required |
| 16 | Ownership and support | required | required |
| 17 | Related repositories and references | required | required |
| 18 | License | required | required |

A public README helps an outside user understand and use the project. It does not expose internal planning detail, private infrastructure, confidential assessments or credentials. A private README may carry more internal navigation.

### Template mapping

| Baseline topic | Private template | Public template |
|---|---|---|
| 1 Title and metadata | title and table | title and table |
| 2 Purpose and scope | 1 | 1 |
| 3 Ecosystem | 2 | 2 |
| 4 Architecture | 3 | 3 |
| 5 Documents to read | 4 | 4 |
| 6 Structure | 5 | 5 |
| 7 Tools and workflow | 6 | 6 |
| 8 Dependencies | 7 | 7 |
| 9 Milestones | 8 | 8 (Roadmap) |
| 10 Tasks and acceptance | 9 | 9 |
| 11 Status reporting | 10 | 10 |
| 12 Validation | 11 | 11 |
| 13 Git workflow | 12 | 12 |
| 14 Safety and security | 13 | 13 |
| 15 Release | 14 | 14 |
| 16 Ownership | 15 | 15 |
| 17 Related repositories | 16 | 16 |
| 18 License | 17 | 17 |

A repository may use a different layout where its domain needs one, as long as every topic is covered and the README says where. `Not applicable` is allowed only with a reason.

## 6. Commands and effects

The tool and validation tables label each command by effect: **check** (read only), **generate** (writes files locally), **modify** (changes repository or remote state), **merge** or **deploy** or **publish** (changes shared state). A command with a non-local, destructive, privileged, merge, deploy or publish effect carries a one-line warning before it, names the permission or credential it needs (never the secret), and shows a dry run or preview option when one exists.

## 7. Status invariants

Wherever a README covers status, acceptance or release:

- **Execution** is the repository's reported implementation state.
- **Evidence** names the commit and the validation result behind a claim, and its scope. Evidence from a milestone-level run is not evidence from the task's own commit.
- **Acceptance** is decided by the repository's approved acceptance authority, not by the repository's own report.
- **Release readiness** is the result of the applicable gates.
- A status file or generated view never approves its own work, and a generated view is a derived snapshot that can lag its inputs.
- A repository that reports to kritva-program sends facts only. It does not claim central approval or program credit. A repository without central reporting documents its own acceptance process and does not imply that the program flow applies to it.
- A roadmap or milestone pointer states the plan's status and what its dates mean (for example `proposed targets, not approved delivery commitments`).

## 8. Compliance levels

| Level | Applies to | Adds |
|---|---|---|
| 1. Common | Every repository | Sections 1 to 18 above |
| 2. Domain | By repository type | Software: APIs, data formats, service dependencies. Firmware: MCU, toolchain, fault handling, hardware validation. Mechanical: requirements, BOM, sizing, verification. Each lists its open safety gates |
| 3. Program | kritva-program only | Baseline, approvals, gates, source snapshots, consolidated status, program-level acceptance |

kritva-program uses a program layout in its own README (it adds governance, program architecture, gates and generated-report sections and still covers every topic of section 5) and keeps `v2/README.md` as the detailed dashboard.

## 9. Source and document headers

- Source files keep the header each repository's lint already enforces (for example the SPDX block checked by `check_source_headers.py` in core, community and raas). This standard adds no second source-header block.
- Detailed human-maintained Markdown documents use the header in [DOCUMENT_HEADER_STANDARD.md](DOCUMENT_HEADER_STANDARD.md). Generated files and structured records keep their own schema and markers.

## 10. Automated check

`python3 scripts/docs/check_readme.py README.md` (also `make readme_check`) runs these structural checks and nothing else:

- the metadata block has every required field of section 4 and none is empty;
- every topic of section 5 appears as a heading (matched by keyword, so a broad match can pass; order is a review item);
- every relative Markdown link `[text](path)` points to an existing file or directory (the part after `#` is not checked, image links and absolute URLs are skipped);
- no placeholder text such as `<repository-name>` or `TODO` remains outside code (fenced blocks, inline code and lines indented by four spaces or a tab count as code, so an example commit message can show `<TASK-ID>`).

A PASS means those implemented checks passed. It does not show that the content is accurate or complete, that a command works, that an external URL is reachable, that a heading anchor exists, that a link is relevant, or that anything is approved. Those are review items in [README_REVIEW_CHECKLIST.md](README_REVIEW_CHECKLIST.md).

## 11. Exceptions

A repository that cannot follow this standard records the deviation here, with the repository, the rule, the reason, the approving decision and a review date. No exception is recorded yet.

| Repository | Rule | Reason | Decision | Review date |
|---|---|---|---|---|
| (none) | | | | |
