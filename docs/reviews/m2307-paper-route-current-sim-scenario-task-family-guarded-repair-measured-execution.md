# m2307-paper-route-current-sim-scenario-task-family-guarded-repair-measured-execution Research Review

## Summary

- Generated at UTC: 20260601T221444Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: current_sim_scenario_task_family_measured_execution_pass
- Decision reason: M2307 measured execution pass 1080/1080 failure 0 global success/offtrack/collision 68/786/218 guardrail 0 no ranking claims

## Hypothesis

The M2304 guarded-v2 selected checkpoints can be evaluated over the 72-spec scenario-task-family panel without metadata, metric, or claim-boundary violations.

## Lineage

- parent_checkpoint: runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/selected_checkpoint_rows.csv
- parent_dataset: docs/m2306-paper-route-current-sim-scenario-task-family-guarded-repair-selected-checkpoint-measured-execution-design.md, configs/paper_route_current_sim_scenario_task_family_v0.json, runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/selected_checkpoint_rows.csv, runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/configs, runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/summary.json
- parent_config: experiments/manifests/m2306-paper-route-current-sim-scenario-task-family-guarded-repair-selected-checkpoint-measured-execution-design.json
- parent_objective: run measured execution over 72 scenario specs and 15 M2304 selected checkpoints
- derived_from: m2306-paper-route-current-sim-scenario-task-family-guarded-repair-selected-checkpoint-measured-execution-design
- blocked_by: M2306 freezes the 1080-episode measured execution command and claim boundary
- supersedes: direct ranking over M2304 selected checkpoints, manual measured execution without a frozen panel
- invalidates: None

## Success Criteria

- runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/summary.json exists
- episode_count equals 1080
- scenario_spec_count equals 72
- selected_checkpoint_count equals 15
- failure_count equals 0
- metadata_missing_count equals 0
- metric_completeness_failure_count equals 0
- guardrail_violation_count equals 0
- controller_family_ranking_claim_made is false
- winner_selected is false
- paper_level_claim_made is false
- finite_window_vs_gru_conclusion_made is false
- level3_self_id_claim_made is false

## Failure Criteria

- M2307 validation fails before execution
- episode_count is not 1080
- metadata or metric completeness fails
- M2307 changes actor inputs, scenario specs, profile configs, or selected checkpoint rows
- M2307 ranks profiles, selects a winner, promotes a checkpoint, or claims paper/self-ID evidence

## Evidence Gates

- M2307 must run only the frozen M2306 command
- M2307 must use configs/paper_route_current_sim_scenario_task_family_v0.json
- M2307 must use M2304 selected_checkpoint_rows.csv and config root
- M2307 must target 1080 episodes, 72 scenario specs, and 15 selected checkpoints
- M2307 must not rank controller families, select a winner, promote a checkpoint, or claim paper/self-ID evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not change actor inputs
- do not change profile configs
- do not change scenario specs
- do not change selected checkpoint rows
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- training_instability
- metric_artifact
- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m2307-paper-route-current-sim-scenario-task-family-guarded-repair-measured-execution
- type: infrastructure
- checkpoint: runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/summary.json
- success_rate: 0.06296296296296296
- termination_rate: None
- clearance_margin_mean: 6.461206859204371
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_scenario_task_family_measured_execution_pass
- reason: M2307 measured execution pass 1080/1080 failure 0 global success/offtrack/collision 68/786/218 guardrail 0 no ranking claims

## Next Blocker

m2308-paper-route-current-sim-scenario-task-family-guarded-repair-measured-execution-result-audit
