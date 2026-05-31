# M1937 Executable V2 Task-Quality Measured Execution Command Design

- status: completed
- decision: `task_quality_measured_execution_command_design_admit_execution`
- branch: `paper_route_task_quality_reset_execution`
- runner: `src/autodrift/executable_v2_task_quality_measured_runner.py`
- executable specs: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json`
- workload matrix: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_workload_matrix.csv`
- output dir: `runs/m1938_executable_v2_task_quality_measured_execution`
- target episode count: `960`
- target spec count: `80`
- target profile count: `12`
- device: `cpu`
- real measured execution in M1937: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1938 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_measured_runner \
  --executable-task-specs runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json \
  --workload runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_workload_matrix.csv \
  --output-dir runs/m1938_executable_v2_task_quality_measured_execution \
  --eval-seed-base 193800 \
  --target-episode-count 960 \
  --target-spec-count 80 \
  --target-profile-count 12 \
  --device cpu \
  --next-blocker m1939-executable-v2-task-quality-measured-execution-result-audit
```

M1937 does not run this command. It freezes it for M1938.

## Expected Artifacts

M1938 should write:

```text
runs/m1938_executable_v2_task_quality_measured_execution/summary.json
runs/m1938_executable_v2_task_quality_measured_execution/episode_rows.csv
runs/m1938_executable_v2_task_quality_measured_execution/failure_rows.csv
runs/m1938_executable_v2_task_quality_measured_execution/profile_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/tier_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/role_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/surface_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/sampled_label_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/outcome_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/termination_reason_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/metric_completeness_failures.csv
runs/m1938_executable_v2_task_quality_measured_execution/claim_boundary.csv
runs/m1938_executable_v2_task_quality_measured_execution/run_state.json
```

## Pass Gates

M1938 passes only if:

```text
result_class == task_quality_measured_execution_pass
episode_count == 960
target_episode_count == 960
failure_count == 0
spec_count == 80
target_spec_count == 80
profile_count == 12
target_profile_count == 12
tier_count == 5
role_count == 4
surface_count == 2
metric_completeness_failure_count == 0
all_selected_metrics_finite == true
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

If any row fails, M1938 must preserve the failure in `failure_rows.csv` and
route to M1939 result/failure audit. It must not repair, rerun with changed
seeds, or tune profiles inside the same milestone.

## Claim Boundary

If M1938 passes, it may claim only:

```text
the reset-valid M1928 public task-quality panel has complete measured rollout
artifacts over 12 controller profiles.
```

It still cannot claim:

- controller-family ranking;
- paper-level benchmark result;
- finite-window vs GRU conclusion;
- policy improvement;
- level3 self-identification.

Those require M1939 audit and later comparison/generalization/mechanism gates.

## Next

Next milestone:

```text
m1938-executable-v2-task-quality-measured-execution
```

M1938 may run the frozen measured execution command. Interpretation must be
deferred to M1939 result audit.
