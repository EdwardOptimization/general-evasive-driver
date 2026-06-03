# m2529-engineering-controller-failure-surface-intervention-repair-smoke-preflight Research Review

## Summary

- Generated at UTC: 20260603T150212Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: engineering_controller_failure_surface_intervention_repair_smoke_pass
- Decision reason: M2529 runs bounded source-only no-update repair smoke from M2528 candidate config 45 repair smoke rows 7 protected gate evaluations 45 protected rows matched contract/no-oracle/no-ranking gates pass road-boundary mitigation command-conflict proof gates fail negative smoke recorded fresh generalization deferred no training ranking winner promotion success-rate verdict validation or driver-performance claims

## Hypothesis

A bounded source-only repair smoke can test whether the M2528 candidate config is executable against protected failure-surface gates while preserving the deployed actor contract and avoiding promotion or validation overclaims.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/summary.json, runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/candidate_config.json, runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/config_patch_audit.csv, runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/protected_gate_bindings.csv, runs/m2527_engineering_controller_failure_surface_intervention_plan/protected_regression_rows.csv, runs/m2527_engineering_controller_failure_surface_intervention_plan/implementation_gate_matrix.csv, docs/m2526-engineering-controller-failure-surface-intervention-design.md, runs/m2523_engineering_controller_source_only_fresh_seed_measured_behavior_panel/measured_behavior_rows.csv
- parent_config: experiments/manifests/m2528-engineering-controller-failure-surface-intervention-config-materialization-preflight.json
- parent_objective: run a bounded source-only repair smoke using the immutable M2528 candidate config before any promotion or broad validation
- derived_from: m2528-engineering-controller-failure-surface-intervention-config-materialization-preflight, m2527-engineering-controller-failure-surface-intervention-materialization-preflight, m2526-engineering-controller-failure-surface-intervention-design
- blocked_by: M2528 materialized a candidate config but no repair smoke behavior has been measured, M2527 protected gates have not been evaluated against a repaired candidate, Route A still lacks post-intervention source-only behavior evidence
- supersedes: another config-only milestone before repair smoke, checkpoint promotion before protected proof gates, ranking or success-rate interpretation from candidate config materialization
- invalidates: None

## Success Criteria

- runs/m2529_engineering_controller_failure_surface_intervention_repair_smoke/summary.json exists
- runs/m2529_engineering_controller_failure_surface_intervention_repair_smoke/repair_smoke_rows.csv exists
- runs/m2529_engineering_controller_failure_surface_intervention_repair_smoke/protected_gate_evaluation.csv exists
- runs/m2529_engineering_controller_failure_surface_intervention_repair_smoke/candidate_config_snapshot.json exists
- summary verifies P0 observation shape 72 and action shape 3 unchanged
- summary verifies hidden_or_oracle_actor_inputs_required false and active_config_overwritten false
- summary verifies external_high_fidelity_simulation_included false
- summary verifies ranking winner success_rate checkpoint_promoted validation and performance claims false
- protected gate evaluation rows trace to M2527/M2528 bindings

## Failure Criteria

- M2529 installs imports or runs Chrono or another external simulator
- M2529 changes actor input or action contract
- M2529 injects hidden or oracle actor features
- M2529 overwrites an active config or mutates M2528 candidate config in place
- M2529 promotes a checkpoint or selects a winner
- M2529 treats repair smoke as driver performance
- M2529 ranks controller families or computes success-rate verdict
- M2529 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2529 must use the immutable M2528 candidate config and M2527 protected gate bindings
- M2529 must preserve P0 observation shape 72 action shape 3 and no hidden/oracle actor input boundary
- M2529 may run bounded source-only repair smoke policy actions or short repair training only inside the pre-registered smoke scope
- M2529 must write summary.json repair_smoke_rows.csv protected_gate_evaluation.csv and candidate_config_snapshot.json
- M2529 must report negative or failed smoke results without tuning the candidate config in place
- M2529 must not install import or run external high-fidelity simulation
- M2529 must not rank controllers select winners promote checkpoints compute success rates or make paper self-ID finite-window-vs-GRU current-sim high-fidelity validation or driver-performance verdict claims

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
- do not overwrite active training configs
- do not mutate the M2528 candidate config in place
- do not promote a checkpoint
- do not rank controller families
- do not select a winner
- do not compute success rate or controller-family verdict metrics
- do not claim high-fidelity validation readiness
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim driver performance from repair smoke

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit

## Scoreboard

- milestone: m2529-engineering-controller-failure-surface-intervention-repair-smoke-preflight
- type: infrastructure
- checkpoint: runs/m2529_engineering_controller_failure_surface_intervention_repair_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: engineering_controller_failure_surface_intervention_repair_smoke_pass
- reason: M2529 runs bounded source-only no-update repair smoke from M2528 candidate config 45 repair smoke rows 7 protected gate evaluations 45 protected rows matched contract/no-oracle/no-ranking gates pass road-boundary mitigation command-conflict proof gates fail negative smoke recorded fresh generalization deferred no training ranking winner promotion success-rate verdict validation or driver-performance claims

## Next Blocker

m2530-engineering-controller-failure-surface-intervention-repair-smoke-result-audit
