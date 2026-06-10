# m3138-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-result-audit Research Review

## Summary

- Generated at UTC: 20260608T001251Z
- Type: gate
- Gate tier: process
- Promotion decision: accept_m3137_artifacts_reject_behavior_regression_stop_guarded_fallback_hybrid_branch_retain_m3105_incumbent
- Decision reason: Completed: audit accepts M3137 artifacts as complete and claim-safe with 64/64 episode rows 0 failures 256 same-row comparisons exact-seed aligned against M3105 M3095 M3100 M3090; M3137 is behavior-negative vs M3105 and M3095 with success_delta -1 collision_delta +1 offtrack_delta 0 speed_too_low_delta 0, so rejects repair-success validation ranking promotion driver-performance current-sim high-fidelity paper full-driver robustness-result feasibility-proof and self-ID claims; stops guarded fallback hybrid branch and retains M3105/M3103 no-regression direct-action reflex as incumbent.

## Hypothesis

A bounded result audit can accept or reject the M3137 residual regression-aware guarded fallback hybrid full-fresh measurement artifacts before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3137-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-preflight.md, runs/m3135_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_preflight/direct_action_policy_config.json
- parent_dataset: runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/summary.json, runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/measurement_episode_rows.csv, runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/measurement_failure_rows.csv, runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/measurement_metric_summary_rows.csv, runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/measurement_contract_guard_rows.csv, runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/same_row_comparison_rows.csv, runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/claim_boundary_rows.csv, runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/gate_matrix.csv
- parent_config: experiments/manifests/m3137-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-preflight.json
- parent_objective: audit full-fresh M3135 residual regression-aware guarded fallback hybrid repair measurement before broader interpretation
- derived_from: m3137-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-preflight, m3136-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-result-audit, m3135-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-preflight, m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight, m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight, m3100-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-preflight
- blocked_by: M3137 full-fresh measurement rows require audit before any validation or repair-success route, same-row comparison against M3105 M3095 M3100 and M3090 is measurement context and not a performance verdict before M3138
- supersedes: direct interpretation of M3137 rows without audit
- invalidates: None

## Success Criteria

- docs/m3138-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-result-audit.md exists
- M3138 audits M3137 row counts gates actor contract same-row comparison and claim boundaries
- M3138 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3138 selects exactly one next route or stop state

## Failure Criteria

- M3138 hides M3137 failures or missing artifacts
- M3138 treats M3137 runtime measurement as validation repair-success or performance verdict
- M3138 changes actor input or action contract
- M3138 leaves next route ambiguous

## Evidence Gates

- M3138 must audit M3137 summary measurement comparison metric guard claim and gate artifacts
- M3138 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false
- M3138 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims
- M3138 must select exactly one behavior synthesis validation-planning stop or next repair route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun tune expand rank promote validate or mutate checkpoints
- do not convert M3137 same-row deltas into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success or self-ID claims
- do not change actor input or action contract

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

- milestone: m3138-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-result-audit
- type: gate
- checkpoint: docs/m3138-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: accept_m3137_artifacts_reject_behavior_regression_stop_guarded_fallback_hybrid_branch_retain_m3105_incumbent
- reason: Completed: audit accepts M3137 artifacts as complete and claim-safe with 64/64 episode rows 0 failures 256 same-row comparisons exact-seed aligned against M3105 M3095 M3100 M3090; M3137 is behavior-negative vs M3105 and M3095 with success_delta -1 collision_delta +1 offtrack_delta 0 speed_too_low_delta 0, so rejects repair-success validation ranking promotion driver-performance current-sim high-fidelity paper full-driver robustness-result feasibility-proof and self-ID claims; stops guarded fallback hybrid branch and retains M3105/M3103 no-regression direct-action reflex as incumbent.

## Next Blocker

m3138-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-result-audit
