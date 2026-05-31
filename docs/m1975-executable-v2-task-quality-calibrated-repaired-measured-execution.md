# M1975 Executable V2 Task-Quality Calibrated Repaired Measured Execution

- status: completed
- decision: `task_quality_calibrated_repaired_measured_execution_pass_route_to_result_synthesis`
- run dir: `runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired`
- measured execution in M1975: `true`
- environment rollout started: `true`
- policy action executed: `true`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1975 ran the exact frozen M1974 command:

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

## Result

The repaired calibrated measured execution completed cleanly:

```text
result_class: task_quality_calibrated_measured_execution_pass
episode_count: 960
target_episode_count: 960
spec_count: 80
profile_count: 12
failure_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
source_kind_quota_pass: true
role_surface_quota_pass: true
environment_rollout_started: true
policy_action_executed: true
measured_rollout_started: true
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Outcome Distribution

Raw outcomes remain low-support and offtrack-dominated:

```text
success_obstacle_pass: 38
collision_failure: 150
off_track_noncollision_noncompletion: 772
```

Termination reasons:

```text
success / blank termination: 38
obstacle_collision: 109
off_track: 813
```

Source-kind aggregates:

```text
anchor_neighborhood:
  episodes: 384
  success_rate: 0.0000000000
  collision_rate: 0.0000000000
  clearance_margin_mean: 42.3614039681
  return_mean: 4.9856141150

mitigation_isolation_check:
  episodes: 192
  success_rate: 0.0677083333
  collision_rate: 0.5520833333
  clearance_margin_mean: 0.8132220862
  return_mean: -2.8422137626

offtrack_boundary_relief:
  episodes: 96
  success_rate: 0.0000000000
  collision_rate: 0.0000000000
  clearance_margin_mean: 15.9134214471
  return_mean: 5.5346180853

success_stabilizer:
  episodes: 288
  success_rate: 0.0868055556
  collision_rate: 0.1527777778
  clearance_margin_mean: 9.0023842366
  return_mean: 4.5516428089
```

Outcome aggregates:

```text
collision_failure:
  episodes: 150
  success_rate: 0.0000000000
  collision_rate: 1.0000000000
  clearance_margin_mean: -0.3476455158

off_track_noncollision_noncompletion:
  episodes: 772
  success_rate: 0.0000000000
  collision_rate: 0.0000000000
  clearance_margin_mean: 26.5653157030

success_obstacle_pass:
  episodes: 38
  success_rate: 1.0000000000
  collision_rate: 0.0000000000
  clearance_margin_mean: 2.2898944221
```

## Supported Claims

Supported:

- the repaired calibrated measured runner executed the full `80 x 12 = 960`
  public diagnostic workload;
- the offtrack parent-tier sentinel repair survived reset and measured rollout;
- episode rows, aggregate artifacts, source-kind quotas, role-surface quotas,
  metric completeness, and guardrails are clean;
- no training, replay, PPO, controller-family ranking, paper-level benchmark
  claim, or level3 self-ID claim was made.

Unsupported:

- controller-family ranking;
- paper-level benchmark evidence;
- policy improvement;
- finite-window vs GRU conclusion;
- level3 self-identification;
- high-fidelity validation readiness.

## Next Route

Decision:

```text
route to result synthesis
```

Next milestone:

```text
m1976-executable-v2-task-quality-calibrated-repaired-measured-execution-result-synthesis
```

M1976 must synthesize M1966-M1975 before any additional local repair or rerun.
The measured execution pass resolves the runner/materialization blocker, but
the low-support offtrack-dominated outcome distribution blocks controller
ranking and paper-level comparison.
