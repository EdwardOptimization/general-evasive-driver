# m2391-paper-route-current-sim-dual-axis-effective-config-schema-repair-materialization Research Review

## Summary

- Generated at UTC: 20260602T083857Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: effective_candidate_pack_materialization_pass_route_to_branch_synthesis
- Decision reason: M2391 materializes 54/54 effective candidates selected scenario refs 2049 unmatched/env_config missing 0/0 env load/reset 0 guardrail 0 no repair/training/ranking claims

## Hypothesis

Artifact-only materialization can join 54 M2385 candidate overlays to M2356 reset-valid base pack scenario specs and emit run-dir effective candidate pack artifacts without environment load/reset, active config overwrite, repair execution, ranking, or training-success claims.

## Lineage

- parent_checkpoint: not_applicable_effective_config_schema_repair_materialization
- parent_dataset: docs/m2390-paper-route-current-sim-dual-axis-effective-config-schema-repair-design.md, runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/summary.json, runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_config_rows.csv, runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_configs, runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_config_pack_manifest.json, runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/baseline_reference_pack.json, runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/g_primary_pack.json, runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/h_primary_pack.json, runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/g_h_primary_pack.json, runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/gh_minimal_pack.json, runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/summary.json, runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/summary.json, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2390-paper-route-current-sim-dual-axis-effective-config-schema-repair-design.json
- parent_objective: materialize run-dir-only effective candidate pack artifacts by joining M2385 candidate overlays to M2356 reset-valid base pack scenario specs
- derived_from: m2390-paper-route-current-sim-dual-axis-effective-config-schema-repair-design, m2389-paper-route-current-sim-dual-axis-candidate-config-reset-validation-result-audit, m2385-paper-route-current-sim-dual-axis-offtrack-guardrail-candidate-config-generation-materialization, m2359-paper-route-current-sim-dual-axis-repaired-pack-reset-validation-implementation, m2356-paper-route-current-sim-dual-axis-candidate-pack-sampling-repair-materialization-implementation
- blocked_by: M2390 designs effective candidate pack schema but does not materialize artifacts, M2388 reset validation remains blocked until candidate overlays are joined with reset-valid base scenario specs
- supersedes: direct reset validation from overlay-only candidate configs, direct active config overwrite from candidate overlays, forcing one standalone env_config into each overlay candidate
- invalidates: None

## Success Criteria

- runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/summary.json exists
- source_candidate_config_count equals 54
- static_validation_pass_count equals 54
- effective_candidate_config_written_count equals 54
- effective_candidate_config_outside_run_dir_count equals 0
- candidate_without_matching_scenarios_count equals 0
- candidate_without_env_config_count equals 0
- base_pack_count equals 5
- base_scenario_specs_per_pack_count equals 72
- selected_scenario_reference_count is greater than 0
- active_config_overwrite_count environment_load_attempt_count environment_reset_attempt_count environment_step_count are 0
- actor_input_contract_changed hidden_oracle_feature_injection profile_specific_tuning are false
- policy_action_executed environment_rollout_started repair_execution_started training_started replay_started ppo_used are false
- ranking_admissible_count winner_selected_count guardrail_violation_count are 0
- paper-level finite-window-vs-GRU level3 self-ID scenario-redesign-executed training-repair-success and current-sim verdict claims are false

## Failure Criteria

- summary is missing
- source candidate count differs from 54
- any candidate has no matching scenario specs
- any selected scenario lacks env_config
- any effective candidate config path escapes the M2391 run directory
- active config overwrite occurs
- environment load reset step rollout policy action repair training replay PPO ranking or winner selection occurs
- any forbidden claim flag is set
- M2392 result audit route is missing

## Evidence Gates

- M2391 must materialize effective candidate pack artifacts under its run directory only
- M2391 must join M2385 overlays to M2356 reset-valid base scenario specs by source_slice_axis/source_slice_value matching
- M2391 must preserve P0 human-view no-wheel no-oracle actor contract guardrails from selected base env_config entries
- M2391 must fail closed if any candidate has no matching scenario specs or missing env_config
- M2391 must not load or reset an environment, step a policy, execute repair, train, rank, or make paper/self-ID/current-sim claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not load an environment
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not execute repair levers
- do not apply overlays to the active config
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
- do not write effective candidate configs outside the M2391 run directory
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim scenario redesign executed
- do not claim training repair success
- do not claim current-sim verdict

## Failure Taxonomy

- scenario_sampling_failure
- lineage_invalid
- contract_violation
- metric_artifact
- behavior_regression

## Scoreboard

- milestone: m2391-paper-route-current-sim-dual-axis-effective-config-schema-repair-materialization
- type: infrastructure
- checkpoint: runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: effective_candidate_pack_materialization_pass_route_to_branch_synthesis
- reason: M2391 materializes 54/54 effective candidates selected scenario refs 2049 unmatched/env_config missing 0/0 env load/reset 0 guardrail 0 no repair/training/ranking claims

## Next Blocker

m2392-paper-route-current-sim-dual-axis-effective-config-materialization-branch-synthesis
