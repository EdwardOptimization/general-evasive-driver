# m2532-engineering-controller-failure-surface-guarded-repair-execution-preflight Research Review

## Summary

- Generated at UTC: 20260603T155233Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: engineering_controller_failure_surface_guarded_repair_execution_pass
- Decision reason: M2532 runs behavior-changing guarded source-only repair execution from M2528 config writes repaired checkpoint training trace manifest post-repair rows gate evaluation 45 rows 7 gates road-boundary and command-conflict proof pass mitigation proof fails one row protected_proof_gates_all_passed false no ranking winner promotion success-rate verdict validation or driver-performance claims

## Hypothesis

A bounded guarded repair execution can produce the first post-repair closed-loop behavior evidence against the protected failure surface while preserving the deployed actor contract and avoiding promotion or validation overclaims.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m2531-engineering-controller-failure-surface-guarded-repair-execution-design.md, docs/m2530-engineering-controller-failure-surface-intervention-repair-smoke-result-audit.md, runs/m2529_engineering_controller_failure_surface_intervention_repair_smoke/summary.json, runs/m2529_engineering_controller_failure_surface_intervention_repair_smoke/protected_gate_evaluation.csv, runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/candidate_config.json, runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/protected_gate_bindings.csv, runs/m2527_engineering_controller_failure_surface_intervention_plan/protected_regression_rows.csv
- parent_config: experiments/manifests/m2531-engineering-controller-failure-surface-guarded-repair-execution-design.json
- parent_objective: run the minimal bounded guarded repair execution and post-repair protected proof smoke after M2531 design
- derived_from: m2531-engineering-controller-failure-surface-guarded-repair-execution-design, m2530-engineering-controller-failure-surface-intervention-repair-smoke-result-audit, m2529-engineering-controller-failure-surface-intervention-repair-smoke-preflight
- blocked_by: M2529 no-update smoke confirmed the current actor does not improve protected proof gates without actual repair, M2531 selected guarded repair execution as the next evidence-producing step, Route A still lacks any post-repair closed-loop behavior evidence
- supersedes: another config-only or no-update artifact before repair execution, direct promotion or ranking before proof gates, training without protected gate traceability and rollback artifacts
- invalidates: None

## Success Criteria

- runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/summary.json exists
- runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/repair_training_trace.csv exists
- runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/repaired_checkpoint_manifest.json exists
- runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/post_repair_smoke_rows.csv exists
- runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/protected_gate_evaluation.csv exists
- runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/candidate_config_snapshot.json exists
- summary verifies P0 observation shape 72 and action shape 3 unchanged
- summary verifies hidden_or_oracle_actor_inputs_required false active_config_overwritten false candidate_config_mutated false and checkpoint_promoted false
- summary separates status_pass from protected_proof_gates_all_passed
- protected gate evaluation rows trace to M2527/M2528 bindings
- no external high-fidelity simulation ranking winner success-rate promotion validation or performance claim is made

## Failure Criteria

- M2532 installs imports or runs Chrono or another external simulator
- M2532 changes actor input or action contract
- M2532 injects hidden or oracle actor features
- M2532 overwrites an active config or mutates M2528 candidate config in place
- M2532 promotes a checkpoint or selects a winner
- M2532 treats repair smoke as driver performance
- M2532 ranks controller families or computes success-rate verdict
- M2532 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2532 must preserve P0 observation shape 72 action shape 3 and no hidden/oracle actor input boundary
- M2532 may run bounded source-only guarded repair training only inside runs/m2532_engineering_controller_failure_surface_guarded_repair_execution
- M2532 must write summary repair_training_trace repaired_checkpoint_manifest post_repair_smoke_rows protected_gate_evaluation and candidate_config_snapshot artifacts
- M2532 must keep source checkpoint M2528 candidate config and active configs unchanged
- M2532 must evaluate protected proof gates before any fresh/generalization interpretation
- M2532 must classify proof_washout behavior_regression training_instability objective_overfit contract_violation lineage_invalid metric_artifact and scenario_sampling_failure as applicable
- M2532 must not rank controllers select winners promote checkpoints compute success rates or make paper self-ID finite-window-vs-GRU current-sim high-fidelity validation or driver-performance verdict claims

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
- do not tune protected rows in place without writing training trace and post-repair gate evidence
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
- do not claim driver performance from guarded repair preflight

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

- milestone: m2532-engineering-controller-failure-surface-guarded-repair-execution-preflight
- type: infrastructure
- checkpoint: runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: engineering_controller_failure_surface_guarded_repair_execution_pass
- reason: M2532 runs behavior-changing guarded source-only repair execution from M2528 config writes repaired checkpoint training trace manifest post-repair rows gate evaluation 45 rows 7 gates road-boundary and command-conflict proof pass mitigation proof fails one row protected_proof_gates_all_passed false no ranking winner promotion success-rate verdict validation or driver-performance claims

## Next Blocker

m2533-engineering-controller-failure-surface-guarded-repair-execution-result-audit
