# m1386-paper-route-history-profile-one-seed-fixed-budget-smoke Research Review

## Summary

- Generated at UTC: 20260528T223903Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: history_profile_one_seed_smoke_pass_route_to_result_audit
- Decision reason: M1386 completes all 8 corrected profile train-eval seed runs with finite metrics and routes to audit before any 3-seed scaling or ranking claim

## Hypothesis

All eight corrected history-profile configs can complete one fixed-budget train/eval seed with finite metrics under the current codebase.

## Lineage

- parent_checkpoint: none
- parent_dataset: docs/m1385-paper-route-history-profile-corrected-runtime-smoke.md, runs/m1385_history_profile_corrected_runtime_smoke/summary.json, configs/paper_route_corrected_profiles
- parent_config: experiments/manifests/m1385-paper-route-history-profile-corrected-runtime-smoke.json
- parent_objective: run one-seed fixed-budget L0/L1/L2/L3 profile training/eval smoke after corrected runtime smoke passes
- derived_from: m1385-paper-route-history-profile-corrected-runtime-smoke
- blocked_by: M1385 passes runtime smoke and admits one-seed fixed-budget training/eval smoke
- supersedes: jumping directly to a 3-seed profile pilot, claiming profile ranking before one-seed fixed-budget plumbing is verified
- invalidates: None

## Success Criteria

- docs/m1386-paper-route-history-profile-one-seed-fixed-budget-smoke.md exists
- runs/m1386_history_profile_fixed_budget_smoke/summary.json exists
- profile_seed_rows.csv exists
- eval_rows.csv exists
- profile_aggregate.csv exists
- total_seed_runs is 8
- completed_seed_runs is 8
- failed_seed_runs is 0
- all_eval_metrics_finite is true
- private holdout remains unused
- no promotion or actor-input contract change occurs
- claims are limited to one-seed fixed-budget smoke

## Failure Criteria

- profile-specific budgets or hyperparameters change after seeing results
- private holdout is used
- metrics are framed as architecture-ranking or paper-level evidence
- hidden or oracle actor inputs are introduced
- failed profiles are omitted from summary
- corrected controls are not applied in training or evaluation

## Evidence Gates

- M1386 may run exactly one fixed-budget seed per corrected profile
- M1386 must use the same training seed and eval seed block for every profile
- M1386 must record failed profiles instead of omitting them
- M1386 must not promote, use private holdout, tune profiles, export corpus, or claim paper-level/profile-ranking evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change profile-specific budgets
- do not use private holdout
- do not promote any checkpoint
- do not tune hyperparameters after seeing profile results
- do not add hidden or oracle actor inputs
- do not claim recurrent-belief advantage
- do not claim self-identification
- do not claim architecture ranking from one seed

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1386-paper-route-history-profile-one-seed-fixed-budget-smoke
- type: gate
- checkpoint: runs/m1386_history_profile_fixed_budget_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: history_profile_one_seed_smoke_pass_route_to_result_audit
- reason: M1386 completes all 8 corrected profile train-eval seed runs with finite metrics and routes to audit before any 3-seed scaling or ranking claim

## Next Blocker

m1387-paper-route-history-profile-one-seed-smoke-result-audit
