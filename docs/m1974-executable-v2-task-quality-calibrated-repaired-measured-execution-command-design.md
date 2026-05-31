# M1974 Executable V2 Task-Quality Calibrated Repaired Measured Execution Command Design

- status: completed
- decision: `task_quality_calibrated_repaired_measured_execution_command_design_admit_execution`
- repaired executable specs: `runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json`
- repaired planned workload: `runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/planned_workload.csv`
- measured execution in M1974: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1975 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_measured_runner \
  --executable-task-specs runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json \
  --workload runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/planned_workload.csv \
  --output-dir runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired \
  --eval-seed-base 197500 \
  --device cpu \
  --target-episode-count 960 \
  --target-spec-count 80 \
  --target-profile-count 12 \
  --next-blocker m1976-executable-v2-task-quality-calibrated-repaired-measured-execution-result-synthesis
```

M1974 does not run this command. It freezes it for M1975.

## Expected Artifacts

M1975 must write:

```text
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/summary.json
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/episode_rows.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/failure_rows.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/validation_failure_rows.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/metric_completeness_failures.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/profile_aggregate.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/source_kind_aggregate.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/role_aggregate.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/normalized_surface_aggregate.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/role_surface_aggregate.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/sampled_label_aggregate.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/outcome_aggregate.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/termination_reason_aggregate.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/claim_boundary.csv
runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/run_state.json
```

## Pass Gates

M1975 passes only if:

```text
result_class == task_quality_calibrated_measured_execution_pass
episode_count == 960
target_episode_count == 960
failure_count == 0
spec_count == 80
profile_count == 12
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

If any row fails, M1975 must preserve failure artifacts and route to result
synthesis. It must not repair and rerun inside the same milestone.

## Claim Boundary

If M1975 passes, it may claim only:

```text
the repaired calibrated 960-cell public diagnostic measured execution completed
with metadata-preserving episode rows.
```

It still cannot claim controller-family ranking, paper-level benchmark evidence,
policy improvement, finite-window vs GRU conclusion, or level3
self-identification.

## Next

Next milestone:

```text
m1975-executable-v2-task-quality-calibrated-repaired-measured-execution
```

M1975 may run only the frozen measured execution command.
