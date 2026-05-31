# m1915-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-rerun Research Review

## Summary

- Generated at UTC: 20260531T064748Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_repair_axis_measured_wrapper_execution_rerun_pass_route_to_result_audit
- Decision reason: M1915 repaired rerun passes 960 measured rollout rows 576 imports 1536 combined panel rows failure 0 guardrail 0; interpretation deferred

## Hypothesis

After M1914, the repaired measured-wrapper command can execute all 960 rollout rows and merge 576 import/postprocess rows into a 1536-row panel with clean guardrails.

## Lineage

- parent_checkpoint: not_applicable_task_quality_repair_axis_measured_wrapper_execution_rerun
- parent_dataset: docs/m1914-executable-v2-support-first-task-quality-repair-axis-geometry-delta-mapping-repair.md, runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_matrix.csv, runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv, runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.json
- parent_config: experiments/manifests/m1914-executable-v2-support-first-task-quality-repair-axis-geometry-delta-mapping-repair.json
- parent_objective: rerun measured-wrapper execution after road_geometry_fixed obstacle-delta mapping repair
- derived_from: m1914-executable-v2-support-first-task-quality-repair-axis-geometry-delta-mapping-repair
- blocked_by: M1912 failed target counts before M1914 repair
- supersedes: interpreting partial M1912 rows
- invalidates: None

## Success Criteria

- runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/summary.json exists
- summary result_class is task_quality_repair_axis_measured_wrapper_execution_pass
- measured_rollout_row_count is 960
- import_postprocess_row_count is 576
- combined_panel_row_count is 1536
- failure_count is 0
- guardrail_violation_count is 0
- controller-family ranking and paper claims remain blocked

## Failure Criteria

- summary is missing
- execution command diverges from the repaired M1912 command
- target counts fail
- guardrail violations occur
- interpretation or ranking is claimed before audit

## Evidence Gates

- M1915 must run the repaired measured-wrapper command in a fresh output directory
- M1915 must use eval seed base 191200 to isolate the mapping repair
- M1915 must produce 960 measured rollout rows, 576 import/postprocess rows, and 1536 combined panel rows
- M1915 must preserve all guardrails and claim boundaries
- M1915 must defer interpretation to a later result audit
- M1915 must keep controller-family ranking blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

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

- milestone: m1915-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-rerun
- type: gate
- checkpoint: runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_repair_axis_measured_wrapper_execution_rerun_pass_route_to_result_audit
- reason: M1915 repaired rerun passes 960 measured rollout rows 576 imports 1536 combined panel rows failure 0 guardrail 0; interpretation deferred

## Next Blocker

m1915-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-rerun
