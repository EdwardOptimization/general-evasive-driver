# m1904-executable-v2-support-first-task-quality-repair-axis-execution-design Research Review

## Summary

- Generated at UTC: 20260531T053711Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_repair_axis_execution_design_admit_wrapper_implementation
- Decision reason: M1904 designs wrapper protocol for M1902 axis matrix execution with 960 geometry rows and 576 import/postprocess rows while direct rollout and ranking remain blocked

## Hypothesis

A precise execution design can run only the M1902 geometry rows while importing/postprocessing the baseline and semantics rows into one auditable 1536-row panel.

## Lineage

- parent_checkpoint: not_applicable_task_quality_repair_axis_execution_design
- parent_dataset: docs/m1903-executable-v2-support-first-task-quality-repair-axis-materialization-result-audit.md, runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/summary.json, runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_matrix.csv, runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_spec.json, runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/role_surface_axis_target_map.csv
- parent_config: experiments/manifests/m1903-executable-v2-support-first-task-quality-repair-axis-materialization-result-audit.json
- parent_objective: design the execution wrapper/protocol for the M1902 repair-axis matrix before rollout
- derived_from: m1903-executable-v2-support-first-task-quality-repair-axis-materialization-result-audit
- blocked_by: M1902 has mixed rollout/import/postprocess row kinds that require an explicit execution protocol
- supersedes: direct use of the old repaired bounded-smoke runner on the M1902 matrix
- invalidates: None

## Success Criteria

- docs/m1904-executable-v2-support-first-task-quality-repair-axis-execution-design.md exists
- design specifies 960 rollout geometry rows and 576 import/postprocess rows
- design specifies required wrapper inputs outputs metadata preservation and pass gates
- next route is wrapper implementation or explicit helper repair/synthesis

## Failure Criteria

- design document is missing
- design admits direct execution or ranking without wrapper protocol
- design omits axis metadata or source provenance preservation
- design changes actor inputs or tunes controller profiles
- next route is ambiguous

## Evidence Gates

- M1904 must design the repair-axis execution wrapper without running rollout
- M1904 must preserve axis metadata and source provenance for rollout and import/postprocess rows
- M1904 must define pass gates for 960 geometry rollout rows plus 576 import/postprocess rows
- M1904 must keep controller ranking training PPO private holdout paper claims and level3 self-ID claims blocked

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

- milestone: m1904-executable-v2-support-first-task-quality-repair-axis-execution-design
- type: gate
- checkpoint: docs/m1904-executable-v2-support-first-task-quality-repair-axis-execution-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_repair_axis_execution_design_admit_wrapper_implementation
- reason: M1904 designs wrapper protocol for M1902 axis matrix execution with 960 geometry rows and 576 import/postprocess rows while direct rollout and ranking remain blocked

## Next Blocker

m1905-executable-v2-support-first-task-quality-repair-axis-wrapper-implementation
