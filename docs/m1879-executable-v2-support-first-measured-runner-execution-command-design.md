# M1879 Executable V2 Support-First Measured Runner Execution Command Design

- status: completed
- decision: `support_first_measured_runner_execution_command_design_admit_measured_execution`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- parent implementation: `docs/m1878-executable-v2-support-first-measured-runner-implementation.md`
- runner: `src/autodrift/executable_v2_support_first_measured_runner_execution.py`
- M1875 measured specs: `runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.json`
- M1875 workload: `runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_workload_matrix.csv`
- real measured rollout run in M1879: false
- policy action executed in M1879: false
- training/replay/PPO: false

## Purpose

M1879 fixes the exact support-first measured runner execution command and
pass/fail gates for the later 2160-episode public diagnostic rollout. It does
not run the workload. Because M1879 is the command-design milestone, the real
execution output directory is assigned to M1880.

## Preconditions Checked

M1875 adapter preflight remains clean:

```text
result_class: executable_v2_support_first_measured_runner_adapter_pass
support_first_spec_count: 180
controller_profile_count: 12
workload_cell_count: 2160
role_count: 4
role_surface_count: 8
guardrail_violation_count: 0
```

The workload matrix currently has:

```text
rows: 2160
controller profiles: 12
support-first specs: 180
role panels: 4
role-surfaces: 8
```

The M1878 runner CLI exposes the required inputs:

```text
--support-first-measured-specs
--support-first-workload
--m1674-run-dir
--eval-seed-base
--device
--output-dir
--no-resume
--next-blocker
```

## Exact Execution Command

M1880 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_support_first_measured_runner_execution \
  --support-first-measured-specs \
  runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.json \
  --support-first-workload \
  runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_workload_matrix.csv \
  --m1674-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --eval-seed-base 187900 \
  --device cpu \
  --output-dir runs/m1880_executable_v2_support_first_measured_runner_execution \
  --no-resume \
  --next-blocker m1881-executable-v2-support-first-measured-runner-result-audit
```

If runtime is interrupted, the same command may be rerun without `--no-resume`
to continue from existing `episode_rows.csv`.

## Required M1880 Output Artifacts

The execution must write:

```text
runs/m1880_executable_v2_support_first_measured_runner_execution/summary.json
runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/failure_rows.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/run_state.json
runs/m1880_executable_v2_support_first_measured_runner_execution/profile_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/controller_profile_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/role_panel_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/role_surface_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/surface_variant_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/scenario_profile_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/hidden_dynamics_bucket_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/road_boundary_bucket_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/obstacle_timing_bucket_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/obstacle_lateral_bucket_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/sampled_obstacle_label_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/outcome_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/termination_reason_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/controller_profile_role_panel_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/controller_profile_role_surface_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/profile_outcome_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/role_panel_outcome_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/role_surface_outcome_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/profile_hidden_dynamics_worst_bucket.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/metric_completeness_summary.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/metric_completeness_failures.csv
```

## Pass Criteria For M1880

M1880 should pass only if `summary.json` reports:

```text
result_class: executable_v2_support_first_measured_runner_execution_pass
episode_count: 2160
failure_count: 0
controller_profile_count: 12
support_first_spec_count: 180
role_panel_count: 4
role_surface_count: 8
profile_alias_mismatch_count: 0
all_selected_metrics_finite: true
metric_completeness_passed: true
metric_completeness_failure_count: 0
guardrail_violation_count: 0
environment_rollout_started: true
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

If any target count, metric completeness, failure row, or guardrail check fails,
the next step must be a result/failure audit, not controller ranking.

## Claim Boundary

Supported by M1879:

```text
exact M1880 support-first measured execution command is fixed
pass/fail counters are pre-registered
M1880 measured execution is admissible
```

Not supported by M1879:

```text
measured rollout result
controller-family ranking
paper-level benchmark evidence
current-response / finite-window / GRU comparison result
level3 self-identification evidence
```

## Decision

M1879 admits M1880 measured execution over the fixed M1875 2160-cell public
diagnostic workload. Interpretation remains deferred to M1881 result audit.
