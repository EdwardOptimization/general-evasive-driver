# m3156-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260608T020641Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_route_a_deployable_benchmark_pack_materialization_route_to_m3157_result_audit
- Decision reason: Completed: materialized M3156 Route A deployable benchmark pack with status_pass true gate_matrix_pass true required_artifacts_present true 18 benchmark metrics 7 known failures collision 5 offtrack 2 M3105 rows 64 success 57 collision 5 offtrack 2 speed_too_low 0 M3153 comparisons 21 action_channel_sensitive 0 actor obs72 direct [steer throttle brake] runtime_base_policy_required false no validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim registered M3157 audit.

## Hypothesis

A bounded materialization can package the deployable M3105/M3103 active-safety reflex baseline into a Route A benchmark and failure-taxonomy pack, preserving obs72/action3 contract evidence, M3105 hard-safety metrics, residual blockers, and M3153 negative replay diagnostics before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3155-engineering-controller-active-safety-driver-residual-action-delta-negative-counterfactual-replay-synthesis.md, docs/m3140-engineering-controller-active-safety-driver-m3105-incumbent-deployable-reflex-interface-result-audit.md
- parent_dataset: runs/m3139_engineering_controller_active_safety_driver_m3105_incumbent_deployable_reflex_interface_materialization_preflight/deployable_contract.json, runs/m3139_engineering_controller_active_safety_driver_m3105_incumbent_deployable_reflex_interface_materialization_preflight/residual_blocker_rows.csv, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/summary.json, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3153_engineering_controller_active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_materialization_preflight/summary.json, runs/m3153_engineering_controller_active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_materialization_preflight/counterfactual_replay_comparison_rows.csv
- parent_config: experiments/manifests/m3155-engineering-controller-active-safety-driver-residual-action-delta-negative-counterfactual-replay-synthesis.json
- parent_objective: materialize a deployable Route A active-safety benchmark pack and known-failure taxonomy from existing evidence
- derived_from: m3155-engineering-controller-active-safety-driver-residual-action-delta-negative-counterfactual-replay-synthesis, m3154-engineering-controller-active-safety-driver-residual-action-delta-counterfactual-replay-diagnostic-result-audit, m3153-engineering-controller-active-safety-driver-residual-action-delta-counterfactual-replay-diagnostic-materialization-preflight, m3140-engineering-controller-active-safety-driver-m3105-incumbent-deployable-reflex-interface-result-audit, m3139-engineering-controller-active-safety-driver-m3105-incumbent-deployable-reflex-interface-materialization-preflight, m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight
- blocked_by: M3155 stops the local action-delta repair branch and pivots to Route A deployable verification pack materialization, M3105/M3139 provides a deployable incumbent but residual blockers remain explicit
- supersedes: continuing local action-delta tuning as the immediate route, unpackaged incumbent evidence spread across M3105 M3139 and M3153 artifacts
- invalidates: None

## Success Criteria

- M3156 summary and benchmark pack artifacts exist
- M3156 preserves M3105/M3139 deployable obs72/action3 contract evidence
- M3156 preserves M3105 metrics and residual blocker taxonomy
- M3156 registers M3157 result audit without overclaiming

## Failure Criteria

- M3156 treats benchmark packaging as validation or driver-performance verdict
- M3156 hides the 5 collision and 2 offtrack residual blockers
- M3156 changes actor input or direct action contract
- M3156 reruns or tunes policies instead of materializing the existing evidence pack

## Evidence Gates

- M3156 must preserve obs72/action3 direct [steer throttle brake] runtime contract
- M3156 must preserve M3105 64-row denominator metrics and residual blocker counts
- M3156 must preserve M3153 negative replay diagnostics as diagnostic-only evidence
- M3156 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run new measurement validation ranking promotion training PPO or checkpoint mutation
- do not hide residual collision/offtrack blockers or the negative M3153 replay result
- do not claim validation ranking promotion driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID evidence

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

- milestone: m3156-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-materialization-preflight
- type: infrastructure
- checkpoint: runs/m3156_engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_materialization_preflight/summary.json
- success_rate: 0.890625
- termination_rate: None
- clearance_margin_mean: 10.981307227309182
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_route_a_deployable_benchmark_pack_materialization_route_to_m3157_result_audit
- reason: Completed: materialized M3156 Route A deployable benchmark pack with status_pass true gate_matrix_pass true required_artifacts_present true 18 benchmark metrics 7 known failures collision 5 offtrack 2 M3105 rows 64 success 57 collision 5 offtrack 2 speed_too_low 0 M3153 comparisons 21 action_channel_sensitive 0 actor obs72 direct [steer throttle brake] runtime_base_policy_required false no validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim registered M3157 audit.

## Next Blocker

m3157-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-result-audit
