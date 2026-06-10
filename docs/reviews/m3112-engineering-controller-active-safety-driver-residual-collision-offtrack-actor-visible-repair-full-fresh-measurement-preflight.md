# m3112-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-full-fresh-measurement-preflight Research Review

## Summary

- Generated at UTC: 20260607T213722Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_residual_collision_offtrack_actor_visible_repair_full_fresh_measurement_route_to_m3113_result_audit
- Decision reason: Completed: ran M3112 full-fresh M3110 residual actor-visible repair measurement with status_pass true gate_matrix_pass true required_artifacts_present true 64/64 episode rows 0 execution failures 57 success 5 collision 2 offtrack 0 speed_too_low same_row_comparison_rows 256 exact_seed_matches_m3105 64 exact_seed_matches_m3095 64 exact_seed_matches_m3100 64 exact_seed_matches_m3090 64 success_delta_vs_m3105 0 collision_delta_vs_m3105 0 offtrack_delta_vs_m3105 0 speed_too_low_delta_vs_m3105 0 success_delta_vs_m3095 0 collision_delta_vs_m3095 0 offtrack_delta_vs_m3095 0 speed_too_low_delta_vs_m3095 0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false no validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim registered M3113 result audit.

## Hypothesis

A bounded full-fresh measurement preflight can execute the M3110 residual collision offtrack actor-visible repair as the full obs72-to-action3 action source on the complete M3084 fresh denominator and write same-row comparison safety contract and claim-boundary artifacts against M3105 M3095 M3100 and M3090 before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3111-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-materialization-result-audit.md, runs/m3110_engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_preflight/direct_action_policy_config.json
- parent_dataset: runs/m3110_engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_preflight/summary.json, runs/m3110_engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_preflight/residual_repair_guard_rows.csv, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_measurement_episode_rows.csv, runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/measurement_episode_rows.csv
- parent_config: experiments/manifests/m3111-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-materialization-result-audit.json, experiments/manifests/m3110-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-materialization-preflight.json
- parent_objective: measure the M3110 actor-visible residual collision/offtrack repair on the complete fresh denominator
- derived_from: m3111-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-materialization-result-audit, m3110-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-materialization-preflight, m3108-engineering-controller-active-safety-driver-residual-collision-offtrack-failure-decomposition-materialization-preflight, m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight, m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight, m3100-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-preflight, m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-preflight
- blocked_by: M3110 materialization must be measured before any repair-success or behavior interpretation, M3105 still has 5 collision and 2 offtrack residual hard-safety failures, speed-too-low must remain 0 on the same denominator
- supersedes: interpreting M3110 materialization probes as behavior evidence
- invalidates: None

## Success Criteria

- runs/m3112_engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_full_fresh_measurement_preflight/summary.json reports status_pass true and gate_matrix_pass true
- M3112 accounts all 64 M3084 fresh denominator rows with zero execution failures
- M3112 writes same-row comparison rows against M3105 M3095 M3100 and M3090
- M3112 preserves obs72/action3 direct [steer throttle brake] with runtime_base_policy_required false
- M3112 registers M3113 result audit before any repair-success or validation interpretation

## Failure Criteria

- M3112 drops denominator rows or records execution failures
- M3112 changes observation shape action shape action component order or direct-action semantics
- M3112 requires runtime base policy residual adapter checkpoint model hidden state or hidden actor input
- M3112 makes validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claims

## Evidence Gates

- M3112 must execute the complete 64-row M3084 fresh denominator through the M3110 direct-action function
- M3112 must preserve obs72/action3 direct [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false and no recurrent hidden state
- M3112 must write same-row comparisons against M3105 M3095 M3100 and M3090 with exact seed matches
- M3112 must report success collision offtrack speed-too-low clearance stability and action metrics separately
- M3112 must reject validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3112 must register M3113 result audit before any interpretation route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune expand rank promote validate or mutate checkpoints during M3112
- do not use hidden oracle TTC target source route outcome progress verdict labels or baseline outcomes as actor input
- do not convert same-row deltas into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success or self-ID claims
- do not drop any M3084 fresh denominator row

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

- milestone: m3112-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-full-fresh-measurement-preflight
- type: infrastructure
- checkpoint: runs/m3112_engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_full_fresh_measurement_preflight/summary.json
- success_rate: 0.890625
- termination_rate: None
- clearance_margin_mean: 10.981421651533854
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_residual_collision_offtrack_actor_visible_repair_full_fresh_measurement_route_to_m3113_result_audit
- reason: Completed: ran M3112 full-fresh M3110 residual actor-visible repair measurement with status_pass true gate_matrix_pass true required_artifacts_present true 64/64 episode rows 0 execution failures 57 success 5 collision 2 offtrack 0 speed_too_low same_row_comparison_rows 256 exact_seed_matches_m3105 64 exact_seed_matches_m3095 64 exact_seed_matches_m3100 64 exact_seed_matches_m3090 64 success_delta_vs_m3105 0 collision_delta_vs_m3105 0 offtrack_delta_vs_m3105 0 speed_too_low_delta_vs_m3105 0 success_delta_vs_m3095 0 collision_delta_vs_m3095 0 offtrack_delta_vs_m3095 0 speed_too_low_delta_vs_m3095 0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false no validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim registered M3113 result audit.

## Next Blocker

m3113-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-full-fresh-measurement-result-audit
