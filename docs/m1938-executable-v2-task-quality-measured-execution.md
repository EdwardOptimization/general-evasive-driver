# M1938 Executable V2 Task-Quality Measured Execution

- status: completed
- decision: `task_quality_measured_execution_pass_route_to_result_audit`
- branch: `paper_route_task_quality_reset_execution`
- summary: `runs/m1938_executable_v2_task_quality_measured_execution/summary.json`
- episode rows: `runs/m1938_executable_v2_task_quality_measured_execution/episode_rows.csv`
- failure rows: `runs/m1938_executable_v2_task_quality_measured_execution/failure_rows.csv`
- environment rollout started: `true`
- policy action executed: `true`
- measured rollout started: `true`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1938 ran the frozen command from M1937:

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

## Pass-Gate Result

Result class:

```text
task_quality_measured_execution_pass
```

Key counts:

```text
episode_count: 960
target_episode_count: 960
failure_count: 0
spec_count: 80
profile_count: 12
tier_count: 5
role_count: 4
surface_count: 2
metric_completeness_failure_count: 0
all_selected_metrics_finite: true
guardrail_violation_count: 0
```

Guardrail state:

```text
environment_rollout_started: true
policy_action_executed: true
measured_rollout_started: true
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
profile_specific_tuning: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

Coverage:

```text
profile_counts: 12 profiles x 80 rows
tier_counts: 5 tiers x 192 rows
role_counts: 4 roles x 240 rows
surface_counts: steady_surface=480, post_friction_step=480
sampled_label_counts: aeb_feasible=240, aes_feasible=240, drift_required=240, unavoidable=240
```

Raw outcome counts:

```text
success_obstacle_pass: 40
collision_failure: 105
off_track_noncollision_noncompletion: 815
```

Termination reason counts:

```text
obstacle_collision: 90
off_track: 830
empty/none: 40
```

These outcome counts are not interpreted in M1938. They are routed to M1939
audit.

## Artifacts

M1938 wrote:

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

`failure_rows.csv` and `metric_completeness_failures.csv` are header-only.

## Interpretation Boundary

M1938 supports:

```text
the reset-valid M1928 public task-quality panel has complete measured rollout
artifacts over all 960 public diagnostic cells.
```

M1938 does not support:

- controller-family ranking;
- paper-level benchmark result;
- finite-window vs GRU conclusion;
- policy improvement claim;
- level3 self-identification.

Those require result audit, outcome localization, comparison rules, and later
generalization/mechanism gates.

## Next

Next milestone:

```text
m1939-executable-v2-task-quality-measured-execution-result-audit
```

M1939 should audit completeness and raw outcome structure before any controller
ranking or repair.
