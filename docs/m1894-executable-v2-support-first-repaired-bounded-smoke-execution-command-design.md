# M1894 Executable V2 Support-First Repaired Bounded-Smoke Execution Command Design

- status: completed
- decision: `support_first_repaired_bounded_smoke_execution_command_design_admit_execution`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- parent implementation: `docs/m1893-executable-v2-support-first-repaired-bounded-smoke-runner-implementation.md`
- runner: `src/autodrift/executable_v2_support_first_repaired_bounded_smoke_execution.py`
- repaired specs: `runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_executable_specs.json`
- repaired workload: `runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_workload_matrix.csv`
- repaired import rows: `runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_import_rows.csv`
- source episode rows: `runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv`
- real measured rollout run in M1894: false
- policy action executed in M1894: false
- training/replay/PPO: false

## Purpose

M1894 fixes the exact repaired bounded-smoke execution command and pass/fail
gates for the later public diagnostic rollout. It does not run the workload.
Because M1894 is the command-design milestone, the real execution output
directory is assigned to M1895.

## Preconditions Checked

M1889/M1890 repaired adapter preflight remains the parent real-artifact input:

```text
result_class: support_first_repaired_runner_adapter_pass
selected source specs: 16
role surfaces: 8
controller profiles: 12
patched executable specs: 48
new rollout workload cells: 576
import/postprocess rows: 384
total repaired-smoke panel rows: 960
config failures: 0
missing import rows: 0
duplicate specs/workloads: 0 / 0
guardrail violations: 0
```

M1893 implemented the required wrapper and focused tests passed:

```text
tests/test_executable_v2_support_first_repaired_bounded_smoke_execution.py
4 passed
```

The wrapper CLI exposes the required inputs:

```text
--support-first-repaired-measured-specs
--support-first-repaired-workload
--support-first-repaired-import-rows
--source-episode-rows
--m1674-run-dir
--eval-seed-base
--device
--output-dir
--no-resume
--next-blocker
```

## Exact Execution Command

M1895 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_support_first_repaired_bounded_smoke_execution \
  --support-first-repaired-measured-specs \
  runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_executable_specs.json \
  --support-first-repaired-workload \
  runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_workload_matrix.csv \
  --support-first-repaired-import-rows \
  runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_import_rows.csv \
  --source-episode-rows \
  runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv \
  --m1674-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --eval-seed-base 189500 \
  --device cpu \
  --output-dir runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution \
  --no-resume \
  --next-blocker m1896-executable-v2-support-first-repaired-bounded-smoke-execution-result-audit
```

If runtime is interrupted, the same command may be rerun without `--no-resume`
to continue from existing `rollout_episode_rows.csv`. Import rows are
deterministically rebuilt from M1889 metadata and M1880 source episode rows at
finalization.

## Required M1895 Output Artifacts

The execution must write:

```text
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/summary.json
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/rollout_episode_rows.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/import_episode_rows.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/failure_rows.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/import_failure_rows.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/run_state.json
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/profile_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/controller_profile_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/role_panel_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/role_surface_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/surface_variant_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/scenario_profile_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/hidden_dynamics_bucket_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/road_boundary_bucket_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/obstacle_timing_bucket_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/obstacle_lateral_bucket_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/sampled_obstacle_label_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/repair_variant_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/repair_variant_kind_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/geometry_variant_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/success_semantics_variant_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/execution_row_kind_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/controller_profile_repair_variant_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/controller_profile_role_surface_repair_variant_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/role_surface_repair_variant_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/repair_variant_outcome_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/outcome_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/termination_reason_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/import_rollout_alignment.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/profile_hidden_dynamics_worst_bucket.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/metric_completeness_summary.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/metric_completeness_failures.csv
```

## Pass Criteria For M1895

M1895 should pass only if `summary.json` reports:

```text
result_class: executable_v2_support_first_repaired_bounded_smoke_execution_pass
rollout_episode_count: 576
import_episode_count: 384
total_panel_row_count: 960
failure_count: 0
import_failure_count: 0
source_episode_join_missing_count: 0
controller_profile_count: 12
selected_source_spec_count: 16
repaired_executable_spec_count: 48
role_panel_count: 4
role_surface_count: 8
repair_variant_count: 5
rollout_variant_count: 3
import_variant_count: 2
profile_alias_mismatch_count: 0
duplicate_panel_row_count: 0
all_selected_metrics_finite: true
metric_completeness_passed: true
metric_completeness_failure_count: 0
guardrail_violation_count: 0
environment_rollout_started: true
measured_rollout_started: true
policy_action_executed: true
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

If any target count, import join, metric completeness, failure row, duplicate
panel row, or guardrail check fails, the next step must be a result/failure
audit, not controller ranking.

## Claim Boundary

Supported by M1894:

```text
exact M1895 repaired bounded-smoke execution command is fixed
pass/fail counters are pre-registered
M1895 measured execution is admissible
```

Not supported by M1894:

```text
measured rollout result
repaired task-quality conclusion
controller-family ranking
paper-level benchmark evidence
current-response / finite-window / GRU comparison result
level3 self-identification evidence
```

## Decision

M1894 admits M1895 measured execution over the fixed repaired bounded-smoke
public diagnostic workload. Interpretation remains deferred to M1896 result
audit.
