# m1950-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-implementation Research Review

## Summary

- Generated at UTC: 20260531T094440Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: task_quality_anchor_fallback_geometry_calibration_pass_route_to_calibrated_source_mining_application_design
- Decision reason: M1950 calibration pass selects label-correct stable-AEB fallback geometry at distance 52 half-width 0.75 for both surfaces with 64/64 supported anchors 4032 accepted cells and guardrail 0

## Hypothesis

A focused no-rollout calibration tool can find stable-AEB anchor fallback geometry whose classifier support is label-correct for both surface variants.

## Lineage

- parent_checkpoint: not_applicable_task_quality_offtrack_support_anchor_fallback_geometry_calibration
- parent_dataset: docs/m1949-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-design.md, configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json, runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/repair_blocked_rows.csv, runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/source_kind_aggregate.csv
- parent_config: experiments/manifests/m1949-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-design.json
- parent_objective: implement and run no-rollout stable-AEB anchor fallback geometry calibration
- derived_from: m1949-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-design
- blocked_by: M1949 requires a calibration artifact before source-mining can be rerun with repaired fallback geometry
- supersedes: manual fallback geometry tuning, rerunning M1947 with the same stale fallback defaults
- invalidates: None

## Success Criteria

- focused tests pass
- runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/summary.json exists
- selected_anchor_fallback_geometry.json exists
- selected surfaces include post_friction_step and steady_surface
- selected center labels are aeb_feasible
- selected supported-anchor count floors pass
- guardrail violation count is zero

## Failure Criteria

- focused tests fail
- calibration summary is missing
- selected fallback geometry is missing or label-incorrect
- support floors fail
- reset rollout ranking or paper-level claims are made

## Evidence Gates

- M1950 must implement the calibration tool and focused tests
- M1950 must run only no-rollout classifier/source-mining calibration
- M1950 must write selected fallback geometry and calibration summary artifacts
- M1950 must keep reset rollout measured execution profile tuning ranking paper and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not relax stable-AEB anchors to accept aes_feasible labels
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1950-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-implementation
- type: infrastructure
- checkpoint: runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_anchor_fallback_geometry_calibration_pass_route_to_calibrated_source_mining_application_design
- reason: M1950 calibration pass selects label-correct stable-AEB fallback geometry at distance 52 half-width 0.75 for both surfaces with 64/64 supported anchors 4032 accepted cells and guardrail 0

## Next Blocker

m1950-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-implementation
