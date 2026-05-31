# M2002 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Measured Execution Rerun Command Design

- status: completed
- decision: `task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_command_design_admit_execution`
- executable specs: `runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.json`
- planned workload: `runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/planned_workload.csv`
- measured execution in M2002: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M2003 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_measured_runner \
  --executable-task-specs runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.json \
  --workload runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/planned_workload.csv \
  --output-dir runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun \
  --eval-seed-base 200300 \
  --device cpu \
  --target-episode-count 960 \
  --target-spec-count 80 \
  --target-profile-count 12 \
  --next-blocker m2004-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-execution-rerun-result-audit
```

M2002 does not run this command. It freezes it for M2003.

## Expected Workload Distribution

The active M1986 workload has:

```text
episode rows: 960
task specs: 80
controller profiles: 12
```

Expected source-kind counts:

```text
anchor_neighborhood: 288
mitigation_isolation_check: 240
offtrack_boundary_relief: 192
success_stabilizer: 240
```

Expected role-surface counts:

```text
anchor_neighborhood|stable_aeb|post_friction_step: 288
mitigation_isolation_check|drift_required_recovery|steady_surface: 12
mitigation_isolation_check|unavoidable_mitigation|steady_surface: 228
offtrack_boundary_relief|stable_aes_only|relief_surface_unspecified: 192
success_stabilizer|drift_required_recovery|post_friction_step: 36
success_stabilizer|drift_required_recovery|steady_surface: 24
success_stabilizer|stable_aeb|post_friction_step: 72
success_stabilizer|stable_aeb|steady_surface: 24
success_stabilizer|stable_aes_only|post_friction_step: 60
success_stabilizer|unavoidable_mitigation|post_friction_step: 24
```

These are expected to be computed by the repaired measured runner from the
active workload. They are not hard-coded into the command.

## Expected Artifacts

M2003 must write:

```text
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/summary.json
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/episode_rows.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/failure_rows.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/validation_failure_rows.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/metric_completeness_failures.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/quota_metadata_missing_rows.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/profile_aggregate.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/source_kind_aggregate.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/role_aggregate.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/normalized_surface_aggregate.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/role_surface_aggregate.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/sampled_label_aggregate.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/outcome_aggregate.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/termination_reason_aggregate.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/claim_boundary.csv
runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/run_state.json
```

## Pass Gates

M2003 passes only if:

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

If any row fails, M2003 must preserve failure artifacts and route to result
audit. It must not repair and rerun inside the same milestone.

## Claim Boundary

If M2003 passes, it may claim only:

```text
the repaired outcome-support 960-cell measured execution completed with
metadata-preserving episode rows and workload-derived quota gates.
```

It still cannot claim controller-family ranking, paper-level benchmark evidence,
policy improvement, finite-window vs GRU conclusion, or level3
self-identification.

## Next

Next milestone:

```text
m2003-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-execution-rerun
```

M2003 may run only the frozen measured execution command.
