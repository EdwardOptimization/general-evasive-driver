# m1311-paper-route-source-history-robust-minfold-objective-design Research Review

## Summary

- Generated at UTC: 20260528T161220Z
- Type: gate
- Gate tier: process
- Promotion decision: source_history_robust_minfold_objective_design_admit_bounded_probe
- Decision reason: M1311 designs train-split-only robust minfold objective with bucket CVaR passing-fold retention and lost-pass non-regression before bounded no-PPO probe

## Hypothesis

A robust min-fold or lexicographic objective can address M1309's weighted-repeat global regression by making lost-pass non-regression a first-class constraint instead of increasing scalar group weights.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1310-paper-route-source-history-weighted-repeat-tradeoff-audit.md, runs/m1310_source_history_weighted_repeat_tradeoff_audit/summary.json, runs/m1310_source_history_weighted_repeat_tradeoff_audit/offset_comparison.csv, runs/m1310_source_history_weighted_repeat_tradeoff_audit/full_group_comparison.csv, runs/m1310_source_history_weighted_repeat_tradeoff_audit/source_probe_summary.csv, runs/m1310_source_history_weighted_repeat_tradeoff_audit/weight_gain_summary.csv
- parent_config: experiments/manifests/m1310-paper-route-source-history-weighted-repeat-tradeoff-audit.json
- parent_objective: design robust min-fold or lexicographic source-history objective after weighted-repeat regression
- derived_from: m1310-paper-route-source-history-weighted-repeat-tradeoff-audit
- blocked_by: M1310 classified M1309 as top-combo partial improvement with global repeat regression
- supersedes: more scalar group-weight pressure after M1309
- invalidates: None

## Success Criteria

- docs/m1311-paper-route-source-history-robust-minfold-objective-design.md exists
- design defines fold-level non-regression criteria
- design defines objective terms for passing-fold retention and failed-fold improvement
- design keeps pair-specific weights forbidden
- design pre-registers implementation thresholds if implementation is admitted
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design only increases scalar weights
- design omits lost-pass non-regression
- design uses pair-specific weights
- design routes directly to PPO
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1311 must not train
- M1311 must not run PPO
- M1311 must not use private holdout
- M1311 must not promote
- M1311 must preserve actor input contract
- M1311 must design fold-level non-regression criteria
- M1311 must define how passing folds are protected before failed folds are optimized
- M1311 must decide whether implementation is justified

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not use pair-specific weights
- do not average away lost-pass regressions
- do not treat fixed-current diagnostics as closed-loop self-identification proof

## Failure Taxonomy

- objective_overfit
- scenario_sampling_failure

## Scoreboard

- milestone: m1311-paper-route-source-history-robust-minfold-objective-design
- type: gate
- checkpoint: docs/m1311-paper-route-source-history-robust-minfold-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_robust_minfold_objective_design_admit_bounded_probe
- reason: M1311 designs train-split-only robust minfold objective with bucket CVaR passing-fold retention and lost-pass non-regression before bounded no-PPO probe

## Next Blocker

m1312-paper-route-source-history-robust-minfold-objective-probe
