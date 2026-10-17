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

Regenerate `v2/tracking/consolidated_status.json` and `STATUS_VIEW.md` with `tools/consolidate_status.py` after changing any tracking input; do not edit them by hand.

## Secrets and data

- Never commit credentials, tokens, private keys, production data or personal data. Use obviously fake values in examples and mark them as such.
- If a secret is committed by mistake, tell the Security Owner (Dinesh, D-032) at once. Removing it in a later commit does not make it safe; it must be revoked or rotated.
- The `secret-scan` workflow (gitleaks) runs on every push and pull request. Do not add allowlist entries to silence it; propose them to the owner with the reason.

## Commits and pull requests

- Work on a branch and open a pull request. Do not push to `main`. Do not force-push shared branches or rewrite history without the owner's explicit approval.
- Use short imperative messages in the repository's existing style (`type(scope): summary`).
- Do not add `Claude-Session:` or session-URL trailers to commit messages or pull request descriptions. The `commit-message-check` workflow rejects them. A `Co-Authored-By:` line is allowed.
- `main` is protected by a ruleset that requires `secret-scan`, `commit-message-check` and Code Owner review (owner statement, D-040; not independently verified). With one owner, the PR author cannot self-approve: ask the owner to merge using the bypass or add a second reviewer.

## When unsure

Say what you do not know and ask the owner. Do not invent evidence, test results, hardware behaviour or approvals, and do not claim a check passed unless you ran it.
