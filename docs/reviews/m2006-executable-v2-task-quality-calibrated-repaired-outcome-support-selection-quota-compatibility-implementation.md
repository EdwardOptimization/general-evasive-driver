# m2006-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-implementation Research Review

## Summary

- Generated at UTC: 20260531T140530Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: task_quality_calibrated_selection_quota_compatibility_implementation_pass_route_to_audit
- Decision reason: M2006 implements selection_quota_name fallback to repair_axis missing provenance fail-closed behavior and focused tests pass 6 no real measured execution

## Hypothesis

Runner-side selection_quota_name fallback to repair_axis can validate M1986-style artifacts without accepting missing repair provenance.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_repaired_outcome_support_selection_quota_compatibility_implementation
- parent_dataset: docs/m2005-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-design.md, src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py, tests/test_executable_v2_task_quality_calibrated_measured_runner.py
- parent_config: experiments/manifests/m2005-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-design.json
- parent_objective: implement measured-runner selection_quota_name compatibility with repair_axis fallback
- derived_from: m2005-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-design
- blocked_by: M2003 failed closed because M1986 artifacts have repair_axis but not selection_quota_name
- supersedes: rerunning M2003 without selection quota compatibility
- invalidates: None

## Success Criteria

- runner materializes selection_quota_name from repair_axis when missing
- runner preserves repair_axis in outputs
- runner fails closed when both selection_quota_name and repair_axis are missing
- focused tests pass
- no real measured execution is performed

## Failure Criteria

- focused tests fail
- rows missing both provenance fields pass validation
- M1986-style rows still fail validation in focused tests
- real measured execution ranking or paper-level claims are made

## Evidence Gates

- M2006 must implement repair_axis fallback for missing selection_quota_name
- M2006 must fail closed when both provenance fields are missing
- M2006 must add focused tests
- M2006 must not run real measured execution

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run real measured execution
- do not run environment rollout except focused fake-rollout unit tests
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

- milestone: m2006-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-implementation
- type: infrastructure
- checkpoint: docs/m2006-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-implementation.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_selection_quota_compatibility_implementation_pass_route_to_audit
- reason: M2006 implements selection_quota_name fallback to repair_axis missing provenance fail-closed behavior and focused tests pass 6 no real measured execution

## Next Blocker

m2006-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-implementation
