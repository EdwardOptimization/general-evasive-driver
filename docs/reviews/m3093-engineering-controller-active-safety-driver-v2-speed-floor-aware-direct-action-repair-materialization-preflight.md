# m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260607T192544Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: route_to_m3094_speed_floor_aware_repair_materialization_result_audit
- Decision reason: Completed: materialized M3093 v2 speed-floor-aware balanced direct-action repair artifacts with status_pass true gate_matrix_pass true required_artifacts_present true policy_id m3093_speed_floor_aware_balanced_direct_action_repair_v2 rule_rows 5 actor_input_exclusion_rows 10 claim_boundary_rows 20 gate_rows 25 low_speed_probe_throttle 0.3700000047683716 urgent_obstacle_probe_brake 0.4399999976158142 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false recurrent_hidden_state_required false; no reset step rollout replay fitting PPO training measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim; registered M3094 result audit.

## Hypothesis

A bounded v2 speed-floor-aware balanced direct-action repair materialization can produce actor-visible obs72-to-action3 rule and config artifacts that target M3090 speed-too-low, collision, and offtrack blockers while preserving claim boundaries before any measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3092-engineering-controller-active-safety-driver-v1-full-fresh-runtime-behavior-negative-repair-synthesis.md, src/autodrift/active_safety_reflex_driver.py, src/autodrift/engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight.py
- parent_dataset: runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/summary.json, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_measurement_episode_rows.csv, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_measurement_metric_summary_rows.csv, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_parity_rows.csv
- parent_config: experiments/manifests/m3092-engineering-controller-active-safety-driver-v1-full-fresh-runtime-behavior-negative-repair-synthesis.json, experiments/manifests/m3091-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-result-audit.json
- parent_objective: materialize one bounded speed-floor-aware direct-action repair route selected by M3092
- derived_from: m3092-engineering-controller-active-safety-driver-v1-full-fresh-runtime-behavior-negative-repair-synthesis, m3091-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-result-audit, m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-preflight, m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight
- blocked_by: M3090 has 11 speed-too-low, 5 collision, and 5 offtrack blockers, M3092 selects repair materialization before any validation or promotion route
- supersedes: v1 deterministic safety-reflex rule/config as the only active candidate
- invalidates: None

## Success Criteria

- runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/summary.json reports status_pass true and gate_matrix_pass true
- runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/direct_action_policy_config.json contains v2 speed-floor-aware direct-action repair config
- runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/safety_reflex_rule_rows.csv records the speed-floor recovery, obstacle safety, road recovery, stability, and action-bound rules
- runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/actor_input_exclusion_rows.csv rejects hidden oracle TTC target source route outcome progress and verdict actor inputs
- runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/claim_boundary_rows.csv rejects validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- experiments/manifests/m3094-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-result-audit.json is created and pending

## Failure Criteria

- M3093 changes observation shape action shape action component order or direct-action semantics
- M3093 uses hidden oracle TTC target source route outcome progress or verdict labels as actor input
- M3093 requires runtime base policy checkpoint model recurrent hidden state or checkpoint mutation
- M3093 claims measurement validation performance repair success robustness success or promotion

## Evidence Gates

- M3093 must materialize v2 rule/config artifacts that preserve obs72/action3 direct [steer throttle brake] output
- M3093 must add speed-floor-aware throttle/brake release using only actor-visible ego velocity and existing actor-visible urgency features
- M3093 must preserve urgent obstacle and road-corridor safety branches without hidden oracle TTC target source route outcome progress or verdict actor inputs
- M3093 must write claim-boundary and actor-input exclusion guards and register M3094 result audit
- M3093 must not run measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run reset step rollout replay fitting PPO training validation ranking promotion or high-fidelity simulation in M3093
- do not use hidden oracle TTC target source route outcome progress verdict labels or M3090 outcome labels as actor input
- do not mutate or promote a checkpoint
- do not claim repair success or robustness success from materialization artifacts

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

- milestone: m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight
- type: infrastructure
- checkpoint: runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_m3094_speed_floor_aware_repair_materialization_result_audit
- reason: Completed: materialized M3093 v2 speed-floor-aware balanced direct-action repair artifacts with status_pass true gate_matrix_pass true required_artifacts_present true policy_id m3093_speed_floor_aware_balanced_direct_action_repair_v2 rule_rows 5 actor_input_exclusion_rows 10 claim_boundary_rows 20 gate_rows 25 low_speed_probe_throttle 0.3700000047683716 urgent_obstacle_probe_brake 0.4399999976158142 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false recurrent_hidden_state_required false; no reset step rollout replay fitting PPO training measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim; registered M3094 result audit.

## Next Blocker

m3094-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-result-audit
