# Engineering contract compliance report (KRP-ENG-001)

Generated 2026-11-08T12:11:51Z by `tools/engineering_compliance.py` from the default branch of each repository on GitHub. It records facts only; it is not an acceptance decision. Acceptance is the owner's approval record in `v2/tracking/approvals.json`.

| Repository | Default branch head | Agent file | commit-message-check | secret-scan | readme-check | pr-acceptance-gate | unit-tests | Required checks on the default branch |
|---|---|---|---|---|---|---|---|---|
| kritva-program | `5c435d7` | AGENTS.md | yes | yes | yes | yes | yes | commit-message-check, secret-scan, status-validate |
| kritva-core | `8ac173f` | AGENTS.md | yes | yes | yes | no | no | commit-message-check, secret-scan, source-header-check, status-report-check |
| kritvaos-community | `87007e8` | AGENTS.md | yes | yes | yes | no | no | source-header-check, status-report-check |
| kritva-sense | `6a10cac` | AGENTS.md | yes | yes | yes | yes | yes | commit-message-check, pr-acceptance-gate, readme-check, secret-scan, unit-tests |
| kritva-mind | `beb9fa1` | AGENTS.md | yes | yes | yes | yes | yes | commit-message-check, pr-acceptance-gate, readme-check, secret-scan |
| kritva-motion | `5c52ae7` | AGENTS.md | yes | yes | yes | yes | yes | commit-message-check, pr-acceptance-gate, readme-check, secret-scan, unit-tests |
| kritva-skill | `5c04151` | AGENTS.md | yes | yes | yes | yes | no | commit-message-check, pr-acceptance-gate, readme-check, secret-scan |

Core engineering contract pin file `docs/development/ENGINEERING_CONTRACT.pin.json`: present.

## Differences to read before approving

- None in the agent file, commit-message-check and secret-scan checks.
- `no` in the pr-acceptance-gate, unit-tests or readme-check columns is not itself a gap: the owner decisions D-061 and PD-018 require the PR gate in the four capability repositories (Sense, Mind, Motion, Skill) and the program, and the commit standard in Core and Community. Read the column against those decisions.
- A repository's default branch can move after this report; the head commit column says what was read.
