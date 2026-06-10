# m3097-engineering-controller-active-safety-driver-v2-residual-collision-offtrack-hard-safety-repair-synthesis Research Review

## Summary

- Generated at UTC: 20260607T203305Z
- Type: gate
- Gate tier: process
- Promotion decision: route_to_m3098_v3_high_speed_obstacle_edge_hard_safety_repair_materialization
- Decision reason: Completed: residual hard-safety synthesis classifies M3095 remaining failures as 7/64 all T5 rows: 5 obstacle_collision and 2 off_track, concentrated in collision_lateral_intrusion and offtrack_boundary_recovery; speed_floor_stress and stability_action_pressure are 16/16 success, speed_too_low is 0, but collision count remains 5 and offtrack remains 2, so M3095 is not repair-success validation or performance evidence. Selects exactly one follow-up to M3098 v3 high-speed obstacle/edge hard-safety direct-action repair materialization while preserving obs72/action3 direct [steer throttle brake] runtime_base_policy_required false and forbidding hidden actor inputs.

## Hypothesis

A bounded residual hard-safety repair synthesis can classify the M3095 remaining collision and offtrack failures and select exactly one direct-action repair materialization route before any validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3096-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-result-audit.md, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/summary.json, runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/direct_action_policy_config.json
- parent_dataset: runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/measurement_failure_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/measurement_metric_summary_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/same_row_comparison_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/measurement_contract_guard_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/claim_boundary_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/gate_matrix.csv
- parent_config: experiments/manifests/m3096-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-result-audit.json, experiments/manifests/m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight.json, experiments/manifests/m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight.json
- parent_objective: classify residual hard-safety blockers after v2 speed-floor-aware measurement
- derived_from: m3096-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-result-audit, m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight, m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight, m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-preflight
- blocked_by: M3095 still has 5 obstacle-collision failures and 2 off-track failures, M3095 measurement cannot support validation repair-success or performance claims before residual hard-safety synthesis
- supersedes: direct validation planning from M3095 speed-floor improvement
- invalidates: None

## Success Criteria

- docs/m3097-engineering-controller-active-safety-driver-v2-residual-collision-offtrack-hard-safety-repair-synthesis.md exists
- M3097 classifies all M3095 residual collision and offtrack failures
- M3097 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3097 selects exactly one next route or stop state

## Failure Criteria

- M3097 hides residual M3095 collision or offtrack failures
- M3097 treats M3095 measurement as validation repair-success or performance verdict
- M3097 changes actor input or action contract
- M3097 leaves next route ambiguous

## Evidence Gates

- M3097 must audit and classify all residual M3095 collision and offtrack rows
- M3097 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false
- M3097 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3097 must select exactly one bounded repair materialization synthesis stop or artifact-repair route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun tune expand rank promote validate or mutate checkpoints
- do not use hidden oracle TTC target source route outcome progress verdict or M3095 failure labels as actor input
- do not treat M3095 success delta as repair-success driver-performance current-sim robustness-result high-fidelity paper full-driver or self-ID evidence
- do not ignore the 5 collision failures while optimizing speed or offtrack only

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

- milestone: m3097-engineering-controller-active-safety-driver-v2-residual-collision-offtrack-hard-safety-repair-synthesis
- type: gate
- checkpoint: docs/m3097-engineering-controller-active-safety-driver-v2-residual-collision-offtrack-hard-safety-repair-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_m3098_v3_high_speed_obstacle_edge_hard_safety_repair_materialization
- reason: Completed: residual hard-safety synthesis classifies M3095 remaining failures as 7/64 all T5 rows: 5 obstacle_collision and 2 off_track, concentrated in collision_lateral_intrusion and offtrack_boundary_recovery; speed_floor_stress and stability_action_pressure are 16/16 success, speed_too_low is 0, but collision count remains 5 and offtrack remains 2, so M3095 is not repair-success validation or performance evidence. Selects exactly one follow-up to M3098 v3 high-speed obstacle/edge hard-safety direct-action repair materialization while preserving obs72/action3 direct [steer throttle brake] runtime_base_policy_required false and forbidding hidden actor inputs.

## Next Blocker

m3098-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-materialization-preflight
