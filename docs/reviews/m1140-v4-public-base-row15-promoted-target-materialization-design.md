# m1140-v4-public-base-row15-promoted-target-materialization-design Research Review

## Summary

- Generated at UTC: 20260527T224458Z
- Type: gate
- Gate tier: process
- Promotion decision: row15_promoted_target_materialization_design_route_to_branch_synthesis
- Decision reason: M1140 designs row15_current target-policy materialization for 148 M1139 intersection rows and routes to synthesis before implementation because cadence fired

## Hypothesis

The M1139 all-policy intersection can be materialized under the current public-gate base row15_current so later objective rows use one target-policy hidden-state/action/margin space.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1139-v4-public-base-row15-promoted-intersection-selector.md, runs/m1139_row15_promoted_intersection_selector/family_intersection_rows.csv, runs/m1136_row15_promoted_family_aggregate_replay_sanity/cross_family_replay_rows.csv
- parent_config: experiments/manifests/m1139-v4-public-base-row15-promoted-intersection-selector.json
- parent_objective: design current public-gate base target-policy materialization for M1139 all-policy intersection rows
- derived_from: m1139-v4-public-base-row15-promoted-intersection-selector
- blocked_by: M1139 selector passes, but direct objective conversion would mix source-policy rows with target-policy objective fields
- supersedes: None
- invalidates: feeding M1139 family_intersection_rows.csv directly into an objective corpus, mixing source-policy hidden-state spaces in one objective corpus, using source-row margins when optimizing row15_current target policy

## Success Criteria

- design artifact exists
- target policy label is explicit
- target policy checkpoint path is explicit
- source metadata preservation is explicit
- target-policy objective field mapping is explicit
- row count and diversity validation thresholds are explicit
- fail-closed behavior is explicit
- no training, PPO, replay, objective optimization, mining, promotion, or private holdout occurs

## Failure Criteria

- design artifact is missing
- target policy selection is ambiguous
- source and target fields are conflated
- required boundary-outcome columns are not mapped
- training, PPO, replay, objective optimization, mining, promotion, or private holdout starts

## Evidence Gates

- M1140 must design only
- M1140 must not train actor weights
- M1140 must not run PPO
- M1140 must not run replay
- M1140 must not run objective optimization
- M1140 must not mine rows
- M1140 must not promote
- M1140 must not use private holdout
- M1140 must preserve actor inputs
- M1140 must select exactly one target policy for materialization

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not run objective optimization
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not write objective NPZ
- do not weaken M1139 selector thresholds after seeing the result
- do not materialize multiple target policies into one objective row file

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1140-v4-public-base-row15-promoted-target-materialization-design
- type: gate
- checkpoint: docs/m1140-v4-public-base-row15-promoted-target-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_target_materialization_design_route_to_branch_synthesis
- reason: M1140 designs row15_current target-policy materialization for 148 M1139 intersection rows and routes to synthesis before implementation because cadence fired

## Next Blocker

m1141-v4-public-base-row15-promoted-surface-refresh-synthesis
