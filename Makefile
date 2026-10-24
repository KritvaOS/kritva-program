# kritva-program Makefile: program-level helpers. Nothing here merges a PR.
#
#   make pr_check all                              sweep every repo's open PRs through the gate; approve the clear ones (D-046)
#   make pr_check REPO=kritva-sense PR=7           one PR
#   make pr_check REPO=kritva-sense                every open PR of one repo
#   make pr_check all REPOS="kritva-sense kritva-mind"   only these repos
#   make pr_check all DRY=1                        report only, no review is submitted
#
#   make ship TAR=~/Downloads/x.tar.gz BRANCH=feat/x   open, check, merge and sync one PR per repo in the tarball (dependency order)
#   make ship PATCHES=/tmp/rr BRANCH=feat/x ONLY=kritva-program   an extracted folder; ONLY limits the repos; add DRY=1 to preview
#
#   make merge REPO=kritva-sense PR=7                  merge a PR you pushed yourself: gate, checks, --admin merge, sync local main
#   make merge REPO=kritva-sense PR=7 DRY=1            everything except the merge
#
#   make readme_check                              check README.md against the README standard (D-055); README=path for another file
#
# GNU make takes "--repo" and "--pr" as its own options, so use REPO= and PR=.
# The script can also be called directly: python3 scripts/pipeline/pr_check.py --repo kritva-sense --pr 7

# Repositories that `make pr_check all` reviews. Edit this list to add or drop a repo; each name must be a repo_id in
# v2/planning/repo-pipeline.json (a test keeps this list and the manifest in step).
# A phase HOLD in the manifest (the actuator sub-repos, P6) delays milestones, not PR review, so those repos are listed too.
REPOS := \
	kritva-program \
	kritva-core \
	kritvaos-community \
	kritva-sense \
	kritva-motion \
	kritva-mind \
	kritva-skill \
	kritva-actuator \
	kritva-actuator-embedded \
	kritva-actuator-s \
	kritva-actuator-m \
	kritva-actuator-l

.PHONY: help pr_check all ship merge readme_check

help:
	@sed -n '3,16p' Makefile

# "all" is only a word after pr_check, so it must not build anything.
all:
	@$(if $(filter pr_check,$(MAKECMDGOALS)),:,$(MAKE) --no-print-directory help)

pr_check:
	@python3 scripts/pipeline/pr_check.py $(if $(filter all,$(MAKECMDGOALS)),all --repos "$(REPOS)") $(if $(REPO),--repo $(REPO)) $(if $(PR),--pr $(PR)) $(if $(DRY),--no-approve)

# Wraps scripts/pipeline/ship-prs.sh (always --admin, manifest order). Options: TAR or PATCHES, BRANCH, ONLY, BODY, TAG + MILESTONE, DRY=1.
ship:
	@scripts/pipeline/ship.sh $(if $(BRANCH),--branch "$(BRANCH)") $(if $(TAR),--tar "$(TAR)") $(if $(PATCHES),--patches "$(PATCHES)") $(if $(ONLY),--only "$(ONLY)") $(if $(BODY),--body "$(BODY)") $(if $(TAG),--tag "$(TAG)" --milestone "$(MILESTONE)") $(if $(DRY),--dry)

# Merge an already open PR (see scripts/pipeline/merge-pr.sh). Options: REPO, PR, DRY=1, NOADMIN=1.
merge:
	@scripts/pipeline/merge-pr.sh $(if $(REPO),--repo "$(REPO)") $(if $(PR),--pr "$(PR)") $(if $(DRY),--dry) $(if $(NOADMIN),--no-admin)

# README structure, metadata and local links (v2/planning/standards/README_STANDARD.md).
readme_check:
	@python3 scripts/docs/check_readme.py $(or $(README),README.md)
