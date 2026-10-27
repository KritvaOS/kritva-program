# kritva-program Makefile: program-level helpers.  Run `make` or `make help` for the command list.
#
# Lines starting with "##" are the help text. "##@ Name" starts a group, "## name: text" documents a target.
# GNU make takes "--repo" and "--pr" as its own options, so use REPO= and PR=. Add DRY=1 to preview most commands.
# Nothing here merges a PR except pr_land, ship and merge, which merge with --admin after the checks pass.
# The scripts can also be called directly (scripts/pipeline/*.sh --help, scripts/pipeline/pr_check.py --help).

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

.DEFAULT_GOAL := help
.PHONY: help all sync test regen verify readme_check pr_open pr_watch pr_land pr_check ship merge

##@ Everyday: from a handoff tarball to a merged PR (run in this clone)
## pr_open: tarball to PR: new branch, extract, test, commit, push, open the PR. TAR= BRANCH= MSG= [TASK=KRP-ENG-001] [DRY=1] [NOTEST=1]
## pr_watch: wait for the checks of the PR on the current branch.
## pr_land: merge the current branch's PR (--admin) after the checks pass, then back to an updated main. [DRY=1] [NOADMIN=1]
## sync: switch to main and fast-forward it from origin.
##   e.g.  make pr_open TAR=~/Downloads/x.tar.gz BRANCH=chore/x MSG="chore(x): what changed"
##         make pr_watch          then          make pr_land

##@ Checks and generated files
## test: run the whole test suite (python3 -m unittest).
## regen: regenerate the status JSON, STATUS_VIEW.md and STATUS_DETAIL.md from the inputs (writes files; commit them with the input change).
## verify: check that the committed status files match their inputs (reads only).
## readme_check: check README.md against the README standard (D-055); README=path for another file.

##@ Other repositories (D-046)
## pr_check all: sweep every repo's open PRs through the gate; approve the clear ones. Add DRY=1 to only report; REPOS="a b" limits the repos.
## pr_check REPO=x [PR=n]: one repo, or one PR.
## ship: open, check, merge and sync one PR per repo from a patch set. TAR= or PATCHES=, BRANCH=, [ONLY=repo] [DRY=1].
## merge REPO=x PR=n: merge a PR you pushed yourself in another repo: gate, checks, --admin merge, sync. [DRY=1]

help:  ## show this list
	@awk 'BEGIN{print "\nUsage: make <command> [VAR=value ...]"} \
	  /^##@ /{printf "\n%s\n", substr($$0,5); next} \
	  /^##   /{printf "      %s\n", substr($$0,6); next} \
	  /^## /{s=substr($$0,4); i=index(s,":"); printf "  %-22s %s\n", substr(s,1,i-1), substr(s,i+1)}' $(MAKEFILE_LIST); echo

# "all" is only a word after pr_check, so it must not build anything.
all:
	@$(if $(filter pr_check,$(MAKECMDGOALS)),:,$(MAKE) --no-print-directory help)

sync:
	@git checkout main && git pull --ff-only

test:
	@python3 -m unittest discover -s tests

regen:
	@python3 tools/consolidate_status.py --sources-dir sources

verify:
	@python3 tools/consolidate_status.py --sources-dir sources --check

# Wraps scripts/pipeline/pr-open.sh.
pr_open:
	@scripts/pipeline/pr-open.sh $(if $(TAR),--tar "$(TAR)") $(if $(BRANCH),--branch "$(BRANCH)") $(if $(MSG),--msg "$(MSG)") $(if $(TASK),--task "$(TASK)") $(if $(NOTEST),--no-test) $(if $(DRY),--dry)

pr_watch:
	@gh pr checks --watch

pr_land:
	@scripts/pipeline/pr-land.sh $(if $(DRY),--dry) $(if $(NOADMIN),--no-admin)

pr_check:
	@python3 scripts/pipeline/pr_check.py $(if $(filter all,$(MAKECMDGOALS)),all --repos "$(REPOS)") $(if $(REPO),--repo $(REPO)) $(if $(PR),--pr $(PR)) $(if $(DRY),--no-approve)

# Wraps scripts/pipeline/ship-prs.sh (always --admin, manifest order). Options: TAR or PATCHES, BRANCH, ONLY, BODY, TAG + MILESTONE, DRY=1.
ship:
	@scripts/pipeline/ship.sh $(if $(BRANCH),--branch "$(BRANCH)") $(if $(TAR),--tar "$(TAR)") $(if $(PATCHES),--patches "$(PATCHES)") $(if $(ONLY),--only "$(ONLY)") $(if $(BODY),--body "$(BODY)") $(if $(TAG),--tag "$(TAG)" --milestone "$(MILESTONE)") $(if $(DRY),--dry)

# Merge an already open PR of another repo (see scripts/pipeline/merge-pr.sh). Options: REPO, PR, DRY=1, NOADMIN=1.
merge:
	@scripts/pipeline/merge-pr.sh $(if $(REPO),--repo "$(REPO)") $(if $(PR),--pr "$(PR)") $(if $(DRY),--dry) $(if $(NOADMIN),--no-admin)

# README structure, metadata and local links (v2/planning/standards/README_STANDARD.md).
readme_check:
	@python3 scripts/docs/check_readme.py $(or $(README),README.md)
