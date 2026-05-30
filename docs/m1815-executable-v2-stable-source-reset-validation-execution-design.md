# M1815 Executable V2 Stable Source Reset Validation Execution Design

- status: completed
- decision: `stable_source_reset_validation_adapter_execution_design_admit_preflight_run`
- source implementation: `src/autodrift/executable_v2_stable_source_reset_validation_adapter.py`
- project artifact conversion run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1814 implemented the no-reset adapter, but the adapter has not yet been run on
the real M1811 materialization artifacts. M1815 pre-registers the exact command
for that conversion and keeps reset validation blocked until the converted
payload exists.

## Input Artifacts

```text
runs/m1811_executable_v2_stable_source_materialization/stable_source_materialization_specs.json
runs/m1811_executable_v2_stable_source_materialization/stable_source_materialization_matrix.csv
```

## Output Directory

```text
runs/m1816_executable_v2_stable_source_reset_validation_adapter
```

## Exact M1816 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_stable_source_reset_validation_adapter \
  --stable-materialization-specs runs/m1811_executable_v2_stable_source_materialization/stable_source_materialization_specs.json \
  --stable-materialization-matrix runs/m1811_executable_v2_stable_source_materialization/stable_source_materialization_matrix.csv \
  --output-dir runs/m1816_executable_v2_stable_source_reset_validation_adapter \
  --target-materialization-spec-count 3 \
  --target-executable-spec-count 36 \
  --target-profile-count 12 \
  --target-role-surface-count 1 \
  --next-blocker m1817-executable-v2-stable-source-reset-validation-adapter-result-audit
```

This command is a no-reset conversion only. It should not instantiate
`AutoDriftEnv`, should not call `env.reset`, and should not execute policy
actions.

## Expected Counts

M1816 should pass only if:

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
| `env_config_missing_count` | 0 |
| `missing_join_count` | 0 |
| `duplicate_workload_count` | 0 |
| `guardrail_violation_count` | 0 |

Expected output artifacts:

```text
summary.json
targeted_reset_executable_v2_panel_specs.json
targeted_reset_executable_v2_panel_specs.csv
targeted_reset_validation_matrix.csv
targeted_reset_missing_join_rows.csv
targeted_reset_duplicate_workload_rows.csv
targeted_reset_validation_claim_boundary.csv
```

The converted JSON payload must contain:

```text
executable_v2_panel_specs
```

so a later milestone can run the existing M1792 reset adapter.

## Pass Criteria

M1816 passes if the adapter result class is:

```text
executable_v2_stable_source_reset_validation_adapter_pass
```

and all expected counts match. M1816 does not prove reset feasibility. It only
proves that M1811 stable sources can be represented as executable v2 reset specs.

## Follow-Up

If M1816 passes, route to:

```text
m1817-executable-v2-stable-source-reset-validation-adapter-result-audit
```

The audit should decide whether to run a targeted M1792 reset preflight over:

```text
runs/m1816_executable_v2_stable_source_reset_validation_adapter/targeted_reset_executable_v2_panel_specs.json
```

with target counts:

```text
--target-spec-count 36
--target-profile-count 12
--target-role-surface-count 1
```

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

- exact no-reset adapter execution command;
- input artifacts, output directory, target counts, and next blocker.

Unsupported:

- adapter execution result;
- targeted reset validation result;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
