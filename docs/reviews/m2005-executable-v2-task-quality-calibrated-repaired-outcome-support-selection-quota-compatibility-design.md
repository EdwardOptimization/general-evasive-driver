# m2005-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-design Research Review

## Summary

- Generated at UTC: 20260531T140156Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_selection_quota_compatibility_design_admit_focused_implementation
- Decision reason: M2005 designs selection_quota_name fallback to repair_axis with missing provenance fail-closed and admits focused implementation

## Hypothesis

The measured runner can safely accept repair_axis as the newer provenance field when selection_quota_name is absent, while still failing closed when both are missing.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_repaired_outcome_support_selection_quota_compatibility_design
- parent_dataset: docs/m2004-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-execution-rerun-result-audit.md, src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py, runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.json, runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/planned_workload.csv
- parent_config: experiments/manifests/m2004-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-execution-rerun-result-audit.json
- parent_objective: design measured-runner compatibility for selection_quota_name versus repair_axis provenance
- derived_from: m2004-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-execution-rerun-result-audit
- blocked_by: M2003 failed closed because M1986 artifacts carry repair_axis but not selection_quota_name
- supersedes: rerunning measured execution without repairing selection_quota_name compatibility
- invalidates: None

## Success Criteria

- docs/m2005-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-design.md exists
- compatibility source is specified
- fail-closed behavior is specified
- focused tests are specified
- next route is explicit
- no code measured execution ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- compatibility source is ambiguous
- design silently allows missing provenance
- next route is ambiguous
- code measured execution ranking or paper-level claims are made

## Evidence Gates

- M2005 must design selection_quota_name compatibility without code edits
- M2005 must preserve fail-closed behavior when both selection_quota_name and repair_axis are missing
- M2005 must not run measured execution
- M2005 must keep ranking paper and self-ID claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not edit code
- do not run real measured execution
- do not run environment rollout
- do not execute policy actions
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

- metric_artifact

## Scoreboard

- milestone: m2005-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-design
- type: gate
- checkpoint: docs/m2005-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_selection_quota_compatibility_design_admit_focused_implementation
- reason: M2005 designs selection_quota_name fallback to repair_axis with missing provenance fail-closed and admits focused implementation

## Next Blocker

m2005-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-design
