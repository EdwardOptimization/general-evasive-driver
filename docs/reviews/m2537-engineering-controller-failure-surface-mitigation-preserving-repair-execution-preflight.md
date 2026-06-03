# m2537-engineering-controller-failure-surface-mitigation-preserving-repair-execution-preflight Research Review

## Summary

- Generated at UTC: 20260603T171615Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: engineering_controller_failure_surface_mitigation_preserving_repair_execution_pass
- Decision reason: M2537 runs bounded mitigation-preserving repair execution status_pass true selected m2537_relax_m2532_bias_8 retained road-boundary and command-conflict proof pass mitigation proof fails 4 improved 1 regressed behavior_regression proof_washout no ranking winner promotion success-rate verdict validation or driver-performance claims

## Hypothesis

One bounded mitigation-preserving repair execution can retain M2532 road-boundary and command-conflict gains while preventing mitigation severity regression across all mitigation primary rows without changing the actor contract or overfitting seed 254302.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/checkpoints/m2532_guarded_actor_head_repair.pt
- parent_dataset: docs/m2536-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis.md, docs/m2535-engineering-controller-failure-surface-mitigation-preserving-repair-design.md, runs/m2534_engineering_controller_failure_surface_mitigation_regression_localization/summary.json, runs/m2534_engineering_controller_failure_surface_mitigation_regression_localization/mitigation_regression_rows.csv, runs/m2534_engineering_controller_failure_surface_mitigation_regression_localization/localization_findings.json, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/summary.json, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/post_repair_smoke_rows.csv, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/protected_gate_evaluation.csv, runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/candidate_config.json, runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/protected_gate_bindings.csv, runs/m2527_engineering_controller_failure_surface_intervention_plan/protected_regression_rows.csv, docs/post-m2470-route-plan.md
- parent_config: experiments/manifests/m2536-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis.json, experiments/manifests/m2535-engineering-controller-failure-surface-mitigation-preserving-repair-design.json
- parent_objective: run one bounded mitigation-preserving repair execution after M2536 synthesis approved continuation
- derived_from: m2536-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis, m2535-engineering-controller-failure-surface-mitigation-preserving-repair-design, m2534-engineering-controller-failure-surface-mitigation-regression-localization-preflight, m2532-engineering-controller-failure-surface-guarded-repair-execution-preflight
- blocked_by: M2536 synthesis approved exactly one bounded mitigation-preserving execution before any further synthesis or pivot, M2534 localized the remaining proof failure to mitigation severity non-regression, fresh/generalization remains deferred until protected proof gates pass
- supersedes: direct public-gate repair without synthesis, seed-254302-only repair, fresh/generalization route before all protected proof gates pass, promotion ranking or validation from partial protected proof
- invalidates: None

## Success Criteria

- runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/summary.json exists
- runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/repair_candidate_sweep.csv exists
- runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/selected_repair_trace.csv exists
- runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/repaired_checkpoint_manifest.json exists
- runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/post_repair_smoke_rows.csv exists
- runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/protected_gate_evaluation.csv exists
- runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/candidate_config_snapshot.json exists
- summary verifies P0 observation shape 72 and action shape 3 unchanged
- summary verifies hidden_or_oracle_actor_inputs_required false active_config_overwritten false candidate_config_mutated false and checkpoint_promoted false
- summary separates status_pass from protected_proof_gates_all_passed
- protected gate evaluation rows trace to M2527/M2528 bindings
- protected gate evaluation includes retained road-boundary retained command-conflict and mitigation-preserving proof results
- no external high-fidelity simulation ranking winner success-rate promotion validation or performance claim is made

## Failure Criteria

- M2537 installs imports or runs Chrono or another external simulator
- M2537 changes actor input or action contract
- M2537 injects hidden or oracle actor features
- M2537 overwrites an active config or mutates M2528 candidate config in place
- M2537 promotes a checkpoint or selects a winner
- M2537 treats protected repair smoke as driver performance
- M2537 ranks controller families or computes success-rate verdict
- M2537 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2537 must preserve P0 observation shape 72 action shape 3 and no hidden/oracle actor input boundary
- M2537 may run bounded source-only policy actions and repair execution only inside runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution
- M2537 must write summary repair_candidate_sweep selected_repair_trace repaired_checkpoint_manifest post_repair_smoke_rows protected_gate_evaluation and candidate_config_snapshot artifacts
- M2537 must keep M2532 repaired checkpoint M2528 candidate config and active configs unchanged
- M2537 must evaluate retained road_boundary_proof retained command_conflict_proof and mitigation_preserving_proof before any fresh/generalization interpretation
- M2537 must classify proof_washout behavior_regression training_instability objective_overfit contract_violation lineage_invalid metric_artifact and scenario_sampling_failure as applicable
- M2537 must not rank controllers select winners promote checkpoints compute success rates or make paper self-ID finite-window-vs-GRU current-sim high-fidelity validation or driver-performance verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not install external simulator dependencies
- do not import external high-fidelity simulation packages
- do not run external high-fidelity simulation
- do not use private holdout
- do not change actor inputs
- do not change the deployed action contract
- do not inject hidden or oracle actor features
- do not add rule-switching controller modes
- do not tune only seed 254302
- do not ignore M2532 road-boundary or command-conflict retained gates
- do not mutate the M2528 candidate config in place
- do not overwrite active training configs
- do not promote a checkpoint
- do not rank controller families
- do not select a winner
- do not compute success rate or controller-family verdict metrics
- do not claim high-fidelity validation readiness
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim driver performance from mitigation-preserving repair preflight

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit
- training_instability
- proof_washout

## Scoreboard

- milestone: m2537-engineering-controller-failure-surface-mitigation-preserving-repair-execution-preflight
- type: infrastructure
- checkpoint: runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: engineering_controller_failure_surface_mitigation_preserving_repair_execution_pass
- reason: M2537 runs bounded mitigation-preserving repair execution status_pass true selected m2537_relax_m2532_bias_8 retained road-boundary and command-conflict proof pass mitigation proof fails 4 improved 1 regressed behavior_regression proof_washout no ranking winner promotion success-rate verdict validation or driver-performance claims

## Next Blocker

m2538-engineering-controller-failure-surface-mitigation-preserving-repair-execution-result-audit
