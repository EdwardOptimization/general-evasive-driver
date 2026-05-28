# m1312-paper-route-source-history-robust-minfold-objective-probe Research Review

## Summary

- Generated at UTC: 20260528T162022Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: robust_minfold_repeat_mean_positive_lost_pass_tradeoff_route_to_result_audit
- Decision reason: M1312 improves aggregate repeat and top failed combo but loses baseline pass offsets 0 and 1 so PPO and promotion remain blocked

## Hypothesis

A train-split-only robust min-fold objective can protect M1302 passing folds while retaining or improving failed-fold source-history directionality better than M1309 weighted mean.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1311-paper-route-source-history-robust-minfold-objective-design.md, runs/m1310_source_history_weighted_repeat_tradeoff_audit/summary.json, runs/m1302_source_history_trainable_scope_repeat_probe/summary.json, runs/m1306_source_history_concentration_refresh_plan/summary.json
- parent_config: experiments/manifests/m1311-paper-route-source-history-robust-minfold-objective-design.json
- parent_objective: implement bounded no-PPO robust min-fold source-history objective probe
- derived_from: m1311-paper-route-source-history-robust-minfold-objective-design
- blocked_by: M1311 admits robust min-fold implementation after M1309 weighted repeat global regression
- supersedes: M1309 weighted mean repeat as the next implementation route
- invalidates: None

## Success Criteria

- runs/m1312_source_history_robust_minfold_probe/summary.json exists
- focused tests pass
- forbidden_parameter_mutation_detected is false
- pair_specific_weight_used is false
- baseline_pass_lost_offsets is empty
- repeat_offset_pass_count >= 3
- mean_eval_both_directional_fraction >= 0.2335317460
- mean_full_both_positive_count >= 38.0
- top_failed_combo_positive_delta >= 0
- no PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- run artifacts are missing
- focused tests fail
- forbidden parameters mutate
- pair-specific weights are used
- held-out eval rows are trained on
- baseline passing offsets are lost
- PPO starts
- private holdout is used
- checkpoint is promoted
- actor input contract changes

## Evidence Gates

- M1312 must not run PPO
- M1312 must not use private holdout
- M1312 must not promote
- M1312 must preserve actor input contract
- M1312 must not use pair-specific weights
- M1312 must report lost-pass offsets versus M1302
- M1312 must report repeat pass count and mean eval metrics
- M1312 must route to result audit before any further gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not use pair-specific weights
- do not train on held-out eval rows in the repeat probe
- do not average away lost-pass regressions
- do not overclaim self-identification

## Failure Taxonomy

- objective_overfit
- scenario_sampling_failure

## Scoreboard

- milestone: m1312-paper-route-source-history-robust-minfold-objective-probe
- type: infrastructure
- checkpoint: runs/m1312_source_history_robust_minfold_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: robust_minfold_repeat_mean_positive_lost_pass_tradeoff_route_to_result_audit
- reason: M1312 improves aggregate repeat and top failed combo but loses baseline pass offsets 0 and 1 so PPO and promotion remain blocked

## Next Blocker

m1313-paper-route-source-history-robust-minfold-result-audit
