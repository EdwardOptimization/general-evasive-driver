# m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis Research Review

## Summary

- Generated at UTC: 20260607T205657Z
- Type: gate
- Gate tier: process
- Promotion decision: pivot_to_m3108_residual_collision_offtrack_failure_decomposition
- Decision reason: Completed: synthesis classifies M3105 as complete and claim-safe but plateaued versus M3095 with 57 success 5 collision 2 offtrack 0 speed_too_low and no aggregate improvement over M3095; M3105 removes M3100 regressions but does not solve residual hard-safety blockers so it is not validation repair-success performance current-sim verdict robustness-result high-fidelity paper full-driver or self-ID evidence. Pivots to M3108 residual collision/offtrack failure decomposition under new branch active_safety_driver_residual_collision_offtrack_decomposition.

## Hypothesis

A bounded synthesis can classify the M3105 no-regression plateau and residual collision/offtrack blockers and select exactly one next active-safety route before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3106-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-result-audit.md, docs/m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight.md, runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight/direct_action_policy_config.json
- parent_dataset: runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/summary.json, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/same_row_comparison_rows.csv, runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv
- parent_config: experiments/manifests/m3106-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-result-audit.json, experiments/manifests/m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight.json
- parent_objective: synthesize M3105 plateau evidence and choose one residual hard-safety route
- derived_from: m3106-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-result-audit, m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight, m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-preflight, m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight
- blocked_by: M3105 matches M3095 but leaves 5 collision and 2 offtrack failures, continuing narrow v4 no-regression edits risks local-search overfit without changing the residual hard-safety evidence
- supersedes: direct continuation of v4 no-regression materialization without plateau synthesis
- invalidates: None

## Success Criteria

- docs/m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis.md exists
- M3107 answers all workflow synthesis questions
- M3107 selects exactly one next route or stop state
- M3107 preserves obs72/action3 direct-action and claim boundaries

## Failure Criteria

- M3107 hides the residual 5 collision and 2 offtrack blockers
- M3107 treats M3105 as validation repair-success or performance evidence
- M3107 leaves the next route ambiguous
- M3107 proposes hidden actor inputs runtime base policy or post-hoc row tuning

## Evidence Gates

- M3107 must classify M3105 versus M3095 M3100 and M3090 without validation ranking promotion or repair-success claims
- M3107 must preserve the obs72/action3 direct [steer throttle brake] deployable actor boundary
- M3107 must explicitly decide whether to pivot to residual collision/offtrack repair decomposition stronger hard-safety materialization or stop
- M3107 must register exactly one follow-up route if it continues

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun tune expand rank promote validate or mutate checkpoints
- do not treat M3105 no-regression versus M3095 as repair-success driver-performance current-sim robustness-result high-fidelity paper full-driver or self-ID evidence
- do not use hidden oracle TTC target source route outcome progress verdict labels or baseline outcomes as actor input

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

- milestone: m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis
- type: gate
- checkpoint: docs/m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: pivot_to_m3108_residual_collision_offtrack_failure_decomposition
- reason: Completed: synthesis classifies M3105 as complete and claim-safe but plateaued versus M3095 with 57 success 5 collision 2 offtrack 0 speed_too_low and no aggregate improvement over M3095; M3105 removes M3100 regressions but does not solve residual hard-safety blockers so it is not validation repair-success performance current-sim verdict robustness-result high-fidelity paper full-driver or self-ID evidence. Pivots to M3108 residual collision/offtrack failure decomposition under new branch active_safety_driver_residual_collision_offtrack_decomposition.

## Next Blocker

m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis
