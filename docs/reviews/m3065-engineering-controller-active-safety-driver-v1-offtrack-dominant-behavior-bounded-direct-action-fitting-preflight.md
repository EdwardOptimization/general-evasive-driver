# m3065-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-preflight Research Review

## Summary

- Generated at UTC: 20260607T152023Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_offtrack_behavior_direct_action_fit_route_to_m3066_result_audit
- Decision reason: Completed: bounded direct-action fitting preflight produced claim-safe candidate with status_pass true gate_matrix_pass true required_artifacts_present true 24 fitting dataset rows 18 fit rows 6 internal-accounting rows 2128 fitting samples 768 masked recovery steps initial weighted MSE 0.6617927582032398 final weighted MSE 0.00020769915329666637 all-accounting weighted MSE 0.0023938326408113344 predicted_action_abs_max 1.0 actor 72/action 3 direct [steer throttle brake] base_policy_required false; target labels/provenance hidden oracle TTC actor inputs false; 0 reset step rollout replay PPO training validation ranking promotion checkpoint mutation driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims; registered M3066 result audit.

## Hypothesis

A bounded offline direct-action fitting preflight can consume the M3064-admitted M3061 raw-trace-backed target tensor artifacts and M3055 direct-action fitting contract to fit or fail closed one deployable obs72-to-action3 active-safety reflex candidate artifact before any rollout validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claim.

## Lineage

- parent_checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt, runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt
- parent_dataset: docs/m3064-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-admission-design.md, docs/m3063-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-to-fitting-branch-synthesis.md, docs/m3062-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-rerun-result-audit.md, runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/summary.json, runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/behavior_target_tensor_rows.csv, runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/target_tensor_file_index_rows.csv, runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/target_tensor_weight_rows.csv, runs/m3055_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_fitting_contract_materialization_preflight/fitting_contract_rows.csv, runs/m3055_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_fitting_contract_materialization_preflight/loss_family_rows.csv
- parent_config: experiments/manifests/m3064-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-admission-design.json, experiments/manifests/m3063-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-to-fitting-branch-synthesis.json, experiments/manifests/m3062-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-rerun-result-audit.json, experiments/manifests/m3061-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-rerun-preflight.json
- parent_objective: fit or fail closed one bounded direct obs72-to-action3 active-safety reflex candidate artifact for later audit
- derived_from: m3064-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-admission-design, m3063-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-to-fitting-branch-synthesis, m3062-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-rerun-result-audit, m3061-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-rerun-preflight, m3055-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-contract-materialization-preflight
- blocked_by: M3064 admits exactly one bounded direct-action fitting preflight and rejects direct validation or performance claims, M3061 target tensor artifacts are complete but target quality and closed-loop behavior remain unvalidated, a deployable direct-action candidate artifact does not yet exist for result audit or later measurement admission
- supersedes: materialization-only route before fitting a direct-action candidate artifact, direct rollout validation ranking promotion or driver-performance claim before fitting result audit
- invalidates: None

## Success Criteria

- runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/summary.json exists
- fitting_dataset_rows split_rows mask_weight_rows fitting_loss_trace_rows target_quality_boundary_rows actor_input_exclusion_rows checkpoint_side_effect_guard_rows claim_boundary_rows gate_matrix run_state and doc artifacts exist
- candidate_direct_action_reflex_layer.npz exists only if fitting contracts pass and remains separate from parent checkpoints
- M3065 consumes only actor-visible observation traces and actor-invisible trainer-side target_action tensors
- M3065 registers exactly one M3066 result-audit manifest
- M3065 makes no rollout validation ranking promotion driver-performance current-sim high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim

## Failure Criteria

- M3065 exposes hidden oracle TTC target provenance source route outcome progress verdict paper labels or target labels to actor input
- M3065 mutates saves over ranks selects or promotes parent checkpoints configs profiles actor inputs actor outputs or fitted artifacts
- M3065 runs reset step rollout replay validation ranking promotion high-fidelity or finite-window-vs-GRU comparison
- M3065 uses raw replay actions as corrected target actions or hides raw_action_trace_used_as_target failures
- M3065 claims target quality repair success validation result driver performance current-sim high-fidelity paper full-driver finite-window-vs-GRU or self-ID evidence

## Evidence Gates

- M3065 must consume M3064 design, M3063 synthesis, M3062 audit, M3061 target tensors, and M3055 direct-action fitting contract
- M3065 must build a fitting dataset only from actor-visible observation traces and actor-invisible trainer-side target_action tensors
- M3065 must use target_action_mask and target_loss_weight as the fitting denominator and report split mask weight accounting
- M3065 must fit or fail closed exactly one bounded direct obs72-to-action3 candidate artifact with output [steer throttle brake]
- M3065 must keep target labels provenance source route outcome progress verdict TTC oracle and paper labels out of actor inputs
- M3065 must not run environment reset step rollout replay validation ranking promotion high-fidelity finite-window-vs-GRU full-driver or self-ID testing
- M3065 must register M3066 result audit before any fitted artifact can inform measurement admission

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not expose target_action target_action_mask target_loss_weight target provenance source route outcome progress verdict TTC oracle or paper labels to actor input
- do not use raw replay actions as corrected recovery targets
- do not run environment reset step rollout replay validation ranking promotion high-fidelity or finite-window-vs-GRU comparison
- do not mutate save over rank select or promote parent checkpoints or the fitted candidate artifact
- do not convert fitting loss decrease into target quality repair success validation driver performance current-sim high-fidelity paper full-driver or self-ID evidence

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- training_instability
- scenario_sampling_failure
- behavior_regression
- objective_overfit
- proof_washout
- seed_fragility

## Scoreboard

- milestone: m3065-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-preflight
- type: infrastructure
- checkpoint: runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_offtrack_behavior_direct_action_fit_route_to_m3066_result_audit
- reason: Completed: bounded direct-action fitting preflight produced claim-safe candidate with status_pass true gate_matrix_pass true required_artifacts_present true 24 fitting dataset rows 18 fit rows 6 internal-accounting rows 2128 fitting samples 768 masked recovery steps initial weighted MSE 0.6617927582032398 final weighted MSE 0.00020769915329666637 all-accounting weighted MSE 0.0023938326408113344 predicted_action_abs_max 1.0 actor 72/action 3 direct [steer throttle brake] base_policy_required false; target labels/provenance hidden oracle TTC actor inputs false; 0 reset step rollout replay PPO training validation ranking promotion checkpoint mutation driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims; registered M3066 result audit.

## Next Blocker

m3066-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-result-audit
