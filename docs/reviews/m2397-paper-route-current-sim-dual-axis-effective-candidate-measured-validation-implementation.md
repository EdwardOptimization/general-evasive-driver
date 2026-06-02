# m2397-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-implementation Research Review

## Summary

- Generated at UTC: 20260602T115549Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: effective_candidate_measured_validation_pass_route_to_result_audit
- Decision reason: M2397 completes 30735/30735 measured episodes with failure/validation/metadata/metric/contract/guardrail 0; outcome offtrack-dominated offtrack_rate 0.8425898812428827 no ranking/verdict claims

## Hypothesis

The reset-ready effective candidate artifacts can be executed in a fixed 30735-episode measured-validation panel without lineage loss, actor-contract violation, metric artifacts, repair execution, training, ranking, or paper/self-ID/current-sim claims.

## Lineage

- parent_checkpoint: not_applicable_effective_candidate_measured_validation_runner
- parent_dataset: docs/m2396-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-design.md, docs/m2395-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-result-audit.md, runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_config_rows.csv, runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_scenario_rows.csv, runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_configs, runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/summary.json, runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/candidate_scenario_reset_rows.csv, runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv, runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2396-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-design.json
- parent_objective: implement and run bounded measured validation over 2049 reset-ready effective candidate scenario references and 15 selected checkpoints
- derived_from: m2396-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-design, m2395-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-result-audit, m2394-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-implementation
- blocked_by: M2396 designs the denominator but does not implement or run measured validation, closed-loop measured outcome evidence over effective candidates remains missing
- supersedes: reset-only validation as the final effective-candidate evidence, manual or profile-specific measured validation without fixed workload ids
- invalidates: None

## Success Criteria

- runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/summary.json exists
- source_candidate_count equals 54
- candidate_scenario_reference_count equals 2049
- selected_checkpoint_count equals 15
- target_episode_count equals 30735
- episode_count equals 30735
- failure_count validation_failure_count metadata_missing_count metric_completeness_failure_count actor_contract_violation_count guardrail_violation_count are 0
- ranking_admissible_count equals 0 and winner_selected is false
- repair execution training replay PPO paper finite-window-vs-GRU level3 self-ID scenario-redesign training-repair and current-sim verdict claims are false

## Failure Criteria

- summary is missing
- workload denominator differs from M2396 without fail-closed reporting
- candidate/pack/scenario/checkpoint lineage is missing from episode rows
- metrics are missing non-finite or mislabeled
- actor contract is violated
- repair execution training replay PPO ranking or winner selection occurs
- any forbidden paper/self-ID/current-sim claim flag is set
- result audit route is missing

## Evidence Gates

- M2397 must implement the measured-validation adapter from the M2396 design
- M2397 must run the fixed 30735-episode denominator unless it fails closed with validation/failure rows
- M2397 must preserve candidate_id pack_id scenario_spec_id and selected checkpoint lineage on every row
- M2397 must not execute repair, train, run replay/PPO, rank, select a winner, or make paper/self-ID/current-sim verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

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
- do not rank effective candidates
- do not select a winner
- do not overwrite the active scenario config
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim scenario redesign executed
- do not claim training repair success
- do not claim current-sim verdict

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- lineage_invalid
- contract_violation
- behavior_regression
- training_instability

## Scoreboard

- milestone: m2397-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-implementation
- type: infrastructure
- checkpoint: runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/summary.json
- success_rate: 0.04054010086220921
- termination_rate: None
- clearance_margin_mean: 8.497377506922128
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: effective_candidate_measured_validation_pass_route_to_result_audit
- reason: M2397 completes 30735/30735 measured episodes with failure/validation/metadata/metric/contract/guardrail 0; outcome offtrack-dominated offtrack_rate 0.8425898812428827 no ranking/verdict claims

## Next Blocker

m2398-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-result-audit
