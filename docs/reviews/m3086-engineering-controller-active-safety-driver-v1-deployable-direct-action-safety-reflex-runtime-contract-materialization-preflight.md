# m3086-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260607T183031Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_route_to_m3087_result_audit
- Decision reason: Completed: materialized M3086 deployable runtime contract with status_pass true gate_matrix_pass true required_artifacts_present true driver active_safety_reflex_driver_v1_m3078_deterministic obs72/action3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false policy_config_sha256 4e3b185f2f98208b9700280174cf3b4401ae418207da8cb293c72b0c4427d40c 2 interface rows 5 finite bounded action probe rows 10 actor-input exclusion rows 21 claim-boundary rows 19 gate rows; no reset step rollout validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claims; registered M3087 result audit.

## Hypothesis

A bounded deployable runtime-contract materialization preflight can package the M3078 deterministic safety-reflex as a callable obs72-to-action3 [steer throttle brake] active-safety layer, with contract probes and claim-boundary guards, before any validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight/direct_action_policy_config.json, docs/m3085-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-result-audit.md
- parent_dataset: runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/summary.json, runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/metric_summary_rows.csv, runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/actor_contract_guard_rows.csv, runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/claim_boundary_rows.csv, runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/gate_matrix.csv
- parent_config: experiments/manifests/m3085-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-result-audit.json, experiments/manifests/m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-preflight.json, experiments/manifests/m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight.json
- parent_objective: materialize a deployable direct-action runtime contract after M3085 accepts M3084 as complete and claim-safe
- derived_from: m3085-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-result-audit, m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-preflight, m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight
- blocked_by: M3084 measured behavior but did not expose a stable deployable driver API or package contract, the active-safety route needs a directly callable [steer throttle brake] runtime boundary before stronger verification
- supersedes: measurement-only handling of the deterministic safety-reflex candidate
- invalidates: None

## Success Criteria

- runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/summary.json reports status_pass true and gate_matrix_pass true
- runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/deployable_driver_contract.json defines obs72/action3 direct [steer throttle brake] runtime semantics
- runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/driver_action_probe_rows.csv records finite bounded action probes
- runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/actor_input_exclusion_rows.csv verifies forbidden actor inputs are excluded
- runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/claim_boundary_rows.csv rejects validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- experiments/manifests/m3087-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-result-audit.json is created and pending

## Failure Criteria

- M3086 changes observation shape action shape action component order or direct-action semantics
- M3086 requires runtime base policy residual adapter checkpoint model or hidden state
- M3086 emits non-finite or out-of-bound actions in contract probes
- M3086 makes validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claims

## Evidence Gates

- M3086 must materialize a deployable obs72-to-action3 direct [steer throttle brake] runtime contract
- M3086 must package the deterministic safety-reflex without runtime base-policy dependency
- M3086 must write finite bounded action probe rows and actor-input exclusion rows
- M3086 must preserve hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor-input exclusion
- M3086 must not claim validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID
- M3086 must register M3087 result audit before any runtime-smoke or validation route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run rollout validation ranking promotion high-fidelity simulation fitting PPO or training
- do not add hidden oracle TTC target provenance source route outcome progress or verdict labels to actor input
- do not require a runtime base policy residual adapter or checkpoint model
- do not treat packaging or action probes as driver-performance repair-success validation current-sim high-fidelity paper full-driver robustness-result or self-ID evidence

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

- milestone: m3086-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-preflight
- type: infrastructure
- checkpoint: runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_route_to_m3087_result_audit
- reason: Completed: materialized M3086 deployable runtime contract with status_pass true gate_matrix_pass true required_artifacts_present true driver active_safety_reflex_driver_v1_m3078_deterministic obs72/action3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false checkpoint_model_required false policy_config_sha256 4e3b185f2f98208b9700280174cf3b4401ae418207da8cb293c72b0c4427d40c 2 interface rows 5 finite bounded action probe rows 10 actor-input exclusion rows 21 claim-boundary rows 19 gate rows; no reset step rollout validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claims; registered M3087 result audit.

## Next Blocker

m3087-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-result-audit
