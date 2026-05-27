# m1134-v4-public-base-row15-promoted-family-aggregate-conversion Research Review

## Summary

- Generated at UTC: 20260527T222559Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: row15_promoted_family_aggregate_conversion_pass_route_to_replay_sanity_design
- Decision reason: M1134 exports 172 source-preserving family aggregate rows with 15 physical pairs 6 left steps 5 checkpoints 3 targets and no mixed source objective NPZ

## Hypothesis

The M1132 172-row promoted-base surface can be exported into a source-preserving family aggregate replay/audit corpus without losing diversity.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: runs/m1132_row15_promoted_source_balanced_surface_seed113200/balanced_accepted_wrong_history_rows.csv, docs/m1133-v4-public-base-row15-promoted-compact-conversion-design.md
- parent_config: experiments/manifests/m1133-v4-public-base-row15-promoted-compact-conversion-design.json
- parent_objective: run export-only family-aggregate conversion for the M1132 promoted-base surface
- derived_from: m1133-v4-public-base-row15-promoted-compact-conversion-design
- blocked_by: M1132 surface has not been converted into source-preserving aggregate replay/audit rows
- supersedes: None
- invalidates: training directly on M1132 rows without conversion, dropping source metadata before replay sanity

## Success Criteria

- family_aggregate_boundary_rows.csv exists
- source_policy_map.json exists
- source_summary.csv exists
- duplicate_geometry_summary.csv exists
- replay_plan.json exists
- summary.json exists
- rows >= 100
- physical_pairs >= 12
- left_steps >= 6
- checkpoints >= 4
- targets >= 2
- normal_margin_buckets >= 2
- success_drop_fraction == 1.0
- max_rows_per_physical_pair_fraction <= 0.25
- no actor training, PPO, objective optimization, replay, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- conversion artifact is missing
- source policy map is incomplete
- diversity thresholds fail
- mixed hidden-state objective NPZ is written
- actor training, PPO, objective optimization, replay, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1134 may run only the M1133 pre-registered export conversion command
- M1134 must not train actor weights
- M1134 must not run PPO
- M1134 must not run objective optimization
- M1134 must not run replay
- M1134 must not promote
- M1134 must not use private holdout
- M1134 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run objective optimization
- do not run replay
- do not promote
- do not use private holdout
- do not change actor inputs
- do not discard source metadata
- do not write mixed hidden-state objective NPZ

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1134-v4-public-base-row15-promoted-family-aggregate-conversion
- type: infrastructure
- checkpoint: runs/m1134_row15_promoted_family_aggregate_conversion/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_family_aggregate_conversion_pass_route_to_replay_sanity_design
- reason: M1134 exports 172 source-preserving family aggregate rows with 15 physical pairs 6 left steps 5 checkpoints 3 targets and no mixed source objective NPZ

## Next Blocker

m1135-v4-public-base-row15-promoted-replay-sanity-design
