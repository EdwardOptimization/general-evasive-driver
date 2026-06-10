# m3135-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260607T235721Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_route_to_m3136_result_audit
- Decision reason: Completed: materialized M3135 guarded fallback hybrid with status_pass true gate_matrix_pass true required_artifacts_present true rule_rows 9 runtime_contract_rows 5 actor_input_exclusion_rows 12 action_probe_rows 5 fallback_path_probes 4 bounded_mix_probes 1 actor obs72 current frame direct_action_clipped [steer throttle brake] runtime_base_policy_required false hidden_oracle_actor_input_required false ttc_actor_input_required false no measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim registered M3136 result audit.

## Hypothesis

A bounded regression-aware guarded fallback hybrid materialization can preserve M3105 as the default deployable obs72-to-action3 direct-action path while allowing only actor-visible corridor-style adjustments guarded against the M3133 added offtrack speed-too-low collision clearance return and stability regressions before any measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3134-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-regression-failure-decomposition-result-audit.md
- parent_dataset: runs/m3133_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_regression_failure_decomposition_materialization_preflight/summary.json, runs/m3133_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_regression_failure_decomposition_materialization_preflight/regression_failure_decomposition_rows.csv, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/summary.json, runs/m3129_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_preflight/summary.json
- parent_config: experiments/manifests/m3134-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-regression-failure-decomposition-result-audit.json, experiments/manifests/m3133-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-regression-failure-decomposition-materialization-preflight.json
- parent_objective: materialize a guarded fallback hybrid route after rejecting standalone corridor reflex behavior
- derived_from: m3134-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-regression-failure-decomposition-result-audit, m3133-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-regression-failure-decomposition-materialization-preflight, m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight, m3129-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-materialization-preflight
- blocked_by: M3131 standalone corridor reflex regresses success by 22 rows and adds collision offtrack and speed-too-low failures versus M3105, M3133 requires any next materialization to block standalone corridor regression axes before measurement
- supersedes: another standalone corridor gain edit without a fallback guard
- invalidates: None

## Success Criteria

- runs/m3135_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_preflight/summary.json reports status_pass true and gate_matrix_pass true
- M3135 writes guarded fallback hybrid materialization artifacts preserving actor-visible direct-action contract
- M3135 registers M3136 result audit

## Failure Criteria

- M3135 drops the M3105 fallback path or actor-visible obs72-to-action3 contract
- M3135 requires hidden actor input runtime learned base policy checkpoint model recurrent hidden state row labels or baseline outcomes
- M3135 claims measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID evidence

## Evidence Gates

- M3135 must preserve deployable obs72 actor-visible current-frame input to direct [steer throttle brake] output
- M3135 must default to the M3105 no-regression behavior path when corridor guards are unsafe
- M3135 must not use M3133 row labels M3105 outcomes source route outcome progress verdict hidden oracle or TTC values as runtime actor inputs
- M3135 must write rule runtime-contract actor-input-exclusion claim-boundary and gate artifacts
- M3135 must not claim measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID evidence
- M3135 must register M3136 result audit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun tune expand rank promote validate or mutate checkpoints
- do not use M3133 row labels baseline outcomes source route outcome progress verdict hidden oracle TTC or future labels as actor inputs
- do not convert materialization artifacts into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID claims
- do not remove the M3105 default fallback path

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

- milestone: m3135-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-preflight
- type: infrastructure
- checkpoint: runs/m3135_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_route_to_m3136_result_audit
- reason: Completed: materialized M3135 guarded fallback hybrid with status_pass true gate_matrix_pass true required_artifacts_present true rule_rows 9 runtime_contract_rows 5 actor_input_exclusion_rows 12 action_probe_rows 5 fallback_path_probes 4 bounded_mix_probes 1 actor obs72 current frame direct_action_clipped [steer throttle brake] runtime_base_policy_required false hidden_oracle_actor_input_required false ttc_actor_input_required false no measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim registered M3136 result audit.

## Next Blocker

m3136-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-result-audit
