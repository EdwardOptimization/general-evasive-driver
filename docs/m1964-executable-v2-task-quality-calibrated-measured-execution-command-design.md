# M1964 Executable V2 Task-Quality Calibrated Measured Execution Command Design

- status: completed
- decision: `task_quality_calibrated_measured_execution_command_design_admit_execution`
- branch: `paper_route_task_quality_calibrated_materialization`
- measured runner: `src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py`
- executable specs: `runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json`
- planned workload: `runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv`
- output dir: `runs/m1965_executable_v2_task_quality_calibrated_measured_execution`
- rollout/measured execution in M1964: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1965 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_measured_runner \
  --executable-task-specs runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json \
  --workload runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv \
  --output-dir runs/m1965_executable_v2_task_quality_calibrated_measured_execution \
  --eval-seed-base 196500 \
  --device cpu \
  --target-episode-count 960 \
  --target-spec-count 80 \
  --target-profile-count 12 \
  --next-blocker m1966-executable-v2-task-quality-calibrated-measured-execution-result-audit
```

M1964 does not run this command. It freezes it for M1965.

## Expected Artifacts

M1965 must write:

```text
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/summary.json
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/episode_rows.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/failure_rows.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/validation_failure_rows.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/metric_completeness_failures.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/profile_aggregate.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/source_kind_aggregate.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/role_aggregate.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/normalized_surface_aggregate.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/role_surface_aggregate.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/sampled_label_aggregate.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/outcome_aggregate.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/termination_reason_aggregate.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/claim_boundary.csv
runs/m1965_executable_v2_task_quality_calibrated_measured_execution/run_state.json
```

## Pass Gates

M1965 passes only if:

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

If any row fails, M1965 must preserve failure rows and route to result/failure
audit. It must not repair and rerun inside the same milestone.

## Claim Boundary

If M1965 passes, it may claim only:

```text
the calibrated 960-cell public diagnostic measured execution completed with
metadata-preserving episode rows.
```

It still cannot claim:

- controller-family ranking;
- paper-level benchmark evidence;
- policy improvement;
- finite-window vs GRU conclusion;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1965-executable-v2-task-quality-calibrated-measured-execution
```

M1965 may run the frozen measured execution command. Interpretation must be
deferred to M1966 result audit.
