# M2184 Paper-Route Current-Sim Repeat Measured Execution Implementation and Run

- status: completed
- decision: `current_sim_repeat_measured_execution_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2184-paper-route-current-sim-repeat-measured-execution-implementation-and-run.json`
- summary: `runs/m2184_paper_route_current_sim_repeat_measured_execution/summary.json`
- training in M2184: `false`
- measured execution in M2184: `true`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command Run

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_measured_runner \
  --executable-task-specs runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json \
  --workload runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/combined_new_repeat_materialized_workload.csv \
  --output-dir runs/m2184_paper_route_current_sim_repeat_measured_execution \
  --eval-seed-base 218400 \
  --device cpu \
  --no-resume \
  --target-episode-count 640 \
  --target-spec-count 40 \
  --target-profile-count 8 \
  --next-blocker m2185-paper-route-current-sim-repeat-measured-execution-result-audit
```

## Execution Result

```text
result_class: current_sim_controlled_comparison_measured_execution_pass
episode_count: 640
failure_count: 0
spec_count: 40
profile_count: 8
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
task_family_quota_pass: true
profile_quota_pass: true
history_representation_quota_pass: true
```

Raw outcome counts:

```text
success_obstacle_pass: 100
collision_failure: 36
off_track_noncollision_noncompletion: 504
```

Repeat metadata was preserved:

```text
training_repeat_aggregate.csv exists
repeat_1_seed_21761: 320 episodes, success_rate 0.15625, collision_rate 0.05625
repeat_2_seed_21762: 320 episodes, success_rate 0.15625, collision_rate 0.05625
```

## Descriptive Aggregates

The profile aggregate exists for audit use only. It is not a ranking result.

```text
L0_current_masked: success_rate 0.000
L1_one_step: success_rate 0.175
L2_window_13: success_rate 0.350
L2_window_25: success_rate 0.075
L2_window_50: success_rate 0.300
L2_window_100: success_rate 0.250
L3_online_gru: success_rate 0.050
L3_reset_control: success_rate 0.050
```

## Claim Boundary

Allowed claim:

```text
The frozen repeat measured-execution command completed 640 current-sim repeat
episodes and preserved repeat metadata with no runner failures.
```

Still blocked:

```text
profile ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2185 must audit this result before any interpretation. The audit should pay
attention to both the offtrack-dominated outcome distribution and the identical
repeat-level aggregate values before deciding the next route.
