# kritva-program Makefile: program-level helpers.  Run `make` or `make help` for the command list.
#
# Lines starting with "##" are the help text. "##@ Name" starts a group, "## name: text" documents a target.
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
# `make help` prints the "#   make ..." example lines above after the target list.
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
.PHONY: help all sync git_sync test regen verify readme_check pr_open pr_watch pr_land pr_check ship merge

##@ Help
help: ## Show this list
	@awk 'BEGIN { FS = ":.*##"; printf "\nUsage: make <target> [VAR=value ...]\n" } \
	  /^##@/ { g = substr($$0, 5); next } \
	  /^[a-zA-Z0-9_.-]+:[^=].*##/ { if (g != "") { printf "\n%s\n", g; g = "" }; sub(/^ +/, "", $$2); printf "  %-24s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo; echo "Examples:"
	@sed -n 's/^#   make /  make /p' $(firstword $(MAKEFILE_LIST))
	@echo

# "all" is only a word after pr_check, so it must not build anything.
all:
	@$(if $(filter pr_check,$(MAKECMDGOALS)),:,$(MAKE) --no-print-directory help)

##@ Everyday: from a handoff tarball to a merged PR (run in this clone)
sync: ## Switch to main and fast-forward it from origin
	@git checkout main && git pull --ff-only

# Wraps scripts/pipeline/pr-open.sh.
pr_open: ## Tarball to PR: new branch, extract, test, commit, push, open the PR. TAR= BRANCH= MSG= [TASK=KRP-ENG-001] [DRY=1] [NOTEST=1]
	@scripts/pipeline/pr-open.sh $(if $(TAR),--tar "$(TAR)") $(if $(BRANCH),--branch "$(BRANCH)") $(if $(MSG),--msg "$(MSG)") $(if $(TASK),--task "$(TASK)") $(if $(NOTEST),--no-test) $(if $(DRY),--dry)

pr_watch: ## Wait for the checks of the PR on the current branch
	@gh pr checks --watch

pr_land: ## Merge the current branch's PR (--admin) after the checks pass, then back to an updated main. [DRY=1] [NOADMIN=1]
	@scripts/pipeline/pr-land.sh $(if $(DRY),--dry) $(if $(NOADMIN),--no-admin)

##@ Checks and generated files
test: ## Run the whole test suite (python3 -m unittest)
	@python3 -m unittest discover -s tests

regen: ## Regenerate the status JSON, STATUS_VIEW.md and STATUS_DETAIL.md from the inputs (writes files; commit them with the input change)
	@python3 tools/consolidate_status.py --sources-dir sources

verify: ## Check that the committed status files match their inputs (reads only)
	@python3 tools/consolidate_status.py --sources-dir sources --check

# README structure, metadata and local links (v2/planning/standards/README_STANDARD.md).
readme_check: ## Check README.md against the README standard (D-055); README=path for another file
	@python3 scripts/docs/check_readme.py $(or $(README),README.md)

##@ Other repositories (D-046)
pr_check: ## Sweep every repo with `pr_check all`, or one repo/PR with REPO=x [PR=n]; DRY=1 only reports
	@python3 scripts/pipeline/pr_check.py $(if $(filter all,$(MAKECMDGOALS)),all --repos "$(REPOS)") $(if $(REPO),--repo $(REPO)) $(if $(PR),--pr $(PR)) $(if $(DRY),--no-approve)

# Wraps scripts/pipeline/ship-prs.sh (always --admin, manifest order). Options: TAR or PATCHES, BRANCH, ONLY, BODY, TAG + MILESTONE, DRY=1.
ship: ## Open, check, merge and sync one PR per repo from a patch set. TAR= or PATCHES=, BRANCH=, [ONLY=repo] [DRY=1]
	@scripts/pipeline/ship.sh $(if $(BRANCH),--branch "$(BRANCH)") $(if $(TAR),--tar "$(TAR)") $(if $(PATCHES),--patches "$(PATCHES)") $(if $(ONLY),--only "$(ONLY)") $(if $(BODY),--body "$(BODY)") $(if $(TAG),--tag "$(TAG)" --milestone "$(MILESTONE)") $(if $(DRY),--dry)

# Merge an already open PR of another repo (see scripts/pipeline/merge-pr.sh). Options: REPO, PR, DRY=1, NOADMIN=1.
merge: ## Merge a PR you pushed yourself in another repo: gate, checks, --admin merge, sync. REPO=x PR=n [DRY=1]
	@scripts/pipeline/merge-pr.sh $(if $(REPO),--repo "$(REPO)") $(if $(PR),--pr "$(PR)") $(if $(DRY),--dry) $(if $(NOADMIN),--no-admin)

##@ Git
git_sync: ## Switch to main, fast-forward from origin, prune, delete merged local branches
	@git switch main
	@git pull --ff-only --prune
	@git branch --format='%(refname:short)' | grep -vx main | xargs -r git branch -d
	@git log --oneline -3
