# m3080-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-closed-loop-measurement-preflight Research Review

## Summary

- Generated at UTC: 20260607T174108Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_measurement_route_to_m3081_result_audit
- Decision reason: Completed: ran same-denominator current-sim measurement for the M3078 deterministic direct-action safety-reflex actor with status_pass True gate_matrix_pass True required_artifacts_present True 32/32 episode rows 0 failures 19 success 3 collision 3 offtrack 7 speed_too_low clearance_margin_mean 11.22031853760992 high_sideslip_fraction_mean 0.15814697934268326 raw_action_abs_max 1.0 action_clip_fraction_mean 0.0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false; no validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claims; registered M3081 result audit.

## Hypothesis

A bounded same-denominator closed-loop measurement preflight can execute the M3078 actor-visible deterministic direct-action safety-reflex policy as the full obs72-to-action3 actor and write collision offtrack clearance stability recovery action-pressure and robustness measurement artifacts before any validation, ranking, promotion, driver-performance, current-sim verdict, high-fidelity, paper, repair-success, full-driver, or self-ID claim.

## Lineage

- parent_checkpoint: runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight/direct_action_policy_config.json, docs/m3079-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-result-audit.md
- parent_dataset: runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight/summary.json, runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight/actor_visible_feature_contract_rows.csv, runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight/safety_reflex_rule_rows.csv, runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight/measurement_admission_gate_rows.csv, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/summary.json, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/summary.json
- parent_config: experiments/manifests/m3079-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-result-audit.json, experiments/manifests/m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight.json
- parent_objective: measure the M3078 deterministic direct-action safety-reflex policy on the same 32-row denominator before any verdict claim
- derived_from: m3079-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-result-audit, m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight
- blocked_by: M3079 accepts M3078 materialization as complete but no closed-loop measurement exists for the deterministic safety-reflex candidate, deployable active-safety objective requires behavior evidence under same-denominator safety metrics
- supersedes: measurement-free safety-reflex route continuation
- invalidates: None

## Success Criteria

- summary.json reports status_pass true and gate_matrix_pass true
- measurement_episode_rows.csv records the same scheduled 32-row denominator
- metric_summary_rows.csv reports success collision offtrack speed-too-low clearance stability recovery and action-pressure metrics
- actor_contract_guard_rows.csv verifies obs72/action3 direct [steer throttle brake] runtime_base_policy_required false
- claim_boundary_rows.csv rejects validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success and self-ID claims
- M3081 result-audit manifest is created and pending

## Failure Criteria

- M3080 changes denominator after M3079 without a separate pre-registered manifest
- M3080 uses hidden oracle TTC target provenance source route outcome progress or verdict actor inputs
- M3080 uses a runtime base policy instead of the M3078 deterministic direct-action actor
- M3080 reports aggregate success without collision offtrack clearance stability recovery action-pressure rows
- M3080 makes validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success or self-ID claims

## Evidence Gates

- M3080 must execute M3078 as full obs72-to-action3 direct actor with runtime_base_policy_required false
- M3080 must preserve same-denominator 32-row measurement scope unless separately pre-registered
- M3080 must report success collision offtrack speed-too-low clearance stability recovery action pressure and robustness artifacts
- M3080 must preserve hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor-input exclusion
- M3080 must not claim validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success or self-ID

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune denominator after seeing M3067/M3075 or M3078 artifacts
- do not use a runtime base policy or residual adapter
- do not add hidden oracle TTC target provenance source route outcome progress or verdict labels to actor input
- do not claim validation ranking promotion driver performance current-sim verdict high-fidelity readiness paper finite-window-vs-GRU full-driver repair success or self-ID

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

- milestone: m3080-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-closed-loop-measurement-preflight
- type: infrastructure
- checkpoint: runs/m3080_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_closed_loop_measurement_preflight/summary.json
- success_rate: 0.59375
- termination_rate: None
- clearance_margin_mean: 11.22031853760992
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_measurement_route_to_m3081_result_audit
- reason: Completed: ran same-denominator current-sim measurement for the M3078 deterministic direct-action safety-reflex actor with status_pass True gate_matrix_pass True required_artifacts_present True 32/32 episode rows 0 failures 19 success 3 collision 3 offtrack 7 speed_too_low clearance_margin_mean 11.22031853760992 high_sideslip_fraction_mean 0.15814697934268326 raw_action_abs_max 1.0 action_clip_fraction_mean 0.0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false; no validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claims; registered M3081 result audit.

## Next Blocker

m3081-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-closed-loop-measurement-result-audit
