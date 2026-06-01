# M2209 Paper-Route Current-Sim Offtrack-Support Measured-Execution Rerun

- status: completed
- decision: `current_sim_offtrack_support_measured_execution_rerun_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2209-paper-route-current-sim-offtrack-support-measured-execution-rerun.json`
- run artifact: `runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/summary.json`
- real measured execution: `true`
- environment rollout started: `true`
- policy actions executed: `true`
- training/replay/PPO in M2209: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M2209 ran the repaired rerun command admitted by M2208:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_measured_runner \
  --executable-task-specs runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json \
  --workload runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/materialized_workload.csv \
  --output-dir runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun \
  --eval-seed-base 220900 \
  --device cpu \
  --no-resume \
  --target-episode-count 2304 \
  --target-spec-count 288 \
  --target-profile-count 8 \
  --next-blocker m2210-paper-route-current-sim-offtrack-support-measured-execution-rerun-result-audit
```

## Execution Result

The repaired measured execution completed:

```text
result_class: current_sim_controlled_comparison_measured_execution_pass
episode_count: 2304
target_episode_count: 2304
failure_count: 0
spec_count: 288
target_spec_count: 288
profile_count: 8
target_profile_count: 8
metadata_missing_count: 0
metric_completeness_failure_count: 0
task_family_quota_pass: true
profile_quota_pass: true
history_representation_quota_pass: true
all_selected_metrics_finite: true
guardrail_violation_count: 0
environment_rollout_started: true
policy_action_executed: true
measured_rollout_started: true
```

Raw outcome counts:

```text
success_obstacle_pass: 374
collision_failure: 49
off_track_noncollision_noncompletion: 1881
```

Raw termination counts:

```text
blank/success-like: 374
obstacle_collision: 40
off_track: 1890
```

These are descriptive execution outputs only. They are not a controller-family
ranking, finite-window vs GRU verdict, paper-level result, or self-ID claim.

## Quotas

Task family counts:

```text
T1_reactive_emergency_avoidance: 192
T2_delayed_actuator_response: 240
T3_diagnostic_warmup_obstacle_reveal: 528
T4_same_current_different_older_history: 560
T5_terminal_boundary_near_constraint: 784
```

History representation counts:

```text
current_response: 288
one_step_command_response: 288
explicit_finite_window: 1152
online_recurrent_hidden: 576
```

Each profile has `288` episodes.

## Artifacts

M2209 wrote:

```text
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/summary.json
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/failure_rows.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/profile_aggregate.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/history_representation_aggregate.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/task_family_aggregate.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/outcome_aggregate.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/termination_reason_aggregate.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/claim_boundary.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/run_state.json
```

## Claim Boundary

Supported by M2209:

```text
The repaired 2304-cell current-sim offtrack-support measured execution ran end
to end with zero runner failures and zero guardrail violations.
```

Still unsupported:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2210 must audit the measured execution result, classify the outcome
distribution, and decide whether this panel is comparison-ready or still
blocked by offtrack dominance / support quality. It must not rerun the workload
or rank profiles.
