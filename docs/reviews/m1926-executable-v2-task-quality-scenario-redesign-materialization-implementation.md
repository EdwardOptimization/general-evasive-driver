# m1926-executable-v2-task-quality-scenario-redesign-materialization-implementation Research Review

## Summary

- Generated at UTC: 20260531T074046Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: task_quality_scenario_materialization_selector_pass_route_to_command_design
- Decision reason: M1926 creates an 80-source balanced non-holdout source subset with 960 expected workload cells and no reset rollout ranking or paper claims

## Hypothesis

The M1925 deterministic selector can create an 80-source balanced non-holdout subset from M1924 supported sources.

## Lineage

- parent_checkpoint: not_applicable_task_quality_scenario_redesign_materialization_implementation
- parent_dataset: docs/m1925-executable-v2-task-quality-scenario-redesign-materialization-design.md, runs/m1924_executable_v2_task_quality_scenario_redesign_source_mining_result_audit/joined_source_support.csv
- parent_config: experiments/manifests/m1925-executable-v2-task-quality-scenario-redesign-materialization-design.json
- parent_objective: implement deterministic bounded non-holdout source selector and emit source-only materialization subset
- derived_from: m1925-executable-v2-task-quality-scenario-redesign-materialization-design
- blocked_by: M1925 defines the panel design but no selector or subset artifact exists
- supersedes: manual source selection from the 399 supported source pool
- invalidates: None

## Success Criteria

- configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json exists
- runs/m1926_executable_v2_task_quality_scenario_redesign_materialization_implementation/summary.json exists
- selected_source_count is 80
- selected_source_count_per_tier_role is 4 for all 20 tier-role cells
- surface balance is 2 steady and 2 post-friction for every tier-role cell
- paper_holdout_selected_count is 0
- labels_enter_actor_input_count is 0
- ranking_admissible_by_default_count is 0
- expected_planned_workload_cell_count is 960
- focused tests pass
- no reset rollout measured execution training replay PPO ranking or paper-level claim is made

## Failure Criteria

- subset artifact is missing
- summary is missing
- selection counts fail
- holdout rows are selected
- actor-input or ranking guardrails fail
- reset rollout measured execution training replay or PPO is run
- controller ranking or paper-level claims are made

## Evidence Gates

- M1926 must select exactly 80 supported non-holdout sources
- M1926 must select exactly 4 sources for every feasibility-tier and role cell
- M1926 must select exactly 2 steady and 2 post-friction sources for every tier-role cell
- M1926 must write a source-only subset artifact and summary without reset rollout measured execution or ranking
- M1926 must keep controller-family ranking paper claims and level3 self-ID blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1926-executable-v2-task-quality-scenario-redesign-materialization-implementation
- type: infrastructure
- checkpoint: configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_scenario_materialization_selector_pass_route_to_command_design
- reason: M1926 creates an 80-source balanced non-holdout source subset with 960 expected workload cells and no reset rollout ranking or paper claims

## Next Blocker

m1926-executable-v2-task-quality-scenario-redesign-materialization-implementation
