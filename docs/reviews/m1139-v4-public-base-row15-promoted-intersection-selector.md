# m1139-v4-public-base-row15-promoted-intersection-selector Research Review

## Summary

- Generated at UTC: 20260527T224201Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: row15_promoted_intersection_selector_pass_route_to_target_materialization_design
- Decision reason: M1139 keeps 148 all-policy-pass rows across 13 physical pairs 5 source labels 2 targets and 6 left steps so it routes to target-policy materialization design

## Hypothesis

The M1137 all-policy intersection can be exported into a deterministic family-intersection surface with at least 100 rows and 12 physical pairs.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: runs/m1134_row15_promoted_family_aggregate_conversion/family_aggregate_boundary_rows.csv, runs/m1136_row15_promoted_family_aggregate_replay_sanity/cross_family_replay_rows.csv, docs/m1138-v4-public-base-row15-promoted-intersection-selector-design.md
- parent_config: experiments/manifests/m1138-v4-public-base-row15-promoted-intersection-selector-design.json
- parent_objective: run deterministic family-intersection selector for all-policy-pass rows
- derived_from: m1138-v4-public-base-row15-promoted-intersection-selector-design
- blocked_by: all-policy intersection rows have not been exported
- supersedes: None
- invalidates: direct mixed-family objective optimization, target-policy materialization before selector result

## Success Criteria

- family_intersection_rows.csv exists
- dropped_cross_family_rows.csv exists
- policy_pass_matrix.csv exists
- source_summary.csv exists
- target_summary.csv exists
- summary.json exists
- family_intersection_rows >= 100
- physical_pairs >= 12
- source_labels >= 4
- targets >= 2
- left_steps >= 6
- max_physical_pair_fraction <= 0.25
- max_source_label_fraction <= 0.45
- no replay, objective optimization, training, PPO, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- selector artifact is missing
- diversity gate fails
- expected policy is missing
- replay, objective optimization, training, PPO, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1139 may run only the M1138 pre-registered selector command
- M1139 must not train actor weights
- M1139 must not run PPO
- M1139 must not run replay
- M1139 must not run objective optimization
- M1139 must not promote
- M1139 must not use private holdout
- M1139 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not run objective optimization
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken thresholds after seeing selector result

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1139-v4-public-base-row15-promoted-intersection-selector
- type: infrastructure
- checkpoint: runs/m1139_row15_promoted_intersection_selector/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_intersection_selector_pass_route_to_target_materialization_design
- reason: M1139 keeps 148 all-policy-pass rows across 13 physical pairs 5 source labels 2 targets and 6 left steps so it routes to target-policy materialization design

## Next Blocker

m1140-v4-public-base-row15-promoted-target-materialization-design
