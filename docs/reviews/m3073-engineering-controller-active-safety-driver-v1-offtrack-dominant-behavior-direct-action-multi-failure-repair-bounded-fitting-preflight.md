# m3073-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-bounded-fitting-preflight Research Review

## Summary

- Generated at UTC: 20260607T164848Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_direct_action_multi_failure_repair_fit_route_to_m3074_result_audit
- Decision reason: Completed: bounded offline direct-action multi-failure repair fitting produced claim-safe repaired candidate with status_pass true gate_matrix_pass true 24 repair fitting dataset rows 18 fit rows 6 internal-accounting rows 2128 fit samples 768 masked steps final weighted MSE 0.00021525553328820269 parent weighted MSE 0.0002183983045141296 all-accounting weighted MSE 0.002601863211948731 final_action_abs_max 1.0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false; no reset step rollout replay PPO validation ranking promotion checkpoint mutation driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claims; registered M3074 result audit.

## Hypothesis

A bounded offline direct-action multi-failure repair fitting preflight can consume the M3072-accepted M3071 repair contract plus existing direct-action candidate and target-tensor artifacts to fit or fail closed one repaired obs72-to-action3 active-safety reflex candidate before any rollout validation ranking promotion driver-performance high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claim.

## Lineage

- parent_checkpoint: runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/candidate_direct_action_reflex_layer.npz, runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt, runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt
- parent_dataset: docs/m3072-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-contract-result-audit.md, runs/m3071_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_contract_materialization_preflight/summary.json, runs/m3071_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_contract_materialization_preflight/direct_action_repair_contract_rows.csv, runs/m3071_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_contract_materialization_preflight/direct_action_loss_family_rows.csv, runs/m3071_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_contract_materialization_preflight/direct_action_row_admission_rows.csv, runs/m3071_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_contract_materialization_preflight/direct_action_guard_family_rows.csv, runs/m3071_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_contract_materialization_preflight/claim_boundary_rows.csv, runs/m3071_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_contract_materialization_preflight/gate_matrix.csv, runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/summary.json, runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/candidate_direct_action_reflex_layer.npz, runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/summary.json, runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/target_tensor_file_index_rows.csv
- parent_config: experiments/manifests/m3072-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-contract-result-audit.json, experiments/manifests/m3071-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-contract-materialization-preflight.json, experiments/manifests/m3065-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-preflight.json, experiments/manifests/m3061-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-rerun-preflight.json
- parent_objective: fit or fail closed one repaired direct-action active-safety reflex candidate under the M3071 multi-failure contract
- derived_from: m3072-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-contract-result-audit, m3071-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-contract-materialization-preflight, m3065-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-preflight, m3061-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-rerun-preflight
- blocked_by: M3067/M3068/M3070 evidence shows 24/32 non-success rows: 16 offtrack, 4 collision, 5 speed-too-low, M3071 materialized a repair contract but did not fit or validate a repaired policy, M3072 admits only a bounded offline fit-or-fail-closed route with no rollout validation or repair-success claim
- supersedes: unbounded direct refit without M3071 contract guards, closed-loop validation before a repaired candidate exists and is audited
- invalidates: None

## Success Criteria

- runs/m3073_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_bounded_fitting_preflight/summary.json exists
- repair fitting dataset split mask weight loss trace target-quality actor-input checkpoint side-effect claim-boundary gate run-state and doc artifacts exist or fail-closed blockers explain why they cannot
- candidate_direct_action_repair_reflex_layer.npz exists only if fitting contracts pass and remains separate from parent checkpoints
- M3073 preserves actor observation 72 final action 3 direct-action/base-policy-free boundary and no hidden oracle actor inputs
- M3073 registers exactly one M3074 result-audit manifest

## Failure Criteria

- M3073 drops M3071 collision speed-floor action-pressure success-preservation stability clearance or claim-boundary requirements
- M3073 runs rollout replay validation ranking promotion checkpoint mutation or profile tuning
- M3073 changes actor input or output contract or requires a runtime base policy
- M3073 claims target quality fitted-policy quality repair success validation driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver or self-ID evidence

## Evidence Gates

- M3073 must consume M3072/M3071 repair-contract artifacts and preserve all M3071 requirement families
- M3073 must preserve actor observation 72 and action 3 direct [steer throttle brake] output semantics
- M3073 must keep target labels target provenance source route outcome progress verdict TTC and hidden oracle values actor-invisible
- M3073 must write or fail-closed record fitting dataset loss trace actor-input checkpoint side-effect claim-boundary gate run-state and doc artifacts
- M3073 must not run rollout replay validation ranking promotion checkpoint mutation driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claims
- M3073 must register exactly one M3074 result-audit manifest before any interpretation of fitted-policy quality

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset step rollout replay validation ranking promotion or profile tuning
- do not expose target labels target provenance source route outcome progress verdict TTC hidden oracle or paper labels to actor input
- do not mutate or promote parent checkpoints
- do not convert offline fitting loss into target quality fitted policy quality validation repair-success or driver-performance evidence
- do not drop collision speed-floor action-pressure success-preservation stability or clearance rows while focusing on offtrack

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit
- proof_washout
- seed_fragility
- training_instability

## Scoreboard

- milestone: m3073-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-bounded-fitting-preflight
- type: infrastructure
- checkpoint: runs/m3073_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_bounded_fitting_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_direct_action_multi_failure_repair_fit_route_to_m3074_result_audit
- reason: Completed: bounded offline direct-action multi-failure repair fitting produced claim-safe repaired candidate with status_pass true gate_matrix_pass true 24 repair fitting dataset rows 18 fit rows 6 internal-accounting rows 2128 fit samples 768 masked steps final weighted MSE 0.00021525553328820269 parent weighted MSE 0.0002183983045141296 all-accounting weighted MSE 0.002601863211948731 final_action_abs_max 1.0 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false; no reset step rollout replay PPO validation ranking promotion checkpoint mutation driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claims; registered M3074 result audit.

## Next Blocker

m3074-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-bounded-fitting-result-audit
