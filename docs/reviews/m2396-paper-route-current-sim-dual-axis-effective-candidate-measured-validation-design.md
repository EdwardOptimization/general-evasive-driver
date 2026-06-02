# m2396-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-design Research Review

## Summary

- Generated at UTC: 20260602T091655Z
- Type: gate
- Gate tier: process
- Promotion decision: effective_candidate_measured_validation_design_admit_implementation
- Decision reason: M2396 freezes 30735-episode effective-candidate measured-validation design no rollout/ranking claims

## Hypothesis

A bounded measured-validation design can evaluate M2394 reset-ready effective candidate artifacts while preserving the paper-route claim boundary, actor contract, and no-ranking discipline.

## Lineage

- parent_checkpoint: not_applicable_effective_candidate_measured_validation_design
- parent_dataset: docs/m2395-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-result-audit.md, docs/m2394-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-implementation.md, runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/summary.json, runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/static_validation_rows.csv, runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/reset_target_rows.csv, runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/reset_validation_rows.csv, runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/effective_candidate_reset_summary_rows.csv, runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_config_rows.csv, runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_scenario_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2395-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-result-audit.json
- parent_objective: design bounded measured validation over reset-ready effective candidate artifacts
- derived_from: m2395-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-result-audit, m2394-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-implementation, m2391-paper-route-current-sim-dual-axis-effective-config-schema-repair-materialization
- blocked_by: M2395 accepts reset-readiness but closed-loop measured validation protocol is not frozen, repair execution, training, ranking, and paper/current-sim verdicts require measured rollout evidence
- supersedes: direct measured execution without a frozen denominator and claim boundary, ranking effective candidates from reset-only evidence, interpreting reset validation as scenario redesign success
- invalidates: None

## Success Criteria

- docs/m2396-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-design.md exists
- input artifacts and fixed denominator are specified
- duplicate policy for candidate-scenario references and measured episodes is specified
- controller/checkpoint source and seed rule are specified without profile-specific tuning
- role metrics and failure semantics are specified
- ranking, winner selection, paper-level, finite-window-vs-GRU, current-sim verdict, and level3 self-ID claims remain blocked
- a bounded non-ranking follow-up route is selected or the branch is stopped

## Failure Criteria

- M2396 runs reset, rollout, measured execution, replay, PPO, or private holdout
- M2396 executes repair levers or trains
- M2396 ranks support policies or controller families
- M2396 makes paper-level finite-window-vs-GRU current-sim verdict or level3 self-ID claims
- M2396 claims scenario redesign executed or training repair success
- M2396 cannot define denominator, duplicate policy, or metric semantics

## Evidence Gates

- M2396 must design measured validation over M2394 reset-ready effective candidates without running rollout
- M2396 must freeze denominator, artifact inputs, controller/checkpoint source, duplicate policy, metrics, and guardrails before execution
- M2396 must distinguish candidate-scenario references from unique reset targets and measured episodes
- M2396 must keep repair execution, training, ranking, winner selection, paper finite-window-vs-GRU, current-sim verdict, and level3 self-ID claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not execute repair levers
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not inject hidden or oracle features
- do not tune controller profiles
- do not rank support policies or controller families
- do not select a winner
- do not overwrite the active scenario config
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim scenario redesign executed
- do not claim training repair success
- do not claim current-sim verdict

## Failure Taxonomy

- metric_artifact
- contract_violation
- scenario_sampling_failure
- lineage_invalid
- behavior_regression

## Scoreboard

- milestone: m2396-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-design
- type: gate
- checkpoint: docs/m2396-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: effective_candidate_measured_validation_design_admit_implementation
- reason: M2396 freezes 30735-episode effective-candidate measured-validation design no rollout/ranking claims

## Next Blocker

m2397-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-implementation
