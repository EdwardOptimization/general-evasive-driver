# M2174 Paper-Route Current-Sim Measured Execution Implementation and Run

- status: completed
- decision: `current_sim_measured_execution_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2174-paper-route-current-sim-measured-execution-implementation-and-run.json`
- run artifact: `runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/summary.json`
- real measured execution: `true`
- environment rollout started: `true`
- policy actions executed: `true`
- training/replay/PPO in M2174: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M2174 ran the frozen M2173 measured-execution command over the M2171
materialized workload.

Execution passed:

```text
result_class = current_sim_controlled_comparison_measured_execution_pass
episode_count = 320
failure_count = 0
spec_count = 40
profile_count = 8
metadata_missing_count = 0
metric_completeness_failure_count = 0
task_family_quota_pass = true
profile_quota_pass = true
history_representation_quota_pass = true
all_selected_metrics_finite = true
guardrail_violation_count = 0
```

The execution preserved the expected quotas:

```text
task families:
  T1_reactive_emergency_avoidance = 64
  T2_delayed_actuator_response = 64
  T3_diagnostic_warmup_obstacle_reveal = 64
  T4_same_current_different_older_history = 64
  T5_terminal_boundary_near_constraint = 64

profiles:
  8 profiles x 40 episodes each

history representations:
  current_response = 40
  one_step_command_response = 40
  explicit_finite_window = 160
  online_recurrent_hidden = 80
```

Raw outcome counts:

```text
success_obstacle_pass = 63
collision_failure = 20
off_track_noncollision_noncompletion = 237
```

Termination reasons:

```text
obstacle_collision = 16
off_track = 241
blank/success-like = 63
```

These are descriptive execution outputs only. They are not a controller-family
ranking and do not support a finite-window vs GRU verdict without M2175 audit
and a denominator-backed comparison protocol.

## Artifacts

M2174 wrote:

```text
runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/summary.json
runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/episode_rows.csv
runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/failure_rows.csv
runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/profile_aggregate.csv
runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/history_representation_aggregate.csv
runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/task_family_aggregate.csv
runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/outcome_aggregate.csv
runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/termination_reason_aggregate.csv
runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/claim_boundary.csv
```

## Claim Boundary

Supported:

```text
The audited current-sim materialized workload can be executed end to end across
the full 320-cell panel.
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

M2175 must audit the measured execution result. That audit should classify the
raw outcome distribution, decide whether the run is comparison-ready, and route
to either denominator-backed comparison design or task/outcome repair. It must
not rerun the workload or rank profiles.
