# m2534-engineering-controller-failure-surface-mitigation-regression-localization-preflight Research Review

## Summary

- Generated at UTC: 20260603T162816Z
- Type: gate
- Gate tier: proof
- Promotion decision: route_to_mitigation_preserving_repair_design
- Decision reason: M2534 localizes M2532 mitigation regression 5 mitigation rows 4 improved 1 regressed seed 254302 all mitigation rows improve road-margin and command-conflict but one low-baseline severity regresses behavior_regression proof_washout objective_overfit no metric artifact route to M2535 no new policy action training ranking promotion success-rate verdict validation or driver-performance claims

## Hypothesis

A bounded localization pass can explain the single M2532 mitigation regression well enough to choose a targeted mitigation repair design or branch synthesis without overfitting a public protected row.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/checkpoints/m2532_guarded_actor_head_repair.pt
- parent_dataset: docs/m2533-engineering-controller-failure-surface-guarded-repair-execution-result-audit.md, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/summary.json, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/repair_training_trace.csv, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/repaired_checkpoint_manifest.json, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/post_repair_smoke_rows.csv, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/protected_gate_evaluation.csv, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/candidate_config_snapshot.json, runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/candidate_config.json, runs/m2527_engineering_controller_failure_surface_intervention_plan/protected_regression_rows.csv, docs/post-m2470-route-plan.md
- parent_config: experiments/manifests/m2533-engineering-controller-failure-surface-guarded-repair-execution-result-audit.json, experiments/manifests/m2532-engineering-controller-failure-surface-guarded-repair-execution-preflight.json
- parent_objective: localize the single remaining mitigation regression from M2532 before another repair attempt or generalization claim
- derived_from: m2533-engineering-controller-failure-surface-guarded-repair-execution-result-audit, m2532-engineering-controller-failure-surface-guarded-repair-execution-preflight
- blocked_by: M2532 passed road_boundary_proof and command_conflict_proof but mitigation_proof failed on one protected unavoidable_mitigation row, M2533 accepted M2532 as partial guarded repair evidence and rejected promotion or generalization interpretation, another repair update would be narrow public-gate repair unless the mitigation regression is localized first
- supersedes: direct second repair execution without diagnosing the mitigation regression, fresh/generalization route before all protected proof gates pass, promotion or ranking from partial protected proof
- invalidates: None

## Success Criteria

- runs/m2534_engineering_controller_failure_surface_mitigation_regression_localization/summary.json exists
- runs/m2534_engineering_controller_failure_surface_mitigation_regression_localization/mitigation_regression_rows.csv exists
- runs/m2534_engineering_controller_failure_surface_mitigation_regression_localization/localization_findings.json exists
- summary identifies the regressed mitigation row and compares it against the four improved mitigation rows
- summary separates road-margin improvement command-conflict improvement and severity regression
- summary classifies proof_washout behavior_regression metric_artifact scenario_sampling_failure and objective_overfit as applicable
- summary preserves actor contract 72/3 hidden_or_oracle_actor_inputs_required false candidate_config_mutated false active_config_overwritten false and false claim flags
- no external high-fidelity simulation install import execution new policy action training ranking winner success-rate or verdict claim is made by M2534

## Failure Criteria

- M2534 installs imports or runs Chrono or another external simulator
- M2534 changes actor input or action contract
- M2534 injects hidden or oracle actor features
- M2534 steps an environment or runs policy rollout
- M2534 starts training
- M2534 treats mitigation localization as driver performance
- M2534 treats localization as protected proof-gate pass
- M2534 ranks controller families or selects a winner
- M2534 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2534 must localize the M2532 mitigation_proof failure using existing M2532/M2528/M2527 artifacts only
- M2534 must identify the regressed row and compare it against the four improved mitigation rows
- M2534 must separate severity regression from road-margin improvement and command-conflict improvement
- M2534 must assess whether the regression is consistent with proof_washout, metric artifact, objective weakness, or scenario sampling risk
- M2534 must preserve actor contract 72/3 no hidden/oracle inputs and no rule-switching actor boundary
- M2534 must not run new policy actions train replay PPO rank controllers select winners promote checkpoints compute success rates or make paper self-ID finite-window-vs-GRU current-sim high-fidelity validation or driver-performance verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not install external simulator dependencies
- do not import external high-fidelity simulation packages
- do not run external high-fidelity simulation
- do not execute new policy actions
- do not train
- do not run replay
- do not run PPO
- do not promote the M2532 checkpoint
- do not use private holdout
- do not change actor inputs
- do not change the deployed action contract
- do not inject hidden or oracle actor features
- do not tune the regressed protected row in place
- do not rank controller families
- do not select a winner
- do not compute success rate or controller-family verdict metrics
- do not claim high-fidelity validation readiness
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim driver performance from mitigation localization

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

- milestone: m2534-engineering-controller-failure-surface-mitigation-regression-localization-preflight
- type: gate
- checkpoint: runs/m2534_engineering_controller_failure_surface_mitigation_regression_localization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_mitigation_preserving_repair_design
- reason: M2534 localizes M2532 mitigation regression 5 mitigation rows 4 improved 1 regressed seed 254302 all mitigation rows improve road-margin and command-conflict but one low-baseline severity regresses behavior_regression proof_washout objective_overfit no metric artifact route to M2535 no new policy action training ranking promotion success-rate verdict validation or driver-performance claims

## Next Blocker

m2535-engineering-controller-failure-surface-mitigation-preserving-repair-design
