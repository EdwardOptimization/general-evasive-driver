# m1123-v4-public-base-row15-unsafe-margin-projection-probe Research Review

## Summary

- Generated at UTC: 20260527T213558Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_unsafe_margin_projection_first_replay_candidate_route_to_family_replay_design
- Decision reason: M1123 selects alpha 0.15 with exact M1107 delta -0.000417 row15 unsafe margins retained and six-surface first replay pass without training PPO promotion or private holdout

## Hypothesis

A smaller nonzero interpolation of the M1118 direction can preserve row15 wrong-history unsafe terminal margin while retaining exact M1107 objective improvement.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt
- parent_dataset: docs/m1122-v4-public-base-row15-unsafe-margin-retention-design.md, runs/m1107_materialized_objective_corpus/boundary_outcome_corpus.npz, runs/m1115_materialized_failed_wrong_history_retention_export/target_base_rejected_trajectory_anchor.npz, runs/m1115_materialized_failed_wrong_history_retention_export/combined_target_base_rejected_anchor.npz, runs/m1120_failed_wrong_history_retention_first_replay/lost_success_drop_rows.csv
- parent_config: experiments/manifests/m1122-v4-public-base-row15-unsafe-margin-retention-design.json
- parent_objective: test whether a nonzero interpolation of the M1118 update direction preserves row15 wrong-history unsafe terminal margin
- derived_from: m1122-v4-public-base-row15-unsafe-margin-retention-design
- blocked_by: M1122 admits only a no-training row15 unsafe-margin projection probe
- supersedes: None
- invalidates: direct M1118 family-intersection replay, direct M1118 full public gate, PPO from m1118_seed111800, promotion of any M1123 candidate

## Success Criteria

- interpolation candidates are generated for the registered alpha set
- selected alpha is nonzero
- selected alpha passes contract and exact gates
- selected alpha passes row15 unsafe-margin gate for all five row15 variants
- selected alpha passes the six-surface M1120 first replay if selected
- no actor training, PPO, family-intersection replay, full public gate, fresh/OOD, behavior gate, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- no nonzero alpha passes row15 unsafe-margin
- selected alpha fails six-surface first replay
- any candidate violates actor contract
- actor training, PPO, family-intersection replay, full public gate, fresh/OOD, behavior gate, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1123 may create interpolation checkpoints between base and M1118 seed111800
- M1123 may evaluate exact M1107 and row15 unsafe-margin replay
- M1123 may run the six-surface M1120 first replay only for the selected nonzero alpha
- M1123 must not train actor weights
- M1123 must not run PPO
- M1123 must not run family-intersection replay
- M1123 must not run full public gate
- M1123 must not run fresh/OOD or behavior gates
- M1123 must not promote
- M1123 must not use private holdout
- M1123 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run family-intersection replay
- do not run full public gate
- do not run fresh/OOD or behavior gates
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken replay thresholds
- do not select alpha 0.0
- do not retry additional alphas after selected first replay failure without a new manifest

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1123-v4-public-base-row15-unsafe-margin-projection-probe
- type: gate
- checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_unsafe_margin_projection_first_replay_candidate_route_to_family_replay_design
- reason: M1123 selects alpha 0.15 with exact M1107 delta -0.000417 row15 unsafe margins retained and six-surface first replay pass without training PPO promotion or private holdout

## Next Blocker

m1124-v4-public-base-row15-projection-family-replay-design
