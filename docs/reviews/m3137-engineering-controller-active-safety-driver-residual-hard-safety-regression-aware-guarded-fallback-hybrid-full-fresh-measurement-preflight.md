# m3137-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-preflight Research Review

## Summary

- Generated at UTC: 20260608T001251Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_route_to_m3138_result_audit
- Decision reason: Completed: ran M3137 full-fresh M3135 guarded fallback hybrid measurement with status_pass true gate_matrix_pass true required_artifacts_present true 64/64 episode rows 0 execution failures 56 success 6 collision 2 offtrack 0 speed_too_low same_row_comparison_rows 256 exact_seed_matches all baselines 64 success_delta_vs_m3105 -1 collision_delta_vs_m3105 +1 offtrack_delta_vs_m3105 0 speed_too_low_delta_vs_m3105 0 actor obs72 current frame direct_action_clipped [steer throttle brake] runtime_base_policy_required false no validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim registered M3138 result audit.

## Hypothesis

A bounded full-fresh measurement preflight can execute the M3135 guarded fallback hybrid as the full obs72-to-action3 action source on the complete M3084 fresh denominator and write same-row comparison safety contract and claim-boundary artifacts against M3105 M3095 M3100 and M3090 before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3136-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-result-audit.md, runs/m3135_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_preflight/direct_action_policy_config.json
- parent_dataset: runs/m3135_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_preflight/summary.json, runs/m3135_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_preflight/gate_matrix.csv, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_measurement_episode_rows.csv, runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/measurement_episode_rows.csv
- parent_config: experiments/manifests/m3136-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-result-audit.json, experiments/manifests/m3135-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-preflight.json
- parent_objective: measure M3135 guarded fallback hybrid on the complete fresh denominator
- derived_from: m3136-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-result-audit, m3135-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-preflight, m3133-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-regression-failure-decomposition-materialization-preflight, m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight
- blocked_by: M3135 is only materialized and needs full-fresh measurement before any behavior interpretation, M3137 must preserve same-row denominator alignment against M3105 M3095 M3100 and M3090
- supersedes: interpreting M3135 action probes as measured repair success
- invalidates: None

## Success Criteria

- runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/summary.json reports status_pass true and gate_matrix_pass true
- M3137 writes 64 measurement episode rows and zero measurement failure rows
- M3137 writes 256 same-row comparison rows and registers M3138 result audit

## Failure Criteria

- M3137 drops rows from the full fresh denominator
- M3137 violates the actor-visible obs72-to-action3 direct-action contract
- M3137 claims validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID evidence

## Evidence Gates

- M3137 must execute exactly the complete M3084 64-row fresh denominator
- M3137 must use the M3135 guarded fallback hybrid as the full obs72-to-action3 action source
- M3137 must write same-row comparisons against M3105 M3095 M3100 and M3090 with exact seed alignment
- M3137 must preserve obs72/action3 direct [steer throttle brake] contract and runtime_base_policy_required false
- M3137 must not claim validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID evidence
- M3137 must register M3138 result audit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune expand rank promote validate or mutate checkpoints
- do not use hidden oracle target TTC source route outcome progress verdict baseline outcome or M3133 row labels as actor inputs
- do not convert M3137 same-row deltas into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID claims

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

- milestone: m3137-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-preflight
- type: infrastructure
- checkpoint: runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/summary.json
- success_rate: 0.875
- termination_rate: None
- clearance_margin_mean: 10.975710800230118
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_route_to_m3138_result_audit
- reason: Completed: ran M3137 full-fresh M3135 guarded fallback hybrid measurement with status_pass true gate_matrix_pass true required_artifacts_present true 64/64 episode rows 0 execution failures 56 success 6 collision 2 offtrack 0 speed_too_low same_row_comparison_rows 256 exact_seed_matches all baselines 64 success_delta_vs_m3105 -1 collision_delta_vs_m3105 +1 offtrack_delta_vs_m3105 0 speed_too_low_delta_vs_m3105 0 actor obs72 current frame direct_action_clipped [steer throttle brake] runtime_base_policy_required false no validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim registered M3138 result audit.

## Next Blocker

m3138-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-result-audit
