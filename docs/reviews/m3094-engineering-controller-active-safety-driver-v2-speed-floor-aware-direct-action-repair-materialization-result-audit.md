# m3094-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-result-audit Research Review

## Summary

- Generated at UTC: 20260607T193006Z
- Type: gate
- Gate tier: process
- Promotion decision: accept_m3093_materialization_route_to_m3095_full_fresh_measurement
- Decision reason: Completed: audit accepts M3093 v2 speed-floor-aware direct-action repair materialization as complete and claim-safe with status_pass true gate_matrix_pass true required_artifacts_present true policy_id m3093_speed_floor_aware_balanced_direct_action_repair_v2 rule_rows 5 actor_input_exclusion_rows 10 claim_boundary_rows 20 low_speed_probe_throttle 0.3700000047683716 urgent_obstacle_probe_brake 0.4399999976158142 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false recurrent_hidden_state_required false; rejects measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result and self-ID claims; selects exactly one follow-up to M3095 full-fresh v2 repair measurement.

## Hypothesis

A bounded result audit can accept or reject the M3093 v2 speed-floor-aware direct-action repair materialization artifacts before any measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight.md, runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/direct_action_policy_config.json
- parent_dataset: runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/summary.json, runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/safety_reflex_rule_rows.csv, runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/actor_input_exclusion_rows.csv, runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/claim_boundary_rows.csv, runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/gate_matrix.csv
- parent_config: experiments/manifests/m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight.json
- parent_objective: audit v2 speed-floor-aware repair materialization before measurement admission
- derived_from: m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight, m3092-engineering-controller-active-safety-driver-v1-full-fresh-runtime-behavior-negative-repair-synthesis, m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-preflight
- blocked_by: M3093 materialization artifacts require audit before measurement, materialization cannot support repair-success or driver-performance claims
- supersedes: direct measurement admission without v2 repair artifact audit
- invalidates: None

## Success Criteria

- docs/m3094-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-result-audit.md exists
- M3094 audits M3093 artifact row counts gates actor contract and claim boundaries
- M3094 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3094 selects exactly one next route or stop state

## Failure Criteria

- M3094 hides M3093 failures or missing artifacts
- M3094 treats M3093 materialization as measurement validation or performance verdict
- M3094 changes actor input or action contract
- M3094 leaves next route ambiguous

## Evidence Gates

- M3094 must audit M3093 summary rule config exclusion claim and gate artifacts
- M3094 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false
- M3094 must reject validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3094 must select exactly one measurement, artifact-repair, synthesis, or stop route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run measurement validation ranking promotion high-fidelity simulation fitting PPO or training
- do not treat M3093 materialization as driver-performance repair-success robustness-result or self-ID evidence
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

- milestone: m3094-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-result-audit
- type: gate
- checkpoint: docs/m3094-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: accept_m3093_materialization_route_to_m3095_full_fresh_measurement
- reason: Completed: audit accepts M3093 v2 speed-floor-aware direct-action repair materialization as complete and claim-safe with status_pass true gate_matrix_pass true required_artifacts_present true policy_id m3093_speed_floor_aware_balanced_direct_action_repair_v2 rule_rows 5 actor_input_exclusion_rows 10 claim_boundary_rows 20 low_speed_probe_throttle 0.3700000047683716 urgent_obstacle_probe_brake 0.4399999976158142 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false recurrent_hidden_state_required false; rejects measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result and self-ID claims; selects exactly one follow-up to M3095 full-fresh v2 repair measurement.

## Next Blocker

m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight
