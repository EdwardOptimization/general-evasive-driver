# m3067-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-preflight Research Review

## Summary

- Generated at UTC: 20260607T154947Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_offtrack_behavior_direct_action_closed_loop_measurement_route_to_m3068_result_audit
- Decision reason: Completed: ran bounded same-denominator current-sim measurement for the M3065 direct-action candidate as full obs72-to-action3 actor with status_pass true gate_matrix_pass true required_artifacts_present true 32/32 episode rows 0 failures 8 success 4 collision 16 offtrack 5 speed_too_low raw_action_abs_max 2.2606801986694336 action_clip_fraction_mean 0.03451952273501378 final_action_abs_max 1.0 actor 72/action 3 direct_action_clipped [steer throttle brake] base_policy_required false runtime_base_policy_required false direct-action adapter actor-contract side-effect and claim guards pass; no validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims; registered M3068 result audit.

## Hypothesis

A bounded same-denominator closed-loop measurement preflight can execute the M3065 direct-action Active Safety Driver v1 candidate as the full obs72-to-action3 actor and write collision offtrack clearance stability recovery action and robustness measurement artifacts before any validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim.

## Lineage

- parent_checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt, runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt
- parent_dataset: docs/m3066-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-result-audit.md, runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/summary.json, runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/candidate_direct_action_reflex_layer.npz, runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/fitting_dataset_rows.csv, runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/fitting_loss_trace_rows.csv, runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/gate_matrix.csv, runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_admission_materialization_preflight/scenario_panel_rows.csv, runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight/baseline_measurement_rows.csv, runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/executable_workload_rows.csv
- parent_config: experiments/manifests/m3066-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-result-audit.json, experiments/manifests/m3065-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-preflight.json, experiments/manifests/m3050-engineering-controller-active-safety-driver-v1-actuation-aware-residual-repair-closed-loop-measurement-preflight.json
- parent_objective: measure the M3065 direct-action candidate as the full action-producing active-safety driver under the preserved denominator
- derived_from: m3066-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-result-audit, m3065-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-preflight
- blocked_by: M3066 accepts M3065 as a complete offline fitting artifact but not as closed-loop repair evidence, offline fitting loss is not validation target-quality driver-performance or current-sim evidence, same-denominator current-sim measurement is needed before any result audit or repair-success discussion
- supersedes: direct driver-performance verdict from M3065 offline fitting loss, direct ranking or promotion of the M3065 candidate before current-sim measurement rows exist
- invalidates: None

## Success Criteria

- runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/summary.json exists
- measurement_episode_rows metric_summary_rows direct_action_adapter_guard_rows actor_contract_guard_rows checkpoint_side_effect_guard_rows claim_boundary_rows gate_matrix run_state and doc artifacts exist
- M3067 preserves actor observation shape 72 final action shape 3 and no hidden oracle TTC target provenance source route outcome progress or verdict actor inputs
- M3067 executes the M3065 candidate as a direct action actor with base_policy_required_at_runtime false
- M3067 reports same-denominator current-sim measurement rows without ranking promotion validation or driver-performance verdict claims
- M3067 registers exactly one M3068 result-audit manifest

## Failure Criteria

- M3067 exposes hidden oracle TTC target provenance source route outcome progress or verdict labels to actor input
- M3067 mutates or promotes parent checkpoints configs profiles actor inputs actor outputs or the M3065 candidate artifact
- M3067 ranks selects a winner promotes a checkpoint or tunes the scenario denominator after measurement
- M3067 runs the direct-action candidate as a residual or requires a runtime base policy
- M3067 claims validation result driver performance current-sim verdict high-fidelity paper full-driver finite-window-vs-GRU or self-ID evidence

## Evidence Gates

- M3067 must consume the M3066 audit and M3065 direct-action candidate artifact
- M3067 must preserve actor observation shape 72 and final action shape 3 with no hidden oracle TTC target provenance source route outcome progress or verdict actor inputs
- M3067 must execute the M3065 candidate as a direct action actor: final_action = clip(obs72 @ linear_weight + linear_bias, action_low, action_high)
- M3067 must not require a base policy at runtime
- M3067 must run a bounded same-denominator current-sim measurement preflight and write episode metric adapter guard claim gate summary doc and M3068 audit manifest artifacts
- M3067 must report collisions offtrack boundary clearance stability recovery actuation and robustness metrics without ranking or promoting a checkpoint
- M3067 must not mutate parent checkpoints configs profiles actor inputs actor outputs or the M3065 candidate artifact
- M3067 must not claim validation driver-performance verdict current-sim verdict high-fidelity result paper evidence finite-window-vs-GRU conclusion full-driver completion or self-ID evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not expose target_action target_action_mask target_loss_weight target provenance objective labels source labels route labels outcome labels progress labels verdict labels hidden oracle values or TTC to actor input
- do not run the M3065 candidate as a residual or with an undisclosed base policy
- do not rank select promote mutate or overwrite parent checkpoints configs profiles actor inputs actor outputs or the M3065 candidate artifact
- do not tune the direct-action candidate profile scenario denominator or baseline context after seeing M3067 measurement rows
- do not convert current-sim measurement rows into validation driver-performance high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims

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

- milestone: m3067-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-preflight
- type: infrastructure
- checkpoint: runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/summary.json
- success_rate: 0.25
- termination_rate: None
- clearance_margin_mean: 8.49553
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_offtrack_behavior_direct_action_closed_loop_measurement_route_to_m3068_result_audit
- reason: Completed: ran bounded same-denominator current-sim measurement for the M3065 direct-action candidate as full obs72-to-action3 actor with status_pass true gate_matrix_pass true required_artifacts_present true 32/32 episode rows 0 failures 8 success 4 collision 16 offtrack 5 speed_too_low raw_action_abs_max 2.2606801986694336 action_clip_fraction_mean 0.03451952273501378 final_action_abs_max 1.0 actor 72/action 3 direct_action_clipped [steer throttle brake] base_policy_required false runtime_base_policy_required false direct-action adapter actor-contract side-effect and claim guards pass; no validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims; registered M3068 result audit.

## Next Blocker

m3068-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-result-audit
