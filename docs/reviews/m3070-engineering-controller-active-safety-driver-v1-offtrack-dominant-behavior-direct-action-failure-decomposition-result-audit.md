# m3070-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-result-audit Research Review

## Summary

- Generated at UTC: 20260607T161906Z
- Type: gate
- Gate tier: process
- Promotion decision: continue_to_m3071_direct_action_multi_failure_repair_contract_materialization_preflight
- Decision reason: Completed: audit accepts M3069 direct-action failure decomposition as complete and claim-safe with status_pass true gate_matrix_pass true 32/32 episode rows 0 failures 8 success 4 collision 16 offtrack 5 speed_too_low 31 failure_mode rows 13 actuation_pressure rows 13 recovery_stability rows 7 repair_requirement rows raw_action_abs_max 2.2606801986694336 action_clip_fraction_mean 0.03451952273501378 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false; rejects validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims; routes exactly one follow-up to M3071 multi-failure direct-action repair-contract materialization.

## Hypothesis

A bounded result audit can accept or reject the M3069 direct-action failure-decomposition artifacts before any fitting training rollout validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim.

## Lineage

- parent_checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt, runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt
- parent_dataset: runs/m3069_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_failure_decomposition_materialization_preflight/summary.json, runs/m3069_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_failure_decomposition_materialization_preflight/direct_action_failure_mode_rows.csv, runs/m3069_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_failure_decomposition_materialization_preflight/direct_action_actuation_pressure_rows.csv, runs/m3069_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_failure_decomposition_materialization_preflight/direct_action_recovery_stability_rows.csv, runs/m3069_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_failure_decomposition_materialization_preflight/direct_action_repair_requirement_rows.csv, runs/m3069_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_failure_decomposition_materialization_preflight/claim_boundary_rows.csv, runs/m3069_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_failure_decomposition_materialization_preflight/gate_matrix.csv, docs/m3069-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-materialization-preflight.md
- parent_config: experiments/manifests/m3069-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-materialization-preflight.json
- parent_objective: audit direct-action failure decomposition before any repair route
- derived_from: m3069-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-materialization-preflight, m3068-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-result-audit, m3067-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-preflight
- blocked_by: M3069 decomposition artifacts require audit before refit rerun repair or stop decision, M3067/M3068 evidence is measurement and audit evidence only
- supersedes: direct repair route without auditing M3069 decomposition
- invalidates: None

## Success Criteria

- docs/m3070-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-result-audit.md exists
- M3070 audits M3069 summary failure actuation recovery repair claim and gate artifacts
- M3070 rejects validation ranking promotion performance high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims
- M3070 selects exactly one repair audit stop or continuation route

## Failure Criteria

- M3070 hides M3069 failures or missing artifacts
- M3070 treats M3069 decomposition as validation or performance verdict
- M3070 changes actor input action contract or runtime base-policy-free boundary
- M3070 leaves next route ambiguous

## Evidence Gates

- M3070 must audit M3069 summary failure actuation recovery repair claim and gate artifacts
- M3070 must confirm all 32 M3067 rows remain accounted for
- M3070 must preserve actor 72/action 3 direct-action/base-policy-free contract and claim boundaries
- M3070 must reject validation ranking promotion high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims unless separately routed
- M3070 must select exactly one repair audit stop or continuation route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun rollout fit train validate rank promote tune or mutate checkpoints
- do not convert M3069 decomposition rows into performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims
- do not change actor input action contract or runtime base-policy-free boundary

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

- milestone: m3070-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-result-audit
- type: gate
- checkpoint: docs/m3070-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: continue_to_m3071_direct_action_multi_failure_repair_contract_materialization_preflight
- reason: Completed: audit accepts M3069 direct-action failure decomposition as complete and claim-safe with status_pass true gate_matrix_pass true 32/32 episode rows 0 failures 8 success 4 collision 16 offtrack 5 speed_too_low 31 failure_mode rows 13 actuation_pressure rows 13 recovery_stability rows 7 repair_requirement rows raw_action_abs_max 2.2606801986694336 action_clip_fraction_mean 0.03451952273501378 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false; rejects validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims; routes exactly one follow-up to M3071 multi-failure direct-action repair-contract materialization.

## Next Blocker

m3071-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-contract-materialization-preflight
