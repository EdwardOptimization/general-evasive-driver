# m3045-engineering-controller-active-safety-driver-v1-failure-decomposition-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260607T122006Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_failure_decomposition_route_to_m3046_result_audit
- Decision reason: Completed: materialized M3043 row-preserving failure decomposition with status_pass true gate_matrix_pass true 32/32 measurement rows 17 failure_mode rows 9 actuation_saturation rows 6 repair_requirement rows 24 offtrack 4 collision 1 speed_too_low candidate action_clip_fraction_mean 0.41243192505631066 parent action_clip_fraction_mean 0.0 actor 72/action 3 no reset step rollout replay fitting training validation ranking promotion driver-performance high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims; registered M3046 result audit.

## Hypothesis

A no-new-execution failure-decomposition materialization preflight can convert the accepted M3044/M3043 closed-loop measurement evidence into row-preserving offtrack collision speed-floor actuation-saturation repair requirements before any fitting training validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim.

## Lineage

- parent_checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt, runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt
- parent_dataset: docs/m3044-engineering-controller-active-safety-driver-v1-closed-loop-measurement-result-audit.md, runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight/summary.json, runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight/measurement_episode_rows.csv, runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight/metric_summary_rows.csv, runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight/residual_adapter_guard_rows.csv, runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight/actor_contract_guard_rows.csv, runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight/checkpoint_side_effect_guard_rows.csv, runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight/claim_boundary_rows.csv, runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight/gate_matrix.csv
- parent_config: experiments/manifests/m3044-engineering-controller-active-safety-driver-v1-closed-loop-measurement-result-audit.json, experiments/manifests/m3043-engineering-controller-active-safety-driver-v1-closed-loop-measurement-preflight.json
- parent_objective: materialize closed-loop failure decomposition before any repair or rerun
- derived_from: m3044-engineering-controller-active-safety-driver-v1-closed-loop-measurement-result-audit, m3043-engineering-controller-active-safety-driver-v1-closed-loop-measurement-preflight
- blocked_by: M3044 accepts M3043 as complete measurement evidence but rejects direct repair-success or driver-performance claims, M3043 failures are offtrack-dominant with candidate-binding action saturation and require decomposition before another fitting or rollout route
- supersedes: direct candidate refit or rerun without preserving the M3043 failure denominator
- invalidates: None

## Success Criteria

- runs/m3045_engineering_controller_active_safety_driver_v1_failure_decomposition_materialization_preflight/summary.json exists
- failure_mode_rows actuation_saturation_rows repair_requirement_rows claim_boundary_rows gate_matrix run_state and doc artifacts exist
- M3045 preserves all 32 M3043 measurement rows in decomposition accounting
- M3045 registers exactly one M3046 result-audit manifest
- M3045 makes no validation ranking promotion driver-performance current-sim verdict high-fidelity paper finite-window-vs-GRU full-driver or self-ID claim

## Failure Criteria

- M3045 drops negative M3043 rows or cherry-picks the positive delta row
- M3045 treats M3043 measurements as driver-performance validation or repair success
- M3045 runs new rollout fitting training ranking promotion or checkpoint mutation
- M3045 leaves next repair or stop route ambiguous

## Evidence Gates

- M3045 must consume M3044 audit and all required M3043 summary episode metric guard claim and gate artifacts
- M3045 must preserve all 32 M3043 measurement rows without cherry-picking successes or deltas
- M3045 must materialize failure decomposition rows for offtrack collision speed-too-low success and role/family splits
- M3045 must materialize actuation saturation rows that separate residual clipping from final action clipping
- M3045 must materialize repair requirement rows without running fitting training rollout validation ranking or promotion
- M3045 must preserve actor observation shape 72 final action shape 3 and no hidden oracle TTC target provenance source route outcome progress or verdict actor inputs
- M3045 must register exactly one M3046 result-audit manifest

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run reset step rollout replay fitting PPO training validation ranking promotion high-fidelity or architecture comparison
- do not drop negative candidate rows or parent rows from the M3043 denominator
- do not convert M3043 measurement rows into driver-performance current-sim validation high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims
- do not mutate checkpoints profiles configs actor inputs actor outputs or the M3041 residual artifact

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

- milestone: m3045-engineering-controller-active-safety-driver-v1-failure-decomposition-materialization-preflight
- type: infrastructure
- checkpoint: runs/m3045_engineering_controller_active_safety_driver_v1_failure_decomposition_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_failure_decomposition_route_to_m3046_result_audit
- reason: Completed: materialized M3043 row-preserving failure decomposition with status_pass true gate_matrix_pass true 32/32 measurement rows 17 failure_mode rows 9 actuation_saturation rows 6 repair_requirement rows 24 offtrack 4 collision 1 speed_too_low candidate action_clip_fraction_mean 0.41243192505631066 parent action_clip_fraction_mean 0.0 actor 72/action 3 no reset step rollout replay fitting training validation ranking promotion driver-performance high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims; registered M3046 result audit.

## Next Blocker

m3046-engineering-controller-active-safety-driver-v1-failure-decomposition-result-audit
