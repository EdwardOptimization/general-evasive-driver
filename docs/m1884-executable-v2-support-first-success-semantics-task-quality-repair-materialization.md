# M1884 Executable V2 Support-First Success Semantics Task-Quality Repair Materialization

- status: completed
- decision: `support_first_success_semantics_task_quality_repair_materialization_pass_route_to_result_audit`
- artifact: `runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/summary.json`
- reset/rollout in M1884: false
- training/replay/PPO: false

## Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_support_first_success_semantics_task_quality_repair_materialization \
  --workload-matrix runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_workload_matrix.csv \
  --episode-rows runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv \
  --localization-summary runs/m1882_executable_v2_support_first_outcome_localization/summary.json \
  --output-dir runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization \
  --target-workload-row-count 2160 \
  --target-repair-variant-count 5 \
  --next-blocker m1885-executable-v2-support-first-success-semantics-task-quality-repair-materialization-result-audit
```

## Summary

M1884 implements and runs the no-rollout materializer designed in M1883. It
does not run environment reset, environment rollout, training, replay, PPO, or
controller-family ranking.

Key results:

```text
result_class: support_first_success_semantics_task_quality_repair_materialization_pass
workload_row_count: 2160 / 2160
episode_row_count: 2160
repair_variant_count: 5 / 5
repair_matrix_row_count: 10800 / 10800
original_baseline_row_count: 2160
original_baseline_retained: true
controller_profile_count: 12
role_panel_count: 4
role_surface_count: 8
support_first_spec_count: 180
profile_alias_mismatch_count: 0
duplicate_repair_key_count: 0
role_semantics_complete: true
guardrail_violation_count: 0
```

Repair variants:

```text
original: 2160
semantics_only: 2160
finish_extended: 2160
road_relaxed: 2160
road_relaxed_finish_extended: 2160
```

## Diagnostic Signal Retained

M1884 also writes role-level diagnostic summaries from the completed M1880
episode rows. These do not rank controllers, but they show why the repair is
needed:

```text
drift_required_recovery:
  obstacle_clearance_pass_rate: 0.7674
  offtrack_after_clearance_rate: 0.7674
  collision_failure_rate: 0.2326

stable_aeb:
  obstacle_clearance_pass_rate: 0.8872
  offtrack_after_clearance_rate: 0.8872
  collision_failure_rate: 0.1128

stable_aes_only:
  obstacle_clearance_pass_rate: 0.9983
  offtrack_after_clearance_rate: 0.9983
  collision_failure_rate: 0.0017

unavoidable_mitigation:
  obstacle_clearance_pass_rate: 0.3519
  offtrack_after_clearance_rate: 0.3519
  collision_failure_rate: 0.6481
```

The diagnostic pattern supports the M1883 diagnosis: the zero-success result is
not immediately a controller-family result. It is largely a success semantics,
road-boundary, and recovery-window evaluation blocker.

## Artifacts

```text
runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/summary.json
runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/repair_variant_matrix.csv
runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/role_semantics_spec.json
runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/repair_variant_spec.json
runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/role_diagnostic_summary.csv
runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/duplicate_repair_keys.csv
```

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- measured rollout started: `false`
- policy action executed: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- semantic labels enter actor input: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- a baseline-preserving no-rollout repair matrix exists;
- role-aware success semantics are materialized as metric/output metadata only;
- all controller profiles and support-first workload cells are preserved;
- M1885 can audit whether the materialized matrix is sufficient for execution
  design.

Unsupported:

- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence;
- measured result for any repair variant.

## Decision

Route to M1885 result audit. Do not run repaired measured execution or ranking
until the audit verifies that the materialized variants are comparison-ready.
