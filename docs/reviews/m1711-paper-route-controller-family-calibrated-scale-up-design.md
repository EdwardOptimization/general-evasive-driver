# m1711-paper-route-controller-family-calibrated-scale-up-design Research Review

## Summary

- Generated at UTC: 20260530T013432Z
- Type: gate
- Gate tier: process
- Promotion decision: calibrated_scale_up_design_admit_no_rollout_preflight
- Decision reason: M1711 designs 18-base-spec 4-variant 864-cell source-expanded scale-up preserving baseline best off-track collision-control and mid variants

## Hypothesis

A source-expanded fixed-budget calibrated scale-up can be designed from M1709/M1710 without overfitting to the best off-track variant.

## Lineage

- parent_checkpoint: runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
- parent_dataset: docs/m1710-paper-route-controller-family-task-quality-calibration-branch-synthesis.md, runs/m1708_controller_family_bounded_calibration_smoke_execution/calibration_variant_aggregate.csv, runs/m1702_controller_family_task_quality_calibration_preflight/calibration_matrix.csv
- parent_config: experiments/manifests/m1710-paper-route-controller-family-task-quality-calibration-branch-synthesis.json
- parent_objective: design source-expanded calibrated scale-up while preserving fixed execution budget
- derived_from: m1710-paper-route-controller-family-task-quality-calibration-branch-synthesis
- blocked_by: need scale-up design before materializing broader calibrated subset
- supersedes: direct execution of M1708 best variant only, direct controller-family ranking after M1709
- invalidates: None

## Success Criteria

- docs/m1711-paper-route-controller-family-calibrated-scale-up-design.md exists
- selected base spec target and task split are specified
- four calibration variants are specified including baseline and collision-control variants
- planned execution budget remains 864 episodes
- rollout execution training replay PPO promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- design executes rollout
- design only keeps the best off-track variant
- design drops baseline or collision-control variants
- design exceeds fixed budget without audit
- design ranks controller profiles
- training replay PPO private holdout promotion or level3 claims occur

## Evidence Gates

- M1711 must design source-expanded calibrated scale-up without execution
- M1711 must preserve original baseline, best off-track, collision-control, and mid calibration variants
- M1711 must keep fixed 864-episode execution budget
- M1711 must keep task-quality calibration separate from controller-family ranking
- M1711 must not execute rollout train replay PPO promote use private holdout or change actor inputs

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
- do not claim controller-family ranking
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1711-paper-route-controller-family-calibrated-scale-up-design
- type: gate
- checkpoint: docs/m1711-paper-route-controller-family-calibrated-scale-up-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: calibrated_scale_up_design_admit_no_rollout_preflight
- reason: M1711 designs 18-base-spec 4-variant 864-cell source-expanded scale-up preserving baseline best off-track collision-control and mid variants

## Next Blocker

m1712-paper-route-controller-family-calibrated-scale-up-preflight
