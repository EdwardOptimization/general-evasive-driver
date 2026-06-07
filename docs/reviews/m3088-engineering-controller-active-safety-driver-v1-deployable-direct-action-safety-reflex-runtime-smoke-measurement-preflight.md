# m3088-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-preflight Research Review

## Summary

- Generated at UTC: 20260607T184827Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_runtime_smoke_measurement_route_to_m3089_result_audit
- Decision reason: Completed: ran M3088 deployable runtime-smoke through ActiveSafetyReflexDriver.act with status_pass true gate_matrix_pass true required_artifacts_present true 8/8 episode rows 0 failures 6 success 0 collision 1 offtrack 1 speed_too_low success_rate 0.75 clearance_margin_mean 10.288422972097099 raw_action_abs_max 1.0 action_clip_fraction_mean 0.0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false M3086 interface/action-probe/actor-input-exclusion/claim guards pass; no validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claims; registered M3089 result audit.

## Hypothesis

A bounded runtime-smoke measurement preflight can execute the packaged ActiveSafetyReflexDriver deployable API as the full obs72-to-action3 action source on a small pre-registered current-sim smoke panel and write safety, contract, and claim-boundary artifacts before any validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/deployable_driver_contract.json, src/autodrift/active_safety_reflex_driver.py, docs/m3087-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-result-audit.md
- parent_dataset: runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/summary.json, runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/driver_action_probe_rows.csv, runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/measurement_episode_rows.csv, runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/summary.json, runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/executable_workload_rows.csv
- parent_config: experiments/manifests/m3087-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-result-audit.json, experiments/manifests/m3086-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-preflight.json, experiments/manifests/m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-preflight.json, experiments/manifests/m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight.json
- parent_objective: execute the deployable runtime API in a bounded current-sim smoke before stronger verification claims
- derived_from: m3087-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-result-audit, m3086-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-preflight, m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-preflight, m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight
- blocked_by: M3086 proves packaging and API probes but has not executed the deployable API inside the environment loop, runtime integration must be checked before any broader robustness or validation route
- supersedes: package-only treatment of ActiveSafetyReflexDriver deployment readiness
- invalidates: None

## Success Criteria

- runs/m3088_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight/summary.json reports status_pass true and gate_matrix_pass true
- runs/m3088_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight/runtime_smoke_episode_rows.csv records the pre-registered smoke rows using ActiveSafetyReflexDriver.act
- runs/m3088_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight/runtime_smoke_metric_summary_rows.csv reports success collision offtrack speed-too-low clearance stability recovery and action-pressure metrics
- runs/m3088_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight/runtime_smoke_contract_guard_rows.csv verifies obs72/action3 direct [steer throttle brake] runtime_base_policy_required false
- runs/m3088_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight/claim_boundary_rows.csv rejects validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- experiments/manifests/m3089-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-result-audit.json is created and pending

## Failure Criteria

- M3088 changes observation shape action shape action component order or direct-action semantics
- M3088 requires runtime base policy residual adapter checkpoint model hidden state or hidden actor input
- M3088 emits non-finite or out-of-bound actions during smoke rollout
- M3088 expands tunes or reselects smoke rows after seeing results
- M3088 makes validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claims

## Evidence Gates

- M3088 must execute only a small pre-registered smoke panel derived from existing M3084/M3012 rows
- M3088 must use ActiveSafetyReflexDriver.act as the action source, not the raw M3078 helper directly
- M3088 must preserve obs72/action3 direct [steer throttle brake], runtime_base_policy_required false, and no checkpoint model dependency
- M3088 must report success collision offtrack speed-too-low clearance stability recovery and action-pressure fields
- M3088 must reject validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3088 must register M3089 result audit before any broader runtime measurement or validation route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run validation ranking promotion high-fidelity simulation fitting PPO or training
- do not expand beyond the pre-registered runtime-smoke panel after seeing results
- do not call hidden oracle TTC target provenance source route outcome progress or verdict labels as actor input
- do not use a runtime base policy checkpoint model residual adapter or recurrent hidden state
- do not treat runtime smoke as driver-performance current-sim robustness-result repair-success validation high-fidelity paper full-driver or self-ID evidence

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

- milestone: m3088-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-preflight
- type: infrastructure
- checkpoint: runs/m3088_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight/summary.json
- success_rate: 0.75
- termination_rate: None
- clearance_margin_mean: 10.288422972097099
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_runtime_smoke_measurement_route_to_m3089_result_audit
- reason: Completed: ran M3088 deployable runtime-smoke through ActiveSafetyReflexDriver.act with status_pass true gate_matrix_pass true required_artifacts_present true 8/8 episode rows 0 failures 6 success 0 collision 1 offtrack 1 speed_too_low success_rate 0.75 clearance_margin_mean 10.288422972097099 raw_action_abs_max 1.0 action_clip_fraction_mean 0.0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false M3086 interface/action-probe/actor-input-exclusion/claim guards pass; no validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claims; registered M3089 result audit.

## Next Blocker

m3088-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-preflight
