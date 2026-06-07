# m3069-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260607T161007Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_direct_action_failure_decomposition_route_to_m3070_result_audit
- Decision reason: Completed: materialized row-preserving direct-action failure decomposition from M3067/M3068 with status_pass true gate_matrix_pass true 32/32 episode rows 0 failures 8 success 4 collision 16 offtrack 5 speed_too_low 31 failure_mode rows 13 actuation_pressure rows 13 recovery_stability rows 7 repair_requirement rows raw_action_abs_max 2.2606801986694336 action_clip_fraction_mean 0.03451952273501378 actor 72/action 3 direct_action_clipped [steer throttle brake] base_policy_required false runtime_base_policy_required false; no reset step rollout replay fitting training validation ranking promotion checkpoint mutation driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claims; registered M3070 result audit.

## Hypothesis

A no-new-execution direct-action failure-decomposition materialization preflight can convert the M3068-accepted M3067 closed-loop measurement rows into row-preserving offtrack collision speed-floor clearance stability recovery actuation-pressure and repair-requirement artifacts before any fitting training rollout validation ranking promotion driver-performance high-fidelity paper finite-window-vs-GRU full-driver or self-ID claim.

## Lineage

- parent_checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt, runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt
- parent_dataset: docs/m3068-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-result-audit.md, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/summary.json, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/measurement_episode_rows.csv, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/measurement_failure_rows.csv, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/metric_summary_rows.csv, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/direct_action_adapter_guard_rows.csv, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/actor_contract_guard_rows.csv, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/checkpoint_side_effect_guard_rows.csv, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/claim_boundary_rows.csv, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/gate_matrix.csv
- parent_config: experiments/manifests/m3068-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-result-audit.json, experiments/manifests/m3067-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-preflight.json
- parent_objective: decompose M3067 direct-action closed-loop failure modes before any next fitting or repair claim
- derived_from: m3068-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-result-audit, m3067-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-preflight
- blocked_by: M3067 measurement rows are complete but behavior-incomplete: 8 success 4 collision 16 offtrack 5 speed-too-low, M3068 selects row-preserving failure decomposition before another direct-action fit or rollout interpretation, current-sim measurement rows cannot be promoted to validation or driver-performance verdicts without decomposition and later gates
- supersedes: direct fitting repair iteration from aggregate success rate alone, direct ranking or promotion of the M3065 candidate before failure decomposition
- invalidates: None

## Success Criteria

- runs/m3069_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_failure_decomposition_materialization_preflight/summary.json exists
- direct_action_failure_mode_rows direct_action_actuation_pressure_rows direct_action_recovery_stability_rows direct_action_repair_requirement_rows claim_boundary_rows gate_matrix run_state and doc artifacts exist
- M3069 preserves all 32 M3067 measurement rows and accounts for success collision offtrack speed-low action clipping clearance stability and recovery metrics
- M3069 preserves actor observation 72 final action 3 direct-action/base-policy-free boundary and no hidden oracle TTC target provenance source route outcome progress or verdict actor inputs
- M3069 registers exactly one M3070 result-audit manifest

## Failure Criteria

- M3069 drops failure rows or optimizes only positive aggregate rows
- M3069 runs new rollout fitting training validation ranking promotion checkpoint mutation or profile tuning
- M3069 changes actor input or output contract or requires a runtime base policy
- M3069 claims validation driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID evidence

## Evidence Gates

- M3069 must consume the M3068 audit and M3067 measurement artifacts without running new rollouts or fitting
- M3069 must preserve all 32 M3067 measurement rows including candidate parent T4 T5 success collision offtrack speed-low and clipping cases
- M3069 must preserve actor observation 72 action 3 direct-action/base-policy-free contract and no hidden oracle TTC target provenance source route outcome progress or verdict actor inputs
- M3069 must materialize offtrack collision speed-floor clearance stability recovery and actuation-pressure repair requirements as measurement-derived rows only
- M3069 must not claim validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair success or self-ID evidence
- M3069 must register exactly one M3070 result-audit manifest

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun rollout train fit validate rank promote tune profiles or mutate checkpoints
- do not cherry-pick only improved success or clearance rows while hiding collision offtrack speed-low or clipping rows
- do not expose target labels provenance source route outcome progress verdict TTC or hidden oracle values to actor input
- do not reinterpret direct-action measurement rows as validation driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims

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

- milestone: m3069-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-materialization-preflight
- type: infrastructure
- checkpoint: runs/m3069_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_failure_decomposition_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_direct_action_failure_decomposition_route_to_m3070_result_audit
- reason: Completed: materialized row-preserving direct-action failure decomposition from M3067/M3068 with status_pass true gate_matrix_pass true 32/32 episode rows 0 failures 8 success 4 collision 16 offtrack 5 speed_too_low 31 failure_mode rows 13 actuation_pressure rows 13 recovery_stability rows 7 repair_requirement rows raw_action_abs_max 2.2606801986694336 action_clip_fraction_mean 0.03451952273501378 actor 72/action 3 direct_action_clipped [steer throttle brake] base_policy_required false runtime_base_policy_required false; no reset step rollout replay fitting training validation ranking promotion checkpoint mutation driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claims; registered M3070 result audit.

## Next Blocker

m3070-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-result-audit
