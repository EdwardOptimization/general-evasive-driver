# m3037-engineering-controller-active-safety-driver-v1-baseline-measurement-table-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260607T110755Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_baseline_measurement_table_materialized_route_to_m3038_result_audit
- Decision reason: Completed: materialized Active Safety Driver v1 baseline measurement tables with status_pass true gate_matrix_pass true 32 baseline rows 2 candidate profile aggregates 34 benchmark-role aggregates 31 metric coverage rows 25/25 required metrics materialized 6 actor guards 25 claim rows actor 72/action 3; 0 environment reset step rollout replay training validation ranking promotion checkpoint mutation high-fidelity finite-window-vs-GRU paper driver-performance current-sim verdict full-driver or self-ID claims; registered M3038 result audit.

## Hypothesis

A no-new-execution measurement-table materialization preflight can convert the accepted M3035 Active Safety Driver v1 baseline contract and M3015 closed-loop rows into official baseline measurement tables covering safety clearance stability recovery actuation robustness and role splits before any training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim.

## Lineage

- parent_checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt, runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt
- parent_dataset: docs/m3036-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-result-audit.md, runs/m3035_engineering_controller_active_safety_driver_v1_baseline_contract_materialization_preflight/summary.json, runs/m3035_engineering_controller_active_safety_driver_v1_baseline_contract_materialization_preflight/baseline_candidate_rows.csv, runs/m3035_engineering_controller_active_safety_driver_v1_baseline_contract_materialization_preflight/benchmark_role_rows.csv, runs/m3035_engineering_controller_active_safety_driver_v1_baseline_contract_materialization_preflight/metric_contract_rows.csv, runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/episode_rows.csv, runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/profile_aggregate_rows.csv
- parent_config: experiments/manifests/m3037-engineering-controller-active-safety-driver-v1-baseline-measurement-table-materialization-preflight.json, experiments/manifests/m3036-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-result-audit.json, experiments/manifests/m3035-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-preflight.json
- parent_objective: materialize official Active Safety Driver v1 baseline measurement tables before training or architecture comparison
- derived_from: m3036-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-result-audit, m3035-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-preflight, m3034-engineering-controller-active-safety-driver-v1-baseline-freeze-design, m3015-engineering-controller-route-a-post-residual-stop-new-source-bounded-execution-preflight
- blocked_by: M3036 accepts M3035 contract but the official baseline measurement tables do not yet exist, Active Safety Driver v1 needs safety clearance stability recovery and robustness baseline aggregates before training or architecture comparison, M3015 diagnostic rows must be re-materialized under M3035 claim boundaries before being used as baseline measurement context
- supersedes: manual interpretation of M3015 diagnostic rows as active-safety baseline metrics, direct training or ranking before baseline measurement table materialization
- invalidates: None

## Success Criteria

- runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight/summary.json exists
- M3037 materializes baseline measurement rows candidate profile aggregates benchmark role aggregates metric coverage actor claim and gate rows
- M3037 preserves actor 72/action 3 and forbidden shortcut boundaries
- M3037 registers exactly one M3038 result-audit manifest before any training validation ranking promotion high-fidelity or self-ID claim

## Failure Criteria

- M3037 cannot materialize row-level baseline measurement rows
- M3037 cannot materialize candidate profile aggregate or benchmark-role aggregate metric rows
- M3037 treats M3032 target tensors as closed-loop performance evidence
- M3037 ranks or promotes a checkpoint
- M3037 runs environment reset step rollout training validation high-fidelity or architecture comparison

## Evidence Gates

- M3037 must preserve actor 72/action 3 and M3035 forbidden shortcut boundaries
- M3037 must materialize 32 baseline measurement rows from M3015 closed-loop rows
- M3037 must materialize candidate profile aggregate rows for the M2655 candidate and M1674 parent checkpoint
- M3037 must materialize benchmark-role aggregate rows using M3035 benchmark role rows
- M3037 must record collision off-track clearance stability recovery actuation and robustness metrics without ranking or promotion
- M3037 must register exactly one M3038 result-audit follow-up manifest

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset step rollout replay training validation ranking promotion high-fidelity or finite-window-vs-GRU comparison
- do not claim driver performance current-sim verdict validation result high-fidelity result paper evidence full-driver completion or self-ID evidence
- do not use hidden dynamics mu slip tire force oracle feasibility TTC labels reference trajectory or precomputed verdict labels as actor inputs
- do not use M3032 target tensors as closed-loop measurement evidence
- do not mutate checkpoints configs profiles or actor contract

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

- milestone: m3037-engineering-controller-active-safety-driver-v1-baseline-measurement-table-materialization-preflight
- type: infrastructure
- checkpoint: runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_baseline_measurement_table_materialized_route_to_m3038_result_audit
- reason: Completed: materialized Active Safety Driver v1 baseline measurement tables with status_pass true gate_matrix_pass true 32 baseline rows 2 candidate profile aggregates 34 benchmark-role aggregates 31 metric coverage rows 25/25 required metrics materialized 6 actor guards 25 claim rows actor 72/action 3; 0 environment reset step rollout replay training validation ranking promotion checkpoint mutation high-fidelity finite-window-vs-GRU paper driver-performance current-sim verdict full-driver or self-ID claims; registered M3038 result audit.

## Next Blocker

m3038-engineering-controller-active-safety-driver-v1-baseline-measurement-table-result-audit
