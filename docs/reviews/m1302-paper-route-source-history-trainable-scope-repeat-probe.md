# m1302-paper-route-source-history-trainable-scope-repeat-probe Research Review

## Summary

- Generated at UTC: 20260528T151736Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_history_trainable_scope_repeat_mixed_route_to_result_audit
- Decision reason: M1302 fusion_head repeat is mixed: 3/5 offsets pass but mean eval fractions 0.2335 are below 0.25; no forbidden mutation and no PPO or promotion

## Hypothesis

The M1299 fusion_head signal remains positive across multiple deterministic pair-disjoint split offsets.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1301-paper-route-source-history-trainable-scope-repeat-design.md, runs/m1280_four_wheel_source_response_history_materialization/history_frame_rows.csv, runs/m1280_four_wheel_source_response_history_materialization/history_intervention_rows.csv, runs/m1280_four_wheel_source_response_history_materialization/wrong_history_pair_rows.csv, runs/m1277_four_wheel_source_intervention_materialization/intervention_observations.csv, runs/m1277_four_wheel_source_intervention_materialization/intervention_action_sequences.csv, runs/m1299_source_history_trainable_scope_probe/summary.json
- parent_config: experiments/manifests/m1301-paper-route-source-history-trainable-scope-repeat-design.json
- parent_objective: implement bounded fusion_head split-repeat source-history diagnostic
- derived_from: m1301-paper-route-source-history-trainable-scope-repeat-design
- blocked_by: M1301 designs split-repeat robustness but no repeat artifacts exist
- supersedes: single split M1299 result as robustness evidence
- invalidates: None

## Success Criteria

- runs/m1302_source_history_trainable_scope_repeat_probe/summary.json exists
- focused tests pass
- repeat summaries and offset pass counts are reported
- parameter-group deltas are reported
- forbidden parameter mutation flag is false
- result class is repeat strong, mixed, negative, or contract artifact
- no PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- run artifacts are missing
- repeat metrics are missing
- parameter-group deltas are missing
- forbidden parameters mutate
- PPO starts
- private holdout is used
- checkpoint is promoted
- actor input contract changes
- thresholds are relaxed after seeing results

## Evidence Gates

- M1302 must preserve actor input contract
- M1302 must not run PPO
- M1302 must not use private holdout
- M1302 must not promote
- M1302 must run multiple pair-disjoint split offsets
- M1302 must report repeat pass counts
- M1302 must report parameter-group deltas

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not train scopes beyond fusion_head
- do not treat repeat success as closed-loop proof
- do not overclaim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1302-paper-route-source-history-trainable-scope-repeat-probe
- type: infrastructure
- checkpoint: runs/m1302_source_history_trainable_scope_repeat_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_trainable_scope_repeat_mixed_route_to_result_audit
- reason: M1302 fusion_head repeat is mixed: 3/5 offsets pass but mean eval fractions 0.2335 are below 0.25; no forbidden mutation and no PPO or promotion

## Next Blocker

m1303-paper-route-source-history-trainable-scope-repeat-result-audit
