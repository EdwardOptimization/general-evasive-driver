# m2375-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-plan-materialization Research Review

## Summary

- Generated at UTC: 20260602T061130Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: offtrack_guardrail_repair_plan_materialization_pass_route_to_result_audit
- Decision reason: M2375 materializes repair-plan artifacts reward 54 curriculum 54 guardrail 284 mixed 18 exclusions 0 guardrail 0 no repair execution/training claims

## Hypothesis

Artifact-only materialization can turn audited repair specs into repair-plan artifacts without executing repair, ranking, or claiming training success.

## Lineage

- parent_checkpoint: not_applicable_artifact_only_repair_plan_materialization
- parent_dataset: docs/m2374-paper-route-current-sim-dual-axis-outcome-localization-branch-synthesis.md, docs/m2373-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-implementation-design.md, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/repair_spec_rows.csv, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/ordinary_offtrack_repair_spec_rows.csv, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/mixed_guarded_repair_spec_rows.csv, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/collision_guardrail_spec_rows.csv, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/r4_guardrail_spec_rows.csv, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/diagnostic_guardrail_spec_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2374-paper-route-current-sim-dual-axis-outcome-localization-branch-synthesis.json
- parent_objective: materialize artifact-only repair-plan artifacts from M2373 design and M2371 specs
- derived_from: m2374-paper-route-current-sim-dual-axis-outcome-localization-branch-synthesis, m2373-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-implementation-design, m2371-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-materialization
- blocked_by: M2374 continues to repair-plan materialization but no repair-plan artifact exists, repair execution remains blocked until artifact-only repair-plan materialization and audit pass
- supersedes: direct repair execution after branch synthesis, training or scenario redesign execution before repair-plan artifact audit
- invalidates: None

## Success Criteria

- runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/summary.json exists
- input_repair_spec_row_count equals 320
- ordinary_offtrack_source_count equals 36
- mixed_guarded_source_count equals 18
- collision_guardrail_source_count equals 28
- r4_guardrail_source_count equals 48
- diagnostic_guardrail_source_count equals 190
- reward_delta_row_count is greater than 0
- curriculum_weight_row_count is greater than 0
- guardrail_constraint_row_count is at least 266
- profile_specific_tuning_count actor_input_change_count hidden_oracle_feature_injection_count collision_blind_mixed_repair_count r4_ordinary_repair_count ranking_admissible_count winner_selected_count are 0
- active_config_overwritten environment_rollout_started policy_action_executed training_started replay_started ppo_used are false
- paper-level finite-window-vs-GRU level3 self-ID scenario-redesign-executed training-repair-success and current-sim verdict claims are false

## Failure Criteria

- summary is missing
- source counts differ from M2371
- any required output family is missing
- guardrail constraints are missing
- repair-plan artifacts include actor input changes hidden/oracle features profile-specific tuning ranking or winner selection
- any forbidden execution or claim flag is set
- result audit route is missing

## Evidence Gates

- M2375 must materialize repair-plan artifacts from M2371 repair specs and M2373 design
- M2375 must preserve collision, R4, diagnostic, and mixed guarded constraints
- M2375 must not run reset rollout measured execution repair execution training replay PPO private holdout ranking or paper/self-ID claims

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
- lineage_invalid
- contract_violation
- objective_overfit
- behavior_regression

## Scoreboard

- milestone: m2375-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-plan-materialization
- type: infrastructure
- checkpoint: runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: offtrack_guardrail_repair_plan_materialization_pass_route_to_result_audit
- reason: M2375 materializes repair-plan artifacts reward 54 curriculum 54 guardrail 284 mixed 18 exclusions 0 guardrail 0 no repair execution/training claims

## Next Blocker

m2376-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-plan-materialization-result-audit
