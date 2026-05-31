# m1977-executable-v2-task-quality-calibrated-repaired-measured-outcome-localization-implementation-and-run Research Review

## Summary

- Generated at UTC: 20260531T120037Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: task_quality_calibrated_repaired_measured_outcome_localization_pass_route_to_result_audit
- Decision reason: M1977 implements and runs no-rerun calibrated repair-aware localization; exact outcome reproduction comparison-ready 0 candidate-support 1 L2 success 0 guardrail 0

## Hypothesis

A calibrated repair-aware no-rerun localizer can determine whether M1975 outcomes support comparison, repair, or scenario redesign.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_repaired_outcome_localization
- parent_dataset: docs/m1976-executable-v2-task-quality-calibrated-repaired-measured-execution-result-synthesis.md, runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/summary.json, runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/episode_rows.csv, runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/source_kind_aggregate.csv, runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/outcome_aggregate.csv
- parent_config: experiments/manifests/m1976-executable-v2-task-quality-calibrated-repaired-measured-execution-result-synthesis.json
- parent_objective: implement and run no-rerun outcome localization for the calibrated repaired M1975 measured artifacts
- derived_from: m1976-executable-v2-task-quality-calibrated-repaired-measured-execution-result-synthesis
- blocked_by: M1976 pivoted to calibrated repaired outcome localization because M1975 is complete but low-support/offtrack-dominated
- supersedes: direct controller ranking from low-support M1975 outcomes, blind reuse of the older M1942 localizer without calibrated repair schema mapping
- invalidates: None

## Success Criteria

- focused tests for calibrated repaired localization pass
- runs/m1977_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization/summary.json exists
- result_class is task_quality_calibrated_repaired_measured_outcome_localization_pass
- episode_count equals 960
- outcome_counts_match_source_summary is true
- required aggregate files are written
- guardrail_violation_count equals 0
- environment_reset_started environment_rollout_started policy_action_executed and measured_rollout_started are false
- controller ranking paper-level and level3 claims are false

## Failure Criteria

- localizer cannot parse M1975 schema
- outcome counts differ from M1975 summary
- required aggregate files are missing
- guardrail violation appears
- new reset rollout measured execution training replay PPO ranking or paper-level claims are made

## Evidence Gates

- M1977 must run only no-rerun CSV/JSON localization over M1975 artifacts
- M1977 must explicitly map parent_feasibility_tier_id and normalized_surface_variant instead of assuming old M1938 schema names
- M1977 must preserve repair_source_kind selection_quota_name and base_geometry_source dimensions
- M1977 must reproduce M1975 outcome counts exactly
- M1977 must keep ranking paper and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not execute policy actions
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

- milestone: m1977-executable-v2-task-quality-calibrated-repaired-measured-outcome-localization-implementation-and-run
- type: infrastructure
- checkpoint: runs/m1977_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: 0.0395833333
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_repaired_measured_outcome_localization_pass_route_to_result_audit
- reason: M1977 implements and runs no-rerun calibrated repair-aware localization; exact outcome reproduction comparison-ready 0 candidate-support 1 L2 success 0 guardrail 0

## Next Blocker

m1977-executable-v2-task-quality-calibrated-repaired-measured-outcome-localization-implementation-and-run
