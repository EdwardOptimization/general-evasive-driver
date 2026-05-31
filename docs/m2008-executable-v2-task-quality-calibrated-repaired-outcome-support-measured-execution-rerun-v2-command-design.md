# M2008 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Measured Execution Rerun V2 Command Design

- status: completed
- decision: `task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_v2_command_design_admit_execution`
- executable specs: `runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.json`
- planned workload: `runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/planned_workload.csv`
- measured execution in M2008: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M2009 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_measured_runner \
  --executable-task-specs runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.json \
  --workload runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/planned_workload.csv \
  --output-dir runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat \
  --eval-seed-base 200900 \
  --device cpu \
  --target-episode-count 960 \
  --target-spec-count 80 \
  --target-profile-count 12 \
  --next-blocker m2010-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-execution-rerun-v2-result-audit
```

M2008 does not run this command. It freezes it for M2009.

## Expected Artifacts

M2009 must write the same measured-runner artifact set as M2003, but in the
fresh output directory:

```text
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/summary.json
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/episode_rows.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/failure_rows.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/validation_failure_rows.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/metric_completeness_failures.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/quota_metadata_missing_rows.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/profile_aggregate.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/source_kind_aggregate.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/role_aggregate.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/normalized_surface_aggregate.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/role_surface_aggregate.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/sampled_label_aggregate.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/outcome_aggregate.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/termination_reason_aggregate.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/claim_boundary.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/run_state.json
```

## Pass Gates

M2009 passes only if:

```text
result_class == task_quality_calibrated_measured_execution_pass
episode_count == 960
target_episode_count == 960
failure_count == 0
spec_count == 80
profile_count == 12
expected_quota_source == workload
quota_metadata_missing_count == 0
source_kind_quota_pass == true
role_surface_quota_pass == true
metric_completeness_failure_count == 0
guardrail_violation_count == 0
environment_rollout_started == true
policy_action_executed == true
measured_rollout_started == true
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If any row fails, M2009 must preserve failure artifacts and route to result
audit. It must not repair and rerun inside the same milestone.

## Claim Boundary

If M2009 passes, it may claim only measured execution completion for the
repaired outcome-support workload. Controller-family ranking, paper-level
benchmark evidence, policy improvement, finite-window vs GRU conclusions, and
level3 self-identification remain blocked until later audits and comparison
design.

## Next

Next milestone:

```text
m2009-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-execution-rerun-v2
```

M2009 may run only the frozen measured execution command.
