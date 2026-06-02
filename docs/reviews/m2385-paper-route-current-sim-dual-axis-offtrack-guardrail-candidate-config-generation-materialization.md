# m2385-paper-route-current-sim-dual-axis-offtrack-guardrail-candidate-config-generation-materialization Research Review

## Summary

- Generated at UTC: 20260602T073540Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: candidate_config_generation_pass_route_to_branch_synthesis
- Decision reason: M2385 materializes 54 run-dir-only candidate config files refs 162/54/284 mixed 18 outside-run-dir 0 guardrail 0 no active overwrite reset repair training or ranking claims

## Hypothesis

Artifact-only materialization can generate candidate config files under the run directory from application-plan artifacts without active config overwrite, reset validation, repair execution, ranking, or training-success claims.

## Lineage

- parent_checkpoint: not_applicable_candidate_config_generation_materialization
- parent_dataset: docs/m2384-paper-route-current-sim-dual-axis-offtrack-guardrail-candidate-config-generation-design.md, runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/summary.json, runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/application_plan_manifest.json, runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/candidate_application_specs.csv, runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/reward_patch_application_refs.csv, runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/curriculum_patch_application_refs.csv, runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/guardrail_patch_application_refs.csv, runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/mixed_guarded_candidate_requirements.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2384-paper-route-current-sim-dual-axis-offtrack-guardrail-candidate-config-generation-design.json
- parent_objective: materialize run-dir-only candidate config artifacts from M2384 design and M2382 application-plan artifacts
- derived_from: m2384-paper-route-current-sim-dual-axis-offtrack-guardrail-candidate-config-generation-design, m2383-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-application-plan-materialization-result-audit, m2382-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-application-plan-materialization
- blocked_by: M2384 designs candidate config generation but does not materialize generated files, reset validation and repair execution remain blocked until candidate config generation is materialized and synthesized
- supersedes: direct reset validation from application-plan artifacts, direct active config overwrite from candidate generation design
- invalidates: None

## Success Criteria

- runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/summary.json exists
- source_candidate_application_spec_count equals 54
- candidate_config_file_written_count equals 54
- candidate_config_files_outside_run_dir_count equals 0
- source_reward_patch_reference_count equals 162
- source_curriculum_patch_reference_count equals 54
- source_guardrail_patch_reference_count equals 284
- mixed_guarded_candidate_requirement_count equals 18
- candidate_without_reward_overlay_count candidate_without_curriculum_overlay_count candidate_without_guardrail_overlay_count are 0
- active_config_overwritten is false and active_config_patch_application_count is 0
- actor_input_change_count hidden_oracle_feature_injection_count profile_specific_tuning_count ranking_admissible_count winner_selected_count are 0
- environment_rollout_started policy_action_executed repair_execution_started training_started replay_started ppo_used are false
- paper-level finite-window-vs-GRU level3 self-ID scenario-redesign-executed training-repair-success and current-sim verdict claims are false

## Failure Criteria

- summary is missing
- source counts differ from M2382
- candidate config file count differs from 54
- candidate config files are written outside the run directory
- active config overwrite occurs
- any forbidden execution or claim flag is set
- M2386 branch synthesis route is missing

## Evidence Gates

- M2385 must materialize candidate config files under its run directory only
- M2385 must preserve active-config overwrite, actor-input, oracle-feature, profile-tuning, collision, R4, diagnostic, and mixed guarded constraints
- M2385 must not run reset rollout measured execution repair execution training replay PPO private holdout ranking or paper/self-ID/current-sim verdict claims

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
- do not write candidate config files outside the M2385 run directory
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim scenario redesign executed
- do not claim training repair success
- do not claim current-sim verdict

## Failure Taxonomy

- metric_artifact
- lineage_invalid
- contract_violation
- objective_overfit
- behavior_regression

## Scoreboard

- milestone: m2385-paper-route-current-sim-dual-axis-offtrack-guardrail-candidate-config-generation-materialization
- type: infrastructure
- checkpoint: runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_config_generation_pass_route_to_branch_synthesis
- reason: M2385 materializes 54 run-dir-only candidate config files refs 162/54/284 mixed 18 outside-run-dir 0 guardrail 0 no active overwrite reset repair training or ranking claims

## Next Blocker

m2386-paper-route-current-sim-dual-axis-candidate-config-generation-branch-synthesis
