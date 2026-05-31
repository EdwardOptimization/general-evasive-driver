# m1912-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution Research Review

## Summary

- Generated at UTC: 20260531T063230Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_repair_axis_measured_wrapper_execution_incomplete_route_to_failure_audit
- Decision reason: M1912 produces 768 measured rollout rows and 576 imports but fails target counts with 192 contained-collision feasibility sampling failures while guardrails remain clean

## Hypothesis

The fixed measured-wrapper command can execute the 960 rollout rows and merge 576 import/postprocess rows into a 1536-row public diagnostic panel with clean guardrails.

## Lineage

- parent_checkpoint: not_applicable_task_quality_repair_axis_measured_wrapper_execution
- parent_dataset: docs/m1911-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-cli-implementation.md, runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_matrix.csv, runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv, runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.json
- parent_config: experiments/manifests/m1911-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-cli-implementation.json
- parent_objective: run the fixed task-quality repair-axis measured-wrapper execution
- derived_from: m1911-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-cli-implementation
- blocked_by: M1911 must provide the measured CLI mode before real execution
- supersedes: manual or unregistered measured-wrapper execution
- invalidates: None

## Success Criteria

- runs/m1912_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution/summary.json exists
- summary result_class is task_quality_repair_axis_measured_wrapper_execution_pass
- measured_rollout_row_count is 960
- import_postprocess_row_count is 576
- combined_panel_row_count is 1536
- failure_count is 0
- guardrail_violation_count is 0
- controller-family ranking and paper claims remain blocked

## Failure Criteria

- summary is missing
- execution command diverges from M1910/M1911
- target counts fail
- guardrail violations occur
- interpretation or ranking is claimed before audit

## Evidence Gates

- M1912 must run the exact M1910/M1911 measured-wrapper command
- M1912 must produce 960 measured rollout rows, 576 import/postprocess rows, and 1536 combined panel rows
- M1912 must preserve all guardrails and claim boundaries
- M1912 must defer interpretation to a later result audit
- M1912 must keep controller-family ranking blocked

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

- milestone: m1912-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution
- type: gate
- checkpoint: runs/m1912_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_repair_axis_measured_wrapper_execution_incomplete_route_to_failure_audit
- reason: M1912 produces 768 measured rollout rows and 576 imports but fails target counts with 192 contained-collision feasibility sampling failures while guardrails remain clean

## Next Blocker

m1913-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-failure-audit
