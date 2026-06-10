# m3102-engineering-controller-active-safety-driver-v3-regression-and-v2-fallback-hard-safety-repair-synthesis Research Review

## Summary

- Generated at UTC: 20260607T203320Z
- Type: gate
- Gate tier: process
- Promotion decision: route_to_m3103_v4_v2_fallback_no_regression_hard_safety_repair_materialization
- Decision reason: Completed: synthesis classifies M3100 as complete and claim-safe but behavior-regressive versus M3095 on the same 64-row denominator: 55 success versus M3095 57, success_delta -2, collision_delta 0, offtrack_delta +1, speed_too_low_delta +1, no same-row success improvements over M3095, and two regressions at comparison rows 0014 off_track from M3095 success and 0048 speed_too_low from M3095 success. M3100 keeps 5 collision failures and adds one offtrack and one speed-floor failure, so it is not validation repair-success performance current-sim verdict robustness-result high-fidelity paper full-driver or self-ID evidence. Selects exactly one follow-up to M3103 v4 v2-fallback no-regression hard-safety direct-action repair materialization while preserving obs72/action3 direct [steer throttle brake] runtime_base_policy_required false and forbidding hidden actor inputs.

## Hypothesis

A bounded synthesis can classify the M3100 v3 regression against M3095 and select exactly one v2-fallback hard-safety repair route, v3 artifact-repair route, or stop state before any validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3101-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-result-audit.md, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/summary.json, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/summary.json
- parent_dataset: runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/same_row_comparison_rows.csv, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_metric_summary_rows.csv, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_contract_guard_rows.csv, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/claim_boundary_rows.csv, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/gate_matrix.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/same_row_comparison_rows.csv
- parent_config: experiments/manifests/m3101-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-result-audit.json, experiments/manifests/m3100-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-preflight.json, experiments/manifests/m3098-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-materialization-preflight.json, experiments/manifests/m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight.json
- parent_objective: classify v3 hard-safety overlay regression against M3095 and choose a bounded next route
- derived_from: m3101-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-result-audit, m3100-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-preflight, m3098-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-materialization-preflight, m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight
- blocked_by: M3100 regresses against M3095 by -2 successes +1 offtrack +1 speed_too_low and unchanged 5 collisions, M3100 measurement cannot support validation repair-success or performance claims before regression synthesis
- supersedes: continuing v3 high-speed obstacle/edge overlay repairs without auditing the M3095 regression
- invalidates: None

## Success Criteria

- docs/m3102-engineering-controller-active-safety-driver-v3-regression-and-v2-fallback-hard-safety-repair-synthesis.md exists
- M3102 classifies M3100 regressions against M3095
- M3102 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3102 selects exactly one next route or stop state

## Failure Criteria

- M3102 hides M3100 regression against M3095
- M3102 treats M3100 measurement as validation repair-success or performance verdict
- M3102 changes actor input or action contract
- M3102 leaves next route ambiguous

## Evidence Gates

- M3102 must audit M3100 against M3095 on the same 64-row denominator
- M3102 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false
- M3102 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3102 must select exactly one bounded next route or stop state

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun tune expand rank promote validate or mutate checkpoints
- do not use hidden oracle TTC target source route outcome progress verdict or M3100/M3095 outcome labels as actor input
- do not treat M3100 aggregate improvement over M3090 as repair-success driver-performance current-sim robustness-result high-fidelity paper full-driver or self-ID evidence
- do not ignore the M3100 regression against M3095 while optimizing clearance margin only

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

- milestone: m3102-engineering-controller-active-safety-driver-v3-regression-and-v2-fallback-hard-safety-repair-synthesis
- type: gate
- checkpoint: docs/m3102-engineering-controller-active-safety-driver-v3-regression-and-v2-fallback-hard-safety-repair-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_m3103_v4_v2_fallback_no_regression_hard_safety_repair_materialization
- reason: Completed: synthesis classifies M3100 as complete and claim-safe but behavior-regressive versus M3095 on the same 64-row denominator: 55 success versus M3095 57, success_delta -2, collision_delta 0, offtrack_delta +1, speed_too_low_delta +1, no same-row success improvements over M3095, and two regressions at comparison rows 0014 off_track from M3095 success and 0048 speed_too_low from M3095 success. M3100 keeps 5 collision failures and adds one offtrack and one speed-floor failure, so it is not validation repair-success performance current-sim verdict robustness-result high-fidelity paper full-driver or self-ID evidence. Selects exactly one follow-up to M3103 v4 v2-fallback no-regression hard-safety direct-action repair materialization while preserving obs72/action3 direct [steer throttle brake] runtime_base_policy_required false and forbidding hidden actor inputs.

## Next Blocker

m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-preflight
