# Kritva Program Security Policy

**Repository:** `kritva-program`
**Security Owner:** Dinesh (program decision D-032)

## 1. Scope

This policy covers reproducible security vulnerabilities in the Kritva program records (decisions, baseline, approvals, status and tooling): code, tooling, documentation, data and CI configuration maintained in this repository.

## 2. Do not disclose unfixed vulnerabilities publicly

This repository is currently public as a temporary measure (D-028) and is planned to return to private (D-037). Whatever its visibility at the time, please do not copy details of an unpatched vulnerability into a public issue, pull request, discussion or post, or into any other public place.

## 3. Reporting

Tell the Security Owner directly through your existing Kritva channel and ask for a private place to share the details; do not put details in the first message. If GitHub private vulnerability reporting is enabled for this repository (Security tab, "Report a vulnerability"), you may use it instead.

Include: the affected file, component or commit, a description, steps to reproduce, observed and expected behaviour, the potential impact, and any mitigation you know of. Please leave out personal, customer, credential or production data.

## 4. What to expect

The Security Owner will make reasonable efforts to acknowledge a valid report, reproduce and assess it, coordinate a fix or mitigation, and agree disclosure timing with the reporter. Response times depend on severity and maintainer availability; this policy sets no guaranteed deadlines.

## 5. Secrets

Never commit credentials, tokens, private keys or production data. If one is committed by mistake, tell the Security Owner at once so that it can be revoked or rotated; removing it from a later commit does not make it safe.
