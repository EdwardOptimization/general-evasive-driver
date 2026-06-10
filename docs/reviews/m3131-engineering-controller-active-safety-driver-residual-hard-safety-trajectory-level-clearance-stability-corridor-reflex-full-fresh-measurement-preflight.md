# m3131-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-full-fresh-measurement-preflight Research Review

## Summary

- Generated at UTC: 20260607T233135Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_full_fresh_measurement_route_to_m3132_result_audit
- Decision reason: Completed: ran M3131 full-fresh M3129 corridor reflex measurement with status_pass true gate_matrix_pass true required_artifacts_present true 64/64 episode rows 0 execution failures 35 success 7 collision 14 offtrack 8 speed_too_low same_row_comparison_rows 256 exact_seed_matches all baselines 64 success_delta_vs_m3105 -22 collision_delta_vs_m3105 +2 offtrack_delta_vs_m3105 +12 speed_too_low_delta_vs_m3105 +8 clearance_margin_mean 8.551778383515293 actor obs72 current frame direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false recurrent_hidden_state_required false no validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim registered M3132 result audit.

## Hypothesis

A bounded full-fresh measurement preflight can execute the M3129 residual trajectory-level clearance/stability corridor-reflex direct-action repair as the full obs72-to-action3 action source on the complete M3084 fresh denominator and write same-row comparison safety contract and claim-boundary artifacts against M3105 M3095 M3100 and M3090 before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3130-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-materialization-result-audit.md, runs/m3129_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_preflight/direct_action_policy_config.json
- parent_dataset: runs/m3129_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_preflight/summary.json, runs/m3129_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_preflight/trajectory_level_corridor_rule_rows.csv, runs/m3129_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_preflight/runtime_contract_rows.csv, runs/m3129_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_preflight/actor_input_exclusion_rows.csv, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_measurement_episode_rows.csv, runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/measurement_episode_rows.csv
- parent_config: experiments/manifests/m3130-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-materialization-result-audit.json, experiments/manifests/m3129-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-materialization-preflight.json
- parent_objective: execute M3129 materialized direct-action repair on the full fresh denominator
- derived_from: m3130-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-materialization-result-audit, m3129-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-materialization-preflight, m3128-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-controller-architecture-diagnostic-result-audit, m3127-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-controller-architecture-diagnostic-materialization-preflight
- blocked_by: M3129 materialization must be measured before behavior interpretation, M3129 is not repair-success or performance evidence until full fresh measurement and result audit
- supersedes: direct interpretation of M3129 materialization without full fresh measurement
- invalidates: None

## Success Criteria

- runs/m3131_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_full_fresh_measurement_preflight/summary.json reports status_pass true and gate_matrix_pass true
- M3131 writes complete 64-row measurement artifacts and same-row comparison artifacts
- M3131 preserves actor 72/action 3 direct [steer throttle brake] and runtime_base_policy_required false
- M3131 registers M3132 result audit

## Failure Criteria

- M3131 drops full-fresh row identity or changes denominator
- M3131 requires hidden actor input runtime base policy checkpoint model or recurrent hidden state
- M3131 claims validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID evidence

## Evidence Gates

- M3131 must execute exactly the complete 64-row M3084 fresh denominator
- M3131 must preserve obs72/action3 direct [steer throttle brake] and runtime_base_policy_required false
- M3131 must write same-row comparisons against M3105 M3095 M3100 and M3090
- M3131 must not claim validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID evidence
- M3131 must register M3132 result audit before any verdict

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune expand rank promote validate or mutate checkpoints
- do not use hidden oracle TTC target source route outcome progress verdict labels or baseline outcomes as actor input
- do not treat M3131 measurement rows as repair-success or driver-performance evidence before M3132 audit

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

- milestone: m3131-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-full-fresh-measurement-preflight
- type: infrastructure
- checkpoint: runs/m3131_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_full_fresh_measurement_preflight/summary.json
- success_rate: 0.546875
- termination_rate: None
- clearance_margin_mean: 8.551778383515293
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_full_fresh_measurement_route_to_m3132_result_audit
- reason: Completed: ran M3131 full-fresh M3129 corridor reflex measurement with status_pass true gate_matrix_pass true required_artifacts_present true 64/64 episode rows 0 execution failures 35 success 7 collision 14 offtrack 8 speed_too_low same_row_comparison_rows 256 exact_seed_matches all baselines 64 success_delta_vs_m3105 -22 collision_delta_vs_m3105 +2 offtrack_delta_vs_m3105 +12 speed_too_low_delta_vs_m3105 +8 clearance_margin_mean 8.551778383515293 actor obs72 current frame direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false recurrent_hidden_state_required false no validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim registered M3132 result audit.

## Next Blocker

m3132-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-full-fresh-measurement-result-audit
