# m3076-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-closed-loop-measurement-result-audit Research Review

## Summary

- Generated at UTC: 20260607T171229Z
- Type: gate
- Gate tier: process
- Promotion decision: pivot_to_m3077_deployable_direct_action_safety_reflex_route_design
- Decision reason: Completed: audit accepts M3075 repaired direct-action closed-loop measurement as complete and claim-safe with status_pass true gate_matrix_pass true required_artifacts_present true 32/32 episode rows 0 failures 6 success 4 collision 19 offtrack 4 speed_too_low success_rate 0.1875 clearance_margin_mean 8.74188928150522 raw_action_abs_max 2.823486328125 action_clip_fraction_mean 0.03910273341603136 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false; same-denominator comparison to M3067 is negative on success and offtrack, so M3076 rejects repair-success driver-performance validation ranking promotion current-sim high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims; synthesis decision pivot routes exactly one follow-up to M3077 deployable direct-action safety-reflex route design.

## Hypothesis

A bounded result-audit synthesis can accept M3075 as complete measurement evidence, reject the current offline repair loop as a repair-success route, and pivot to a deployable direct-action safety-reflex route before any validation ranking promotion driver-performance high-fidelity finite-window-vs-GRU paper full-driver repair-success or self-ID claim.

## Lineage

- parent_checkpoint: runs/m3073_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_bounded_fitting_preflight/candidate_direct_action_repair_reflex_layer.npz, runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/candidate_direct_action_reflex_layer.npz
- parent_dataset: runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/summary.json, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/measurement_episode_rows.csv, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/measurement_failure_rows.csv, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/metric_summary_rows.csv, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/direct_action_adapter_guard_rows.csv, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/actor_contract_guard_rows.csv, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/checkpoint_side_effect_guard_rows.csv, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/claim_boundary_rows.csv, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/gate_matrix.csv, docs/m3075-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-closed-loop-measurement-preflight.md
- parent_config: experiments/manifests/m3075-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-closed-loop-measurement-preflight.json
- parent_objective: audit M3075 repaired direct-action closed-loop measurement artifacts before interpretation
- derived_from: m3075-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-closed-loop-measurement-preflight, m3074-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-bounded-fitting-result-audit
- blocked_by: M3075 measurement rows require audit before any performance or continuation decision, current-sim measurement rows are not validation or promotion evidence before M3076
- supersedes: direct interpretation of M3075 measurement rows without audit
- invalidates: None

## Success Criteria

- docs/m3076-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-closed-loop-measurement-result-audit.md exists
- M3076 audits M3075 row counts gates actor direct-action side-effect and claim boundaries
- M3076 compares M3075 to the same-denominator M3067 parent measurement
- M3076 rejects repair-success validation ranking promotion performance high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims
- M3076 pivots to exactly one next route: M3077 deployable direct-action safety-reflex route design

## Failure Criteria

- M3076 hides M3075 failures or missing artifacts
- M3076 treats M3075 measurements as validation or performance verdict
- M3076 changes actor input or action contract
- M3076 leaves next route ambiguous

## Evidence Gates

- M3076 must audit M3075 summary measurement metric guard claim and gate artifacts
- M3076 must answer evidence_summary supported_claims falsified_claims failure_taxonomy_summary public_gate_overfit_risk and next_branch_decision
- M3076 must preserve actor 72/action 3, direct-action adapter, no runtime base-policy dependency, and claim boundaries
- M3076 must reject validation ranking promotion high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims unless separately routed
- M3076 must select exactly one next route or stop state

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun rollout validate rank promote tune or mutate checkpoints
- do not convert M3075 rows into performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims
- do not change actor input or action contract
- do not reinterpret the M3073 repaired candidate as residual or base-policy-assisted

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

- milestone: m3076-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-closed-loop-measurement-result-audit
- type: gate
- checkpoint: docs/m3076-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-closed-loop-measurement-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: pivot_to_m3077_deployable_direct_action_safety_reflex_route_design
- reason: Completed: audit accepts M3075 repaired direct-action closed-loop measurement as complete and claim-safe with status_pass true gate_matrix_pass true required_artifacts_present true 32/32 episode rows 0 failures 6 success 4 collision 19 offtrack 4 speed_too_low success_rate 0.1875 clearance_margin_mean 8.74188928150522 raw_action_abs_max 2.823486328125 action_clip_fraction_mean 0.03910273341603136 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false; same-denominator comparison to M3067 is negative on success and offtrack, so M3076 rejects repair-success driver-performance validation ranking promotion current-sim high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims; synthesis decision pivot routes exactly one follow-up to M3077 deployable direct-action safety-reflex route design.

## Next Blocker

m3077-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-pivot-route-design
