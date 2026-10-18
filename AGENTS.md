# Kritva Program Agent Instructions

These instructions apply to the `kritva-program` repository, the program's single source of truth for decisions, baseline, approvals, status and tooling. Engineering repositories hold the code; this one does not.

## Authority

- Dinesh (owner and Security Owner) decides. Advice from agents or other AI tools is advisory only.
- `v2/DECISIONS.md` is the decision log. It is append-only: add a row or update the status and consequences of an existing row with evidence, but do not delete or rewrite a decision's meaning.

## What agents must not change without an owner decision

- `v2/tracking/baseline.json`, `v2/tracking/approvals.json` and `v2/tracking/gate_closures.json`. Credit comes only from approved baseline tasks with passing evidence; a repo edit never creates credit.
- The copies under `sources/`. They are refreshed from each repository's `status/status.json` by the refresh workflow or an owner-approved change.
- Open safety gates and the mechanical HOLD.

## Status semantics

- `v2/tracking/planning_inventory.json` is PLANNING_ONLY: it carries no weights and no credit.
- `v2/tracking/repo_readiness.json` is display only. It never changes credit, baseline or approvals. A check is PASS only with evidence at a recorded commit; owner statements are ATTESTED, not verified. `owner_signoff` stays DECISION until Dinesh authorises it.
- Claude and other agents cannot read GitHub rulesets or settings; do not record them as verified.

## Validation before a pull request

    python3 -m unittest discover -s tests
    python3 tools/consolidate_status.py --sources-dir sources --check
    python3 tools/check_planning_inventory.py . --verify-sources <sources-dir>   # when the inventory changes

When `README.md` or a file under `v2/planning/standards/` changes, run `make readme_check` (D-055): it checks the metadata block, the section topics and every local link. Keep the README a navigation page: link the document that owns a fact instead of copying it, and do not write task counts, percentages or gate states into it.

Regenerate `v2/tracking/consolidated_status.json`, `STATUS_VIEW.md` and `STATUS_DETAIL.md` and the generated files in `v2/planning/` (V2_MILESTONE_PLAN.md, V2_REPO_PLAN.md, PENDING_DECISIONS.md, PENDING_REVIEWS.md) with `tools/consolidate_status.py` after changing any tracking or planning input; do not edit them by hand. The V2 plan under `v2/planning/` is a planning layer: never put its milestones into `baseline.json`, never give them weights or credit, and keep proposed dates labelled PROPOSED until the owner approves them.

## Secrets and data

- Never commit credentials, tokens, private keys, production data or personal data. Use obviously fake values in examples and mark them as such.
- If a secret is committed by mistake, tell the Security Owner (Dinesh, D-032) at once. Removing it in a later commit does not make it safe; it must be revoked or rotated.
- The `secret-scan` workflow (gitleaks) runs on every push and pull request. Do not add allowlist entries to silence it; propose them to the owner with the reason.

## Commits and pull requests

- Work on a branch and open a pull request. Do not push to `main`. Do not force-push shared branches or rewrite history without the owner's explicit approval.
- Commit format (D-053): `type(scope): summary` with one `Task:` or `Tasks:` footer (`Tasks: None (reason)` only on docs or chore); see v2/planning/ACCEPTANCE_STANDARD.md section 4. Merge method is a merge commit. PRs use `.github/PULL_REQUEST_TEMPLATE.md`.
- Do not add `Claude-Session:` or session-URL trailers to commit messages or pull request descriptions. The `commit-message-check` workflow rejects them. A `Co-Authored-By:` line is allowed.
- `main` is protected by a ruleset that requires `secret-scan`, `commit-message-check` and Code Owner review (owner statement, D-040; not independently verified). With one owner, the PR author cannot self-approve: ask the owner to merge using the bypass or add a second reviewer.

- Pull requests are judged by the report-only `pr-acceptance-gate` (D-045, `scripts/pipeline/pr_gate.py`). It reports REJECT, NEEDS_HUMAN or APPROVE and approves, merges and changes nothing. Only the owner runs `make pr_check`, which can submit an approving review (D-046); agents use `DRY=1`. Do not edit the gate, its config or the protected paths to make a PR pass; changes there need the owner.

## When unsure

Say what you do not know and ask the owner. Do not invent evidence, test results, hardware behaviour or approvals, and do not claim a check passed unless you ran it.
