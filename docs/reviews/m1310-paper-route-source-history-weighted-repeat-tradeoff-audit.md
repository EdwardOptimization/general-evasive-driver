# m1310-paper-route-source-history-weighted-repeat-tradeoff-audit Research Review

## Summary

- Generated at UTC: 20260528T160859Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: weighted_repeat_top_combo_partial_improvement_global_regression_route_to_robust_minfold_design
- Decision reason: M1310 finds top failed combo partial improvement but global repeat regresses from 3 of 5 to 1 of 5 offsets so route to robust minfold design

## Hypothesis

M1309's best-offset improvement with repeat regression can be classified from existing artifacts as fold overfit, weight-induced tradeoff, top-failed-combo improvement with global regression, or corpus/plan insufficiency before another objective run.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1309-paper-route-source-history-weighted-repeat-implementation.md, runs/m1309_source_history_weighted_repeat_probe/summary.json, runs/m1309_source_history_weighted_repeat_probe/scope_summaries.csv, runs/m1309_source_history_weighted_repeat_probe/group_rows.csv, runs/m1302_source_history_trainable_scope_repeat_probe/summary.json, runs/m1302_source_history_trainable_scope_repeat_probe/scope_summaries.csv, runs/m1304_source_history_repeat_failed_offset_audit/summary.json, runs/m1306_source_history_concentration_refresh_plan/summary.json, runs/m1306_source_history_concentration_refresh_plan/group_weight_rows.csv, runs/m1306_source_history_concentration_refresh_plan/balanced_split_rows.csv
- parent_config: experiments/manifests/m1309-paper-route-source-history-weighted-repeat-implementation.json
- parent_objective: no-training tradeoff audit for weighted source-history repeat
- derived_from: m1309-paper-route-source-history-weighted-repeat-implementation
- blocked_by: M1309 weighted repeat regressed repeat robustness despite improving one split
- supersedes: direct PPO or weighted objective tuning after M1309
- invalidates: None

## Success Criteria

- runs/m1310_source_history_weighted_repeat_tradeoff_audit/summary.json exists
- focused tests pass
- audit compares M1309 and M1302 per offset
- audit reports improved and regressed offsets
- audit reports whether M1304 top failed source-family/probe combo improved
- audit reports whether group weights correlate with gains or regressions
- audit produces a next-route decision
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- audit artifact is missing
- focused tests fail
- audit cannot compare M1309 and M1302
- audit omits failed-offset concentration comparison
- audit starts training or PPO
- audit uses private holdout
- checkpoint is promoted
- actor input contract changes

## Evidence Gates

- M1310 must not train
- M1310 must not run PPO
- M1310 must not use private holdout
- M1310 must not promote
- M1310 must compare M1309 against M1302
- M1310 must report which offsets improved and regressed
- M1310 must classify whether the weighted plan improved the M1304 top failed source-family/probe combo
- M1310 must route to corpus/plan redesign, objective redesign, or branch synthesis

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not tune weights from the same audit and call it unbiased
- do not treat one improved split as repeat robustness
- do not overclaim self-identification

## Failure Taxonomy

- objective_overfit
- scenario_sampling_failure

## Scoreboard

- milestone: m1310-paper-route-source-history-weighted-repeat-tradeoff-audit
- type: infrastructure
- checkpoint: runs/m1310_source_history_weighted_repeat_tradeoff_audit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: weighted_repeat_top_combo_partial_improvement_global_regression_route_to_robust_minfold_design
- reason: M1310 finds top failed combo partial improvement but global repeat regresses from 3 of 5 to 1 of 5 offsets so route to robust minfold design

## Next Blocker

m1311-paper-route-source-history-robust-minfold-objective-design
