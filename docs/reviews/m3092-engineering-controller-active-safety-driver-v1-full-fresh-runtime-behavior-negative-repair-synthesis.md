# m3092-engineering-controller-active-safety-driver-v1-full-fresh-runtime-behavior-negative-repair-synthesis Research Review

## Summary

- Generated at UTC: 20260607T191729Z
- Type: gate
- Gate tier: process
- Promotion decision: route_to_m3093_speed_floor_aware_balanced_direct_action_repair_materialization
- Decision reason: Completed: behavior-negative repair synthesis accepts M3090/M3091 artifacts as complete and claim-safe but rejects validation promotion or performance interpretation; classifies 21/64 non-success rows as 11 speed_too_low 5 collision 5 offtrack across all 4 axes, with speed_too_low the largest blocker and collision/offtrack retained as hard-safety blockers; selects exactly one follow-up to M3093 v2 speed-floor-aware balanced direct-action repair materialization, preserving obs72/action3 direct [steer throttle brake] runtime_base_policy_required false and forbidding hidden oracle TTC target source route outcome progress or verdict actor inputs; no measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Hypothesis

A bounded behavior-negative repair synthesis can classify the M3090 full-fresh deployable runtime failures and select one direct-action active-safety repair route before any validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3091-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-result-audit.md, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/summary.json, src/autodrift/active_safety_reflex_driver.py
- parent_dataset: runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_measurement_episode_rows.csv, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_measurement_metric_summary_rows.csv, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_measurement_contract_guard_rows.csv, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/runtime_parity_rows.csv, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/claim_boundary_rows.csv, runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight/gate_matrix.csv
- parent_config: experiments/manifests/m3091-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-result-audit.json, experiments/manifests/m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-preflight.json
- parent_objective: classify full-fresh deployable runtime safety blockers before selecting a repair route
- derived_from: m3091-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-result-audit, m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-preflight, m3087-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-result-audit, m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-preflight
- blocked_by: M3090 preserves deployable runtime parity but still has 5 collision rows, 5 offtrack rows, and 11 speed-too-low rows, validation or promotion is not justified while hard safety blockers remain
- supersedes: runtime-packaging-only continuation after M3090
- invalidates: None

## Success Criteria

- docs/m3092-engineering-controller-active-safety-driver-v1-full-fresh-runtime-behavior-negative-repair-synthesis.md exists
- M3092 classifies M3090 collision offtrack and speed-too-low rows without dropping failures
- M3092 rejects validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3092 selects exactly one repair route, fallback route, or stop route

## Failure Criteria

- M3092 hides M3090 failures or treats exact parity as behavior improvement
- M3092 selects validation or promotion while collision offtrack and speed-too-low blockers remain
- M3092 changes actor input or action contract
- M3092 leaves next route ambiguous

## Evidence Gates

- M3092 must classify all M3090 non-success rows by termination reason, robustness axis, binding role, and available safety/stability/action-pressure metrics
- M3092 must preserve the obs72/action3 direct [steer throttle brake] actor contract and forbid hidden oracle TTC target source route outcome progress or verdict actor inputs
- M3092 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3092 must select exactly one repair route, stop route, or explicit fallback route before implementation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun expand tune rank promote validate or mutate checkpoints inside M3092
- do not convert M3090 failure counts into a driver-performance verdict or robustness-result claim
- do not add hidden oracle TTC target source route outcome progress or verdict actor input
- do not re-center self-ID, GRU, paper evidence, or high-fidelity validation as the main route before current-sim safety blockers are repaired

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

- milestone: m3092-engineering-controller-active-safety-driver-v1-full-fresh-runtime-behavior-negative-repair-synthesis
- type: gate
- checkpoint: docs/m3092-engineering-controller-active-safety-driver-v1-full-fresh-runtime-behavior-negative-repair-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_m3093_speed_floor_aware_balanced_direct_action_repair_materialization
- reason: Completed: behavior-negative repair synthesis accepts M3090/M3091 artifacts as complete and claim-safe but rejects validation promotion or performance interpretation; classifies 21/64 non-success rows as 11 speed_too_low 5 collision 5 offtrack across all 4 axes, with speed_too_low the largest blocker and collision/offtrack retained as hard-safety blockers; selects exactly one follow-up to M3093 v2 speed-floor-aware balanced direct-action repair materialization, preserving obs72/action3 direct [steer throttle brake] runtime_base_policy_required false and forbidding hidden oracle TTC target source route outcome progress or verdict actor inputs; no measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result or self-ID claim.

## Next Blocker

m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight
