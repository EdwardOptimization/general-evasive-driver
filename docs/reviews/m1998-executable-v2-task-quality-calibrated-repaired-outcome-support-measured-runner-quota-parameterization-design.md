# m1998-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-runner-quota-parameterization-design Research Review

## Summary

- Generated at UTC: 20260531T133800Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_outcome_support_measured_runner_quota_parameterization_design_route_to_required_branch_synthesis
- Decision reason: M1998 designs artifact-driven measured-runner quota expectations from active workload rows and routes to required branch synthesis before focused implementation

## Hypothesis

The calibrated measured runner should use artifact-driven expected source-kind and role-surface counts from the active workload or executable specs instead of stale historical constants.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_repaired_outcome_support_measured_runner_quota_parameterization_design
- parent_dataset: docs/m1997-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-rerun-result-audit.md, runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/planned_workload.csv, src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py
- parent_config: experiments/manifests/m1997-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-rerun-result-audit.json
- parent_objective: design artifact-driven quota expectations for calibrated measured runner before measured execution
- derived_from: m1997-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-rerun-result-audit
- blocked_by: calibrated measured runner still hard-codes older source-kind and role-surface quotas that do not match M1986 workload
- supersedes: direct measured execution command design with known stale measured-runner quota expectations
- invalidates: None

## Success Criteria

- docs/m1998-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-runner-quota-parameterization-design.md exists
- expected quota source is specified
- fail-closed behavior is specified
- focused implementation tests are specified
- next route is explicit
- no measured execution ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- expected quota source is ambiguous
- design disables quota checks silently
- next route is ambiguous
- measured execution ranking or paper-level claims are made

## Evidence Gates

- M1998 must design measured-runner quota repair before code changes
- M1998 must not run measured execution
- M1998 must preserve fail-closed behavior for missing or inconsistent expected distributions
- M1998 must keep controller ranking paper and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not edit code in M1998
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

- metric_artifact

## Scoreboard

- milestone: m1998-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-runner-quota-parameterization-design
- type: gate
- checkpoint: docs/m1998-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-runner-quota-parameterization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_outcome_support_measured_runner_quota_parameterization_design_route_to_required_branch_synthesis
- reason: M1998 designs artifact-driven measured-runner quota expectations from active workload rows and routes to required branch synthesis before focused implementation

## Next Blocker

m1998-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-runner-quota-parameterization-design
