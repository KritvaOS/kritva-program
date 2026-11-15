# Engineering contract compliance report (KRP-ENG-001)

Generated 2026-11-15T15:37:49Z by `tools/engineering_compliance.py` from the default branch of each repository on GitHub. It records facts only; it is not an acceptance decision. Acceptance is the owner's approval record in `v2/tracking/approvals.json`.

| Repository | Default branch head | Agent file | commit-message-check | secret-scan | readme-check | pr-acceptance-gate | unit-tests | Required checks on the default branch |
|---|---|---|---|---|---|---|---|---|
| kritva-program | `da8d6db` | AGENTS.md | yes | yes | yes | yes | yes | commit-message-check, pr-acceptance-gate, secret-scan, status-validate, tag-policy-check, unit-tests |
| kritva-core | `59335f8` | AGENTS.md | yes | yes | yes | no | no | commit-message-check, secret-scan, source-header-check, status-report-check |
| kritvaos-community | `c35ddb7` | AGENTS.md | yes | yes | yes | no | no | commit-message-check, secret-scan, source-header-check, status-report-check |
| kritva-sense | `a1259e5` | AGENTS.md | yes | yes | yes | yes | yes | commit-message-check, pr-acceptance-gate, progress-check, readme-check, secret-scan, unit-tests |
| kritva-mind | `29b8c4f` | AGENTS.md | yes | yes | yes | yes | yes | commit-message-check, pr-acceptance-gate, readme-check, secret-scan, unit-tests |
| kritva-motion | `5d7f36f` | AGENTS.md | yes | yes | yes | yes | yes | commit-message-check, pr-acceptance-gate, progress-check, readme-check, secret-scan, unit-tests |
| kritva-skill | `83d7a46` | AGENTS.md | yes | yes | yes | yes | no | commit-message-check, pr-acceptance-gate, readme-check, secret-scan |

Core engineering contract pin file `docs/development/ENGINEERING_CONTRACT.pin.json`: present.

## Commit checker drift (body hash against the kritva-program copy)

| Repository | check_commit_format.py | check_commit_messages.py |
|---|---|---|
| kritva-program | 965266c1c3df matches base | 9bf12734ce24 matches base |
| kritva-core | 965266c1c3df matches base | 9bf12734ce24 matches base |
| kritvaos-community | 965266c1c3df matches base | 9bf12734ce24 matches base |
| kritva-sense | 965266c1c3df matches base | 9bf12734ce24 matches base |
| kritva-mind | 965266c1c3df matches base | 9bf12734ce24 matches base |
| kritva-motion | 965266c1c3df matches base | 9bf12734ce24 matches base |
| kritva-skill | 965266c1c3df matches base | 9bf12734ce24 matches base |

## Differences to read before approving

- None in the agent file, commit-message-check and secret-scan checks.
- `no` in the pr-acceptance-gate, unit-tests or readme-check columns is not itself a gap: the owner decisions D-061 and PD-018 require the PR gate in the four capability repositories (Sense, Mind, Motion, Skill) and the program, and the commit standard in Core and Community. Read the column against those decisions.
- A repository's default branch can move after this report; the head commit column says what was read.
