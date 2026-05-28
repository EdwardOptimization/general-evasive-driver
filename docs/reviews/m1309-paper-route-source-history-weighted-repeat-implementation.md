# m1309-paper-route-source-history-weighted-repeat-implementation Research Review

## Summary

- Generated at UTC: 20260528T160105Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_history_weighted_repeat_mixed_regression_route_to_tradeoff_audit
- Decision reason: M1309 weighted repeat is infrastructure-valid but regresses repeat robustness from 3 of 5 to 1 of 5 offsets while offset 3 improves strongly

## Hypothesis

Using the M1306 balanced split plan and capped group weights will improve repeat robustness over M1302 without pair-specific overfit or forbidden parameter mutation.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1308-paper-route-source-history-trainable-scope-escalation-synthesis.md, docs/m1307-paper-route-source-history-weighted-repeat-design.md, runs/m1306_source_history_concentration_refresh_plan/balanced_split_rows.csv, runs/m1306_source_history_concentration_refresh_plan/group_weight_rows.csv, runs/m1306_source_history_concentration_refresh_plan/summary.json
- parent_config: experiments/manifests/m1308-paper-route-source-history-trainable-scope-escalation-synthesis.json
- parent_objective: implement bounded weighted source-history trainable-scope repeat
- derived_from: m1308-paper-route-source-history-trainable-scope-escalation-synthesis
- blocked_by: M1308 promotes to a new weighted-repeat implementation branch
- supersedes: unweighted M1302 repeat as the only repeat robustness probe
- invalidates: None

## Success Criteria

- runs/m1309_source_history_weighted_repeat_probe/summary.json exists
- focused tests pass
- split_plan_used is true
- group_weights_used is true
- pair_specific_weight_used is false
- max_group_weight <= 2.0
- weighted repeat metrics are reported
- no PPO, promotion, private holdout, threshold relaxation, pair-specific weighting, or actor-input expansion occurs

## Failure Criteria

- run artifacts are missing
- focused tests fail
- split plan is not used
- group weights are not used
- pair-specific weights are used
- forbidden parameters mutate
- PPO starts
- private holdout is used
- checkpoint is promoted
- actor input contract changes

## Evidence Gates

- M1309 must preserve actor input contract
- M1309 must not run PPO
- M1309 must not use private holdout
- M1309 must not promote
- M1309 must use M1306 split plan
- M1309 must use M1306 group weights
- M1309 must prove pair-specific weights are not used
- M1309 must report weighted repeat metrics

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax thresholds
- do not use pair-specific weights
- do not treat weighted diagnostic success as closed-loop proof
- do not overclaim self-identification

## Failure Taxonomy

- objective_overfit
- scenario_sampling_failure

## Scoreboard

- milestone: m1309-paper-route-source-history-weighted-repeat-implementation
- type: infrastructure
- checkpoint: runs/m1309_source_history_weighted_repeat_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_weighted_repeat_mixed_regression_route_to_tradeoff_audit
- reason: M1309 weighted repeat is infrastructure-valid but regresses repeat robustness from 3 of 5 to 1 of 5 offsets while offset 3 improves strongly

## Next Blocker

m1310-paper-route-source-history-weighted-repeat-tradeoff-audit
