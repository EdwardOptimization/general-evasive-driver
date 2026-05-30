# m1715-paper-route-controller-family-calibrated-scale-up-execution Research Review

## Summary

- Generated at UTC: 20260530T015711Z
- Type: gate
- Gate tier: process
- Promotion decision: controller_family_calibrated_scale_up_execution_pass
- Decision reason: M1715 runs 864 public diagnostic episodes with zero failures finite metrics complete scale-up variant aggregates and guardrail zero

## Hypothesis

The M1712 source-expanded calibrated scale-up matrix can be executed as a fixed public diagnostic run with complete variant/outcome aggregates and no guardrail violations.

## Lineage

- parent_checkpoint: runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
- parent_dataset: docs/m1714-paper-route-controller-family-calibrated-scale-up-execution-design.md, runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_calibration_specs.json, runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_matrix.csv
- parent_config: experiments/manifests/m1714-paper-route-controller-family-calibrated-scale-up-execution-design.json
- parent_objective: execute measured source-expanded calibrated scale-up over fixed 864-cell matrix
- derived_from: m1714-paper-route-controller-family-calibrated-scale-up-execution-design
- blocked_by: need measured execution before scale-up result audit
- supersedes: direct calibrated scale-up result audit without execution
- invalidates: None

## Success Criteria

- runs/m1715_controller_family_calibrated_scale_up_execution/summary.json exists
- episode_count == 864
- failure_count == 0
- all_selected_metrics_finite == true
- guardrail_violation_count == 0
- scale_up_variant_aggregate.csv exists and includes all four labels
- outcome and termination aggregates exist
- scale_up_workload_id and scale_up_variant_label are preserved in episode rows
- training replay PPO promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- episode_count != 864
- failure_count != 0
- selected metrics are non-finite
- required aggregates are missing
- scale_up_variant_label is dropped
- training replay PPO private holdout promotion or actor-input changes occur
- controller-family ranking or level3 claims are made

## Evidence Gates

- M1715 must execute exactly the M1712 864-cell scale-up matrix
- M1715 must write episode, failure, state, variant, outcome, termination, task-family, source-edge, profile, and profile-outcome artifacts
- M1715 must preserve scale_up_variant_label and scale_up_workload_id in episode rows
- M1715 must keep all selected metrics finite and failure_count zero for an execution pass
- M1715 must not train replay PPO promote use private holdout or change actor inputs
- M1715 must not claim controller-family ranking, paper-level evidence, or level3 self-ID

## Holdout Policy

- not_used

## Forbidden Shortcuts

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

- milestone: m1715-paper-route-controller-family-calibrated-scale-up-execution
- type: gate
- checkpoint: runs/m1715_controller_family_calibrated_scale_up_execution/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controller_family_calibrated_scale_up_execution_pass
- reason: M1715 runs 864 public diagnostic episodes with zero failures finite metrics complete scale-up variant aggregates and guardrail zero

## Next Blocker

m1716-paper-route-controller-family-calibrated-scale-up-result-audit
