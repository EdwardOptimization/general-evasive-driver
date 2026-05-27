# m1097-v4-public-base-family-aggregate-conversion-implementation Research Review

## Summary

- Generated at UTC: 20260527T191836Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: family_aggregate_conversion_export_pass
- Decision reason: M1097 export-only conversion passes aggregate thresholds with 146 rows 18 physical pairs 9 left steps 4 checkpoints 3 targets and writes replay_plan without replay or objective optimization

## Hypothesis

The M1096 family-aggregate raw-retained contract can be implemented as an export-only conversion tool that preserves the M1092 source-balanced surface and writes replay-ready metadata without mixing hidden states into an objective corpus.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
- parent_dataset: docs/m1096-v4-public-base-family-aggregate-conversion-design.md, runs/m1092_source_balanced_coverage_expansion_seed109200/balanced_accepted_wrong_history_rows.csv
- parent_config: experiments/manifests/m1096-v4-public-base-family-aggregate-conversion-design.json
- parent_objective: implement and run export-only family-aggregate raw-retained conversion contract
- derived_from: m1096-v4-public-base-family-aggregate-conversion-design
- blocked_by: M1096 requires an export-only conversion before replay sanity or objective optimization
- supersedes: None
- invalidates: writing a mixed-source objective NPZ in the conversion implementation, dropping duplicate geometry rows across checkpoint labels, running replay or objective optimization from M1097

## Success Criteria

- exporter implementation exists
- focused tests pass
- family_aggregate_boundary_rows.csv exists
- source_policy_map.json exists
- source_summary.csv exists
- duplicate_geometry_summary.csv exists
- replay_plan.json exists
- summary.json exists
- aggregate thresholds pass
- no training, PPO, replay, objective optimization, mining, promotion, or private holdout occurs

## Failure Criteria

- exporter is missing
- unmapped source labels do not fail closed
- duplicate geometry is dropped or not summarized
- aggregate thresholds fail
- replay or objective optimization starts
- training, PPO, mining, promotion, or private holdout starts

## Evidence Gates

- M1097 must implement export-only conversion
- M1097 must not train
- M1097 must not run PPO
- M1097 must not run replay
- M1097 must not run objective optimization
- M1097 must not mine rows
- M1097 must not promote
- M1097 must not use private holdout
- M1097 must fail closed on unmapped source checkpoint labels

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
- do not weaken M1092 thresholds
- do not silently mix hidden states into one objective corpus

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1097-v4-public-base-family-aggregate-conversion-implementation
- type: infrastructure
- checkpoint: runs/m1097_family_aggregate_boundary_conversion/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: family_aggregate_conversion_export_pass
- reason: M1097 export-only conversion passes aggregate thresholds with 146 rows 18 physical pairs 9 left steps 4 checkpoints 3 targets and writes replay_plan without replay or objective optimization

## Next Blocker

m1098-v4-public-base-family-aggregate-replay-sanity-design
