# M1814 Executable V2 Stable Source Reset Validation Adapter Implementation

- status: completed
- decision: `stable_source_reset_validation_adapter_implementation_pass_route_to_execution_design`
- module: `src/autodrift/executable_v2_stable_source_reset_validation_adapter.py`
- test: `tests/test_executable_v2_stable_source_reset_validation_adapter.py`
- project artifact conversion run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Summary

M1814 implements the no-reset conversion adapter required by M1813. The adapter
reads stable source materialization artifacts:

```text
stable_source_materialization_specs.json
stable_source_materialization_matrix.csv
```

and writes a reset-adapter-compatible payload:

```text
targeted_reset_executable_v2_panel_specs.json
```

with payload key:

```text
executable_v2_panel_specs
```

The implementation does not run the real M1811 project artifacts and does not
run any environment reset. Focused tests use synthetic materialization fixtures
only.

## Implemented Artifacts

The adapter writes:

```text
summary.json
targeted_reset_executable_v2_panel_specs.json
targeted_reset_executable_v2_panel_specs.csv
targeted_reset_validation_matrix.csv
targeted_reset_missing_join_rows.csv
targeted_reset_duplicate_workload_rows.csv
targeted_reset_validation_claim_boundary.csv
```

Each converted row preserves:

```text
v2_panel_spec_id
source_v1_bounded_panel_spec_id
source_v1_role_panel_id
source_scenario_spec_id
v2_role_surface_id
role_panel_id
profile_name
profile_config_path
checkpoint_path
v2_task_label
allowed_labels_metadata_only
labels_enter_actor_input
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
v2_primary_metric
v2_primary_metric_direction
v2_admissibility_gate
reset_ready_spec
diagnostic_only_no_ranking_claim
v2_ranking_admissible_by_default
reset_validation_required
materialized_source_scenario_spec_id
materialized_bounded_panel_spec_id
target_bounded_panel_spec_id
stable_materialization_key
env_config
```

Stable source rows are converted to:

```text
v2_role_surface_id: stable_avoidance_aes
v2_primary_metric: admissible_obstacle_pass_rate
v2_primary_metric_direction: higher_is_better
v2_admissibility_gate: collision_rate_low_and_off_track_rate_low
reset_ready_spec: true
diagnostic_only_no_ranking_claim: true
v2_ranking_admissible_by_default: false
reset_validation_required: true
```

## Verification

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest tests/test_executable_v2_stable_source_reset_validation_adapter.py -q
```

Result:

```text
2 passed in 0.07s
```

The tests verify:

- `executable_v2_panel_specs` payload shape;
- profile-control expansion from materialized sources;
- `env_config` preservation;
- stable v2 metric and admissibility metadata;
- no label leakage;
- ranking blocked by default;
- missing join and duplicate workload diagnostics;
- no reset, rollout, training, replay, PPO, promotion, ranking, paper-level, or
  level3 claim.

## Expected Project Execution Counts

A later execution-design milestone should run the adapter over M1811 artifacts
with these expected counts:

| field | expected |
| --- | ---: |
| `input_materialization_spec_count` | 3 |
| `input_materialization_matrix_row_count` | 36 |
| `targeted_reset_executable_spec_count` | 36 |
| `profile_control_count` | 12 |
| `role_surface_count` | 1 |
| `reset_ready_spec_count` | 36 |
| `reset_validation_required_count` | 36 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `missing_join_count` | 0 |
| `duplicate_workload_count` | 0 |
| `guardrail_violation_count` | 0 |

## Guardrails

- project artifact conversion run: `false`
- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- no-reset adapter implementation;
- focused tests pass;
- adapter preserves v2 reset payload shape and claim boundary.

Unsupported:

- project artifact conversion result;
- targeted reset validation result;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Decision

Route to:

```text
m1815-executable-v2-stable-source-reset-validation-execution-design
```

M1815 should pre-register the exact no-reset adapter command over M1811
artifacts. It should not run conversion or reset.
