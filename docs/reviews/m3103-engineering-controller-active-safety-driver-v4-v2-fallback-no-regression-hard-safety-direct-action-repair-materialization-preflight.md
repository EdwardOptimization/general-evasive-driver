# m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260607T203321Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v4_v2_fallback_no_regression_hard_safety_repair_materialization_route_to_m3104_result_audit
- Decision reason: Completed: materialized M3103 v4 v2-fallback no-regression hard-safety direct-action repair artifacts with status_pass true gate_matrix_pass true required_artifacts_present true policy_id m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair rule_rows 5 no_regression_guard_rows 4 actor_input_exclusion_rows 10 claim_boundary_rows 21 gate_rows 28 low_speed_probe_throttle 0.3700000047683716 local_high_speed_obstacle_probe_brake 0.5479999780654907 local_high_speed_edge_probe_brake -0.46895238757133484 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false recurrent_hidden_state_required false; no reset step rollout replay fitting PPO training measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim; registered M3104 result audit.

## Hypothesis

A bounded v4 v2-fallback no-regression hard-safety direct-action repair materialization can produce actor-visible obs72-to-action3 rule and config artifacts that target M3095 residual hard-safety failures while explicitly preserving M3095 speed-floor behavior and M3100 regression rows before any measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3102-engineering-controller-active-safety-driver-v3-regression-and-v2-fallback-hard-safety-repair-synthesis.md, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/summary.json, runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/direct_action_policy_config.json
- parent_dataset: runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/same_row_comparison_rows.csv, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/summary.json, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/same_row_comparison_rows.csv
- parent_config: experiments/manifests/m3102-engineering-controller-active-safety-driver-v3-regression-and-v2-fallback-hard-safety-repair-synthesis.json, experiments/manifests/m3100-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-preflight.json, experiments/manifests/m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight.json, experiments/manifests/m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight.json
- parent_objective: materialize a v4 repair from the M3095 fallback base with no-regression guards after M3100 regressed
- derived_from: m3102-engineering-controller-active-safety-driver-v3-regression-and-v2-fallback-hard-safety-repair-synthesis, m3101-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-result-audit, m3100-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-preflight, m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight, m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight
- blocked_by: M3100 global high-speed overlay regressed against M3095, M3095 still has 5 obstacle-collision and 2 offtrack residual hard-safety failures
- supersedes: continuing the M3098/M3100 v3 overlay without no-regression guards
- invalidates: None

## Success Criteria

- runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/summary.json reports status_pass true and gate_matrix_pass true
- runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/direct_action_policy_config.json materializes obs72/action3 direct [steer throttle brake] with runtime_base_policy_required false
- runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/no_regression_guard_rows.csv includes M3095 speed-floor and M3100 regression-row guards
- runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/claim_boundary_rows.csv rejects measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- experiments/manifests/m3104-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-result-audit.json is created and pending

## Failure Criteria

- M3103 changes observation shape action shape action component order or direct-action semantics
- M3103 requires runtime base policy residual adapter checkpoint model hidden state or hidden actor input
- M3103 omits no-regression guards for M3095 speed-floor or M3100 regression rows
- M3103 makes measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claims

## Evidence Gates

- M3103 must materialize artifacts only and run no reset step rollout replay fitting training validation ranking promotion high-fidelity simulation or self-ID test
- M3103 must preserve obs72/action3 direct [steer throttle brake], runtime_base_policy_required false, checkpoint_model_required false, and no recurrent hidden state
- M3103 must include no-regression guard rows for M3095 speed-floor behavior and M3100 regression rows 0014 and 0048
- M3103 must reject measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3103 must register M3104 result audit before any measurement route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run measurement validation ranking promotion high-fidelity simulation fitting PPO or training
- do not treat materialization as driver-performance repair-success robustness-result or self-ID evidence
- do not use hidden oracle TTC target source route outcome progress verdict labels or M3095/M3100 outcome labels as actor input
- do not preserve the M3100 global throttle suppression pattern without explicit no-regression guards

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

- milestone: m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-preflight
- type: infrastructure
- checkpoint: runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v4_v2_fallback_no_regression_hard_safety_repair_materialization_route_to_m3104_result_audit
- reason: Completed: materialized M3103 v4 v2-fallback no-regression hard-safety direct-action repair artifacts with status_pass true gate_matrix_pass true required_artifacts_present true policy_id m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair rule_rows 5 no_regression_guard_rows 4 actor_input_exclusion_rows 10 claim_boundary_rows 21 gate_rows 28 low_speed_probe_throttle 0.3700000047683716 local_high_speed_obstacle_probe_brake 0.5479999780654907 local_high_speed_edge_probe_brake -0.46895238757133484 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false recurrent_hidden_state_required false; no reset step rollout replay fitting PPO training measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim; registered M3104 result audit.

## Next Blocker

m3104-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-result-audit
