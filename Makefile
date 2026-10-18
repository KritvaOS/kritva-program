# kritva-program Makefile: program-level helpers. Nothing here merges a PR.
#
#   make pr_check all                              sweep every repo's open PRs through the gate; approve the clear ones (D-046)
#   make pr_check REPO=kritva-sense PR=7           one PR
#   make pr_check REPO=kritva-sense                every open PR of one repo
#   make pr_check all DRY=1                        report only, no review is submitted
#
# GNU make takes "--repo" and "--pr" as its own options, so use REPO= and PR=.
# The script can also be called directly: python3 scripts/pipeline/pr_check.py --repo kritva-sense --pr 7

.PHONY: help pr_check all

help:
	@sed -n '3,8p' Makefile

# "all" is only a word after pr_check, so it must not build anything.
all:
	@$(if $(filter pr_check,$(MAKECMDGOALS)),:,$(MAKE) --no-print-directory help)

pr_check:
	@python3 scripts/pipeline/pr_check.py $(if $(filter all,$(MAKECMDGOALS)),all) $(if $(REPO),--repo $(REPO)) $(if $(PR),--pr $(PR)) $(if $(DRY),--no-approve)
