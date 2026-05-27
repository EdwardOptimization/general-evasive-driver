# m1098-v4-public-base-family-aggregate-replay-sanity-design Research Review

## Summary

- Generated at UTC: 20260527T192251Z
- Type: gate
- Gate tier: process
- Promotion decision: family_aggregate_replay_sanity_design_admit_wrapper_run
- Decision reason: M1098 designs a source-aware replay wrapper with row_id equals family_row_id source-policy source-row gates cross-family report and duplicate geometry failure audit before objective optimization

## Hypothesis

A source-aware replay sanity design can test the M1097 family-aggregate export before objective optimization while preserving source labels and duplicate geometry metadata.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
- parent_dataset: docs/m1097-v4-public-base-family-aggregate-conversion-implementation.md, runs/m1097_family_aggregate_boundary_conversion/summary.json, runs/m1097_family_aggregate_boundary_conversion/replay_plan.json, runs/m1097_family_aggregate_boundary_conversion/family_aggregate_boundary_rows.csv
- parent_config: experiments/manifests/m1097-v4-public-base-family-aggregate-conversion-implementation.json
- parent_objective: design replay sanity for the family-aggregate raw-retained export before objective optimization
- derived_from: m1097-v4-public-base-family-aggregate-conversion-implementation
- blocked_by: M1097 exported replay-ready rows but intentionally did not run replay or objective optimization
- supersedes: None
- invalidates: running objective optimization before family-aggregate replay sanity, promoting the export as proof without replay, ignoring duplicate geometry groups during replay analysis

## Success Criteria

- replay sanity design artifact exists
- source-policy-on-source-rows gates are explicit
- cross-family replay report metrics are explicit
- duplicate geometry failure analysis is explicit
- no training, PPO, replay, objective optimization, mining, promotion, or private holdout occurs

## Failure Criteria

- design artifact is missing
- source-policy replay gates are ambiguous
- cross-family replay report is missing
- duplicate geometry audit is missing
- training, PPO, replay, objective optimization, mining, promotion, or private holdout starts

## Evidence Gates

- M1098 must design only
- M1098 must not train
- M1098 must not run PPO
- M1098 must not run replay
- M1098 must not run objective optimization
- M1098 must not mine rows
- M1098 must not promote
- M1098 must not use private holdout
- M1098 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run replay
- do not run objective optimization
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken M1097 aggregate thresholds
- do not skip duplicate geometry failure analysis

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1098-v4-public-base-family-aggregate-replay-sanity-design
- type: gate
- checkpoint: docs/m1098-v4-public-base-family-aggregate-replay-sanity-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: family_aggregate_replay_sanity_design_admit_wrapper_run
- reason: M1098 designs a source-aware replay wrapper with row_id equals family_row_id source-policy source-row gates cross-family report and duplicate geometry failure audit before objective optimization

## Next Blocker

m1099-v4-public-base-family-aggregate-replay-sanity-implementation
