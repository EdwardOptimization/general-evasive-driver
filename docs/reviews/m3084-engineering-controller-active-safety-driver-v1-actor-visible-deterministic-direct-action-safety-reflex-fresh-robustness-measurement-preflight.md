# m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-preflight Research Review

## Summary

- Generated at UTC: 20260607T181641Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_route_to_m3085_result_audit
- Decision reason: Completed: ran M3084 fresh robustness current-sim measurement with status_pass true gate_matrix_pass true required_artifacts_present true 64/64 episode rows 0 failures 43 success 5 collision 5 offtrack 11 speed_too_low success_rate 0.671875 clearance_margin_mean 11.341408769853288 raw_action_abs_max 1.0 action_clip_fraction_mean 0.0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false 0 M3080 seed overlap 4 robustness axes; no validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claims; registered M3085 result audit.

## Hypothesis

A bounded fresh robustness measurement preflight can execute the M3078 deterministic direct-action safety-reflex actor as the full obs72-to-action3 actor on the M3082 fresh panel and write collision, offtrack, speed-floor, clearance, stability, recovery, action-pressure, actor-contract, and claim-boundary measurement artifacts before any validation, ranking, promotion, driver-performance, current-sim verdict, high-fidelity, paper, full-driver, repair-success, or self-ID claim.

## Lineage

- parent_checkpoint: runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight/direct_action_policy_config.json, docs/m3083-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-panel-materialization-result-audit.md
- parent_dataset: runs/m3082_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_panel_materialization_preflight/summary.json, runs/m3082_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_panel_materialization_preflight/fresh_robustness_panel_rows.csv, runs/m3082_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_panel_materialization_preflight/robustness_admission_guard_rows.csv, runs/m3082_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_panel_materialization_preflight/actor_contract_guard_rows.csv, runs/m3082_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_panel_materialization_preflight/claim_boundary_rows.csv, runs/m3082_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_panel_materialization_preflight/gate_matrix.csv
- parent_config: experiments/manifests/m3083-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-panel-materialization-result-audit.json, experiments/manifests/m3082-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-panel-materialization-preflight.json, experiments/manifests/m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight.json
- parent_objective: measure the deterministic direct-action safety-reflex actor on the M3082 fresh robustness panel before any verdict claim
- derived_from: m3083-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-panel-materialization-result-audit, m3082-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-panel-materialization-preflight, m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight
- blocked_by: M3082 materialized fresh panel rows but did not execute them, M3080 fixed-panel behavior cannot support robustness interpretation without M3084 fresh measurement
- supersedes: measurement-free interpretation of M3082 fresh panel materialization
- invalidates: None

## Success Criteria

- runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/summary.json reports status_pass true and gate_matrix_pass true
- runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/measurement_episode_rows.csv records the M3082 fresh panel denominator
- runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/metric_summary_rows.csv reports success collision offtrack speed-too-low clearance stability recovery and action-pressure metrics
- runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/actor_contract_guard_rows.csv verifies obs72/action3 direct [steer throttle brake] runtime_base_policy_required false
- runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/claim_boundary_rows.csv rejects validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success and self-ID claims
- experiments/manifests/m3085-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-result-audit.json is created and pending

## Failure Criteria

- M3084 changes denominator after M3083 without a separate pre-registered manifest
- M3084 uses hidden oracle TTC target provenance source route outcome progress or verdict actor inputs
- M3084 uses a runtime base policy instead of the M3078 deterministic direct-action actor
- M3084 reports aggregate success without collision offtrack speed-floor clearance stability recovery and action-pressure rows
- M3084 makes validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success or self-ID claims

## Evidence Gates

- M3084 must execute only M3082 fresh panel rows with 0 M3080 seed overlap unless a separate pre-registered manifest changes the panel
- M3084 must execute M3078 as full obs72-to-action3 direct actor with runtime_base_policy_required false
- M3084 must report success collision offtrack speed-too-low clearance stability recovery action pressure and robustness artifacts by axis and all rows
- M3084 must preserve hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor-input exclusion
- M3084 must not claim validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success or self-ID

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not replace the M3082 fresh panel with the fixed M3067/M3075/M3080 denominator
- do not tune seeds axes profiles or thresholds after seeing M3084 measurements
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

- milestone: m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-preflight
- type: infrastructure
- checkpoint: runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight/summary.json
- success_rate: 0.671875
- termination_rate: None
- clearance_margin_mean: 11.3414
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_route_to_m3085_result_audit
- reason: Completed: ran M3084 fresh robustness current-sim measurement with status_pass true gate_matrix_pass true required_artifacts_present true 64/64 episode rows 0 failures 43 success 5 collision 5 offtrack 11 speed_too_low success_rate 0.671875 clearance_margin_mean 11.341408769853288 raw_action_abs_max 1.0 action_clip_fraction_mean 0.0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false 0 M3080 seed overlap 4 robustness axes; no validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claims; registered M3085 result audit.

## Next Blocker

m3085-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-result-audit
