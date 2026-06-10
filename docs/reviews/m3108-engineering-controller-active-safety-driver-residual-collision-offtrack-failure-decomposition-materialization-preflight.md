# m3108-engineering-controller-active-safety-driver-residual-collision-offtrack-failure-decomposition-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260607T211900Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_residual_collision_offtrack_decomposition_route_to_m3109_result_audit
- Decision reason: Completed: materialized M3108 residual collision offtrack failure decomposition artifacts with status_pass true gate_matrix_pass true required_artifacts_present true source_rows 64 residual_rows 7 collisions 5 offtracks 2 speed_too_low 0 axes collision_lateral_intrusion and offtrack_boundary_recovery residual_comparison_rows 21 repair_requirement_rows 7 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false no_new_execution true no validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim registered M3109 result audit.

## Hypothesis

A no-new-execution materialization can convert the M3107-selected M3105 residual collision/offtrack failures into row-preserving failure, comparison, axis, repair-requirement, contract, and claim-boundary artifacts before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis.md, docs/m3106-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-result-audit.md
- parent_dataset: runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/summary.json, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/same_row_comparison_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv
- parent_config: experiments/manifests/m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis.json, experiments/manifests/m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight.json
- parent_objective: materialize residual collision/offtrack decomposition after M3107 pivot
- derived_from: m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis, m3106-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-result-audit, m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight, m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight
- blocked_by: M3105 leaves 5 obstacle_collision and 2 off_track failures, M3107 pivots away from narrow v4 no-regression continuation toward residual failure decomposition
- supersedes: unstructured residual hard-safety blocker notes
- invalidates: None

## Success Criteria

- runs/m3108_engineering_controller_active_safety_driver_residual_collision_offtrack_failure_decomposition_materialization_preflight/summary.json reports status_pass true and gate_matrix_pass true
- runs/m3108_engineering_controller_active_safety_driver_residual_collision_offtrack_failure_decomposition_materialization_preflight/residual_failure_rows.csv records 7 residual non-success rows
- runs/m3108_engineering_controller_active_safety_driver_residual_collision_offtrack_failure_decomposition_materialization_preflight/residual_axis_summary_rows.csv classifies collision_lateral_intrusion and offtrack_boundary_recovery blockers
- runs/m3108_engineering_controller_active_safety_driver_residual_collision_offtrack_failure_decomposition_materialization_preflight/residual_repair_requirement_rows.csv records next repair requirements without repair-success claims
- experiments/manifests/m3109-engineering-controller-active-safety-driver-residual-collision-offtrack-failure-decomposition-result-audit.json is created and pending

## Failure Criteria

- M3108 runs environment reset step rollout replay fitting training validation ranking promotion or checkpoint mutation
- M3108 drops any residual failure row or changes row identity
- M3108 makes validation driver-performance current-sim robustness-result high-fidelity full-driver repair-success or self-ID claims
- M3108 requires hidden actor inputs runtime base policy or baseline outcome actor inputs

## Evidence Gates

- M3108 must perform no new environment execution training fitting validation ranking promotion or checkpoint mutation
- M3108 must preserve all 64 M3105 rows and explicitly materialize the 7 residual non-success rows
- M3108 must classify residual failures by axis binding role termination clearance stability speed and action pressure
- M3108 must preserve obs72/action3 direct [steer throttle brake] runtime_base_policy_required false and hidden-input exclusions
- M3108 must register M3109 result audit before any repair materialization or measurement route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun tune expand rank promote validate or mutate checkpoints
- do not treat decomposition rows as validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success or self-ID evidence
- do not use hidden oracle TTC target source route outcome progress verdict labels or baseline outcomes as actor input

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit
- proof_washout
- seed_fragility

## Scoreboard

- milestone: m3108-engineering-controller-active-safety-driver-residual-collision-offtrack-failure-decomposition-materialization-preflight
- type: infrastructure
- checkpoint: runs/m3108_engineering_controller_active_safety_driver_residual_collision_offtrack_failure_decomposition_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_residual_collision_offtrack_decomposition_route_to_m3109_result_audit
- reason: Completed: materialized M3108 residual collision offtrack failure decomposition artifacts with status_pass true gate_matrix_pass true required_artifacts_present true source_rows 64 residual_rows 7 collisions 5 offtracks 2 speed_too_low 0 axes collision_lateral_intrusion and offtrack_boundary_recovery residual_comparison_rows 21 repair_requirement_rows 7 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false no_new_execution true no validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim registered M3109 result audit.

## Next Blocker

m3108-engineering-controller-active-safety-driver-residual-collision-offtrack-failure-decomposition-materialization-preflight
