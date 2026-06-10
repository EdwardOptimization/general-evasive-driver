# m3104-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-result-audit Research Review

## Summary

- Generated at UTC: 20260607T203321Z
- Type: gate
- Gate tier: process
- Promotion decision: accept_m3103_materialization_route_to_m3105_full_fresh_measurement
- Decision reason: Completed: audit accepts M3103 v4 v2-fallback no-regression hard-safety direct-action repair materialization as complete and claim-safe with status_pass true gate_matrix_pass true required_artifacts_present true policy_id m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair rule_rows 5 no_regression_guard_rows 4 actor_input_exclusion_rows 10 claim_boundary_rows 21 low_speed_probe_throttle 0.3700000047683716 local_high_speed_obstacle_probe_brake 0.5479999780654907 local_high_speed_edge_probe_brake -0.46895238757133484 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false recurrent_hidden_state_required false; rejects measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result and self-ID claims; selects exactly one follow-up to M3105 full-fresh v4 repair measurement.

## Hypothesis

A bounded result audit can accept or reject the M3103 v4 v2-fallback no-regression hard-safety repair materialization artifacts before any measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-preflight.md, runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/direct_action_policy_config.json
- parent_dataset: runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/summary.json, runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/safety_reflex_rule_rows.csv, runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/no_regression_guard_rows.csv, runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/actor_input_exclusion_rows.csv, runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/claim_boundary_rows.csv, runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/gate_matrix.csv
- parent_config: experiments/manifests/m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-preflight.json
- parent_objective: audit v4 v2-fallback no-regression materialization before measurement admission
- derived_from: m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-preflight, m3102-engineering-controller-active-safety-driver-v3-regression-and-v2-fallback-hard-safety-repair-synthesis, m3100-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-preflight, m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight, m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight
- blocked_by: M3103 materialization artifacts require audit before measurement, materialization cannot support repair-success or driver-performance claims
- supersedes: direct measurement admission without v4 materialization audit
- invalidates: None

## Success Criteria

- docs/m3104-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-result-audit.md exists
- M3104 audits M3103 artifact row counts gates actor contract and claim boundaries
- M3104 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3104 selects exactly one next route or stop state

## Failure Criteria

- M3104 hides M3103 failures or missing artifacts
- M3104 treats M3103 materialization as measurement validation or performance verdict
- M3104 changes actor input or action contract
- M3104 leaves next route ambiguous

## Evidence Gates

- M3104 must audit M3103 summary rule config no-regression exclusion claim and gate artifacts
- M3104 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false
- M3104 must reject measurement validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3104 must select exactly one measurement artifact-repair synthesis or stop route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run measurement validation ranking promotion high-fidelity simulation fitting PPO or training
- do not treat M3103 materialization as driver-performance repair-success robustness-result or self-ID evidence
- do not change actor input action contract or runtime base-policy-free boundary

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

- milestone: m3104-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-result-audit
- type: gate
- checkpoint: docs/m3104-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: accept_m3103_materialization_route_to_m3105_full_fresh_measurement
- reason: Completed: audit accepts M3103 v4 v2-fallback no-regression hard-safety direct-action repair materialization as complete and claim-safe with status_pass true gate_matrix_pass true required_artifacts_present true policy_id m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair rule_rows 5 no_regression_guard_rows 4 actor_input_exclusion_rows 10 claim_boundary_rows 21 low_speed_probe_throttle 0.3700000047683716 local_high_speed_obstacle_probe_brake 0.5479999780654907 local_high_speed_edge_probe_brake -0.46895238757133484 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false recurrent_hidden_state_required false; rejects measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result and self-ID claims; selects exactly one follow-up to M3105 full-fresh v4 repair measurement.

## Next Blocker

m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight
