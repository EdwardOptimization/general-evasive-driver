# m1718-paper-route-controller-family-off-track-dominance-localization Research Review

## Summary

- Generated at UTC: 20260530T020823Z
- Type: gate
- Gate tier: process
- Promotion decision: off_track_dominance_localization_pass
- Decision reason: M1718 materializes no-rollout localization aggregates with 48 repair target slices and guardrail zero

## Hypothesis

Existing M1715 episode rows can localize which variant/source/profile slices drive remaining off-track dominance before repair design.

## Lineage

- parent_checkpoint: not_applicable_no_rollout_data_audit
- parent_dataset: docs/m1717-paper-route-controller-family-task-quality-scale-up-synthesis.md, runs/m1715_controller_family_calibrated_scale_up_execution/episode_rows.csv, runs/m1715_controller_family_calibrated_scale_up_execution/scale_up_variant_aggregate.csv, runs/m1715_controller_family_calibrated_scale_up_execution/source_edge_aggregate.csv, runs/m1715_controller_family_calibrated_scale_up_execution/task_family_aggregate.csv
- parent_config: experiments/manifests/m1717-paper-route-controller-family-task-quality-scale-up-synthesis.json
- parent_objective: localize off-track dominance before task-quality repair
- derived_from: m1717-paper-route-controller-family-task-quality-scale-up-synthesis
- blocked_by: need no-rollout localization before designing repair variants
- supersedes: direct task-quality repair design after M1717, direct controller-family comparison after M1717
- invalidates: None

## Success Criteria

- runs/m1718_off_track_dominance_localization/summary.json exists
- variant_source_edge_aggregate.csv exists
- variant_task_family_aggregate.csv exists
- variant_profile_aggregate.csv exists
- source_task_family_aggregate.csv exists
- repair_target_slices.csv exists
- docs/m1718-paper-route-controller-family-off-track-dominance-localization.md exists
- environment rollout training replay PPO promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- M1715 episode rows are missing
- cross aggregates are missing
- repair target slices are not explicit
- localization ranks controller-family profiles
- environment rollout training replay PPO private holdout promotion or actor-input changes occur

## Evidence Gates

- M1718 must use existing M1715 episode rows only
- M1718 must write variant-source, variant-task-family, variant-profile, source-task-family, and profile-outcome aggregates
- M1718 must identify repair target slices without changing profiles or task configs
- M1718 must not run rollout train replay PPO promote use private holdout or change actor inputs
- M1718 must not claim controller-family ranking, paper-level evidence, or level3 self-ID

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment rollout
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1718-paper-route-controller-family-off-track-dominance-localization
- type: gate
- checkpoint: runs/m1718_off_track_dominance_localization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: off_track_dominance_localization_pass
- reason: M1718 materializes no-rollout localization aggregates with 48 repair target slices and guardrail zero

## Next Blocker

m1719-paper-route-controller-family-off-track-dominance-localization-result-audit
