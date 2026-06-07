# m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-preflight Research Review

## Summary

- Generated at UTC: 20260607T190725Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_full_fresh_runtime_measurement_route_to_m3091_result_audit
- Decision reason: Completed: ran M3090 full-fresh deployable runtime measurement through ActiveSafetyReflexDriver.act with status_pass true gate_matrix_pass true required_artifacts_present true 64/64 episode rows 0 failures 43 success 5 collision 5 offtrack 11 speed_too_low success_rate 0.671875 clearance_margin_mean 11.341408769853288 raw_action_abs_max 1.0 action_clip_fraction_mean 0.0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false parity_rows 64 outcome_matches 64/64 parity_clearance_delta_max 0.0 parity_return_delta_max 0.0; no validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claims; registered M3091 result audit.

## Hypothesis

A bounded full-fresh deployable runtime measurement preflight can execute ActiveSafetyReflexDriver.act as the full obs72-to-action3 action source on the complete M3084 fresh robustness denominator and write runtime measurement, parity, contract, and claim-boundary artifacts before any validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3089-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-result-audit.md, runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/deployable_driver_contract.json, src/autodrift/active_safety_reflex_driver.py
- parent_dataset: runs/m3088_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight/summary.json, runs/m3088_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight/runtime_smoke_episode_rows.csv, runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/measurement_episode_rows.csv, runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/executable_workload_rows.csv
- parent_config: experiments/manifests/m3089-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-result-audit.json, experiments/manifests/m3088-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-preflight.json
- parent_objective: execute the deployable runtime API over the full M3084 fresh denominator after smoke passes
- derived_from: m3089-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-result-audit, m3088-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-preflight, m3086-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-preflight, m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-preflight
- blocked_by: M3088 only covers an 8-row smoke panel, deployable API must be checked over the complete M3084 fresh denominator before broader interpretation
- supersedes: smoke-only deployable runtime execution evidence
- invalidates: None

## Success Criteria

- runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/summary.json reports status_pass true and gate_matrix_pass true
- runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_measurement_episode_rows.csv records 64 pre-registered M3084 rows using ActiveSafetyReflexDriver.act
- runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_parity_rows.csv records same-row parity against M3084 helper-path rows
- runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_measurement_contract_guard_rows.csv verifies obs72/action3 direct [steer throttle brake] runtime_base_policy_required false
- runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/claim_boundary_rows.csv rejects validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- experiments/manifests/m3091-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-result-audit.json is created and pending

## Failure Criteria

- M3090 changes observation shape action shape action component order or direct-action semantics
- M3090 requires runtime base policy residual adapter checkpoint model hidden state or hidden actor input
- M3090 emits non-finite or out-of-bound actions during rollout
- M3090 expands tunes or reselects rows after seeing M3088 or M3090 results
- M3090 makes validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claims

## Evidence Gates

- M3090 must execute the complete 64-row M3084 fresh robustness denominator through ActiveSafetyReflexDriver.act
- M3090 must preserve obs72/action3 direct [steer throttle brake], runtime_base_policy_required false, checkpoint_model_required false, and no recurrent hidden state
- M3090 must write same-row parity artifacts against M3084 helper-path rows without treating parity as validation or performance
- M3090 must report collision offtrack speed-floor clearance stability recovery and action-pressure fields
- M3090 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3090 must register M3091 result audit before any broader validation or promotion route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune expand reselect rank promote validate or mutate checkpoints after seeing M3088
- do not use hidden oracle TTC target provenance source route outcome progress or verdict labels as actor input
- do not use a runtime base policy checkpoint model residual adapter or recurrent hidden state
- do not treat full-fresh runtime measurement or parity as driver-performance current-sim robustness-result repair-success validation high-fidelity paper full-driver or self-ID evidence

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

- milestone: m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-preflight
- type: infrastructure
- checkpoint: runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/summary.json
- success_rate: 0.671875
- termination_rate: None
- clearance_margin_mean: 11.341408769853288
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_full_fresh_runtime_measurement_route_to_m3091_result_audit
- reason: Completed: ran M3090 full-fresh deployable runtime measurement through ActiveSafetyReflexDriver.act with status_pass true gate_matrix_pass true required_artifacts_present true 64/64 episode rows 0 failures 43 success 5 collision 5 offtrack 11 speed_too_low success_rate 0.671875 clearance_margin_mean 11.341408769853288 raw_action_abs_max 1.0 action_clip_fraction_mean 0.0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false parity_rows 64 outcome_matches 64/64 parity_clearance_delta_max 0.0 parity_return_delta_max 0.0; no validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claims; registered M3091 result audit.

## Next Blocker

m3091-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-result-audit
