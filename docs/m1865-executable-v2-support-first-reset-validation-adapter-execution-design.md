# M1865 Executable V2 Support-First Reset Validation Adapter Execution Design

- status: completed
- decision: `support_first_reset_validation_adapter_execution_design_admit_run`
- branch: `paper_route_executable_v2_support_first_reset_validation`
- parent implementation: `docs/m1864-executable-v2-support-first-reset-validation-adapter-implementation.md`
- source implementation: `src/autodrift/executable_v2_support_first_reset_validation_adapter.py`
- project artifact conversion run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1864 implemented and focused-tested the no-reset adapter, but it has not yet
been run on the real M1861 support-first materialization artifacts. M1865
pre-registers the exact command for that conversion and keeps reset validation
blocked until the converted payload exists.

## Input Artifacts

```text
runs/m1861_executable_v2_support_first_materialization/support_first_materialized_executable_v2_panel_specs.json
runs/m1861_executable_v2_support_first_materialization/summary.json
```

The expected input panel contains:

```text
materialized_spec_count: 180
role_count: 4
surface_count: 2
role_surface_count: 8
profile_count: 8
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
```

## Output Directory

```text
runs/m1866_executable_v2_support_first_reset_validation_adapter
```

## Exact M1866 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_support_first_reset_validation_adapter \
  --support-first-materialized-specs runs/m1861_executable_v2_support_first_materialization/support_first_materialized_executable_v2_panel_specs.json \
  --output-dir runs/m1866_executable_v2_support_first_reset_validation_adapter \
  --profile-config-path configs/paper_route_corrected_profiles/m1207_l0_current_masked.json \
  --target-materialized-spec-count 180 \
  --target-executable-spec-count 180 \
  --target-profile-count 8 \
  --target-role-count 4 \
  --target-surface-count 2 \
  --target-role-surface-count 8 \
  --next-blocker m1867-executable-v2-support-first-reset-validation-adapter-result-audit
```

This command is a no-reset conversion only. It must not instantiate
`AutoDriftEnv`, call `env.reset`, execute policy actions, run measured rollout,
train, replay, run PPO, rank controller families, or make paper-level claims.

## Expected Counts

M1866 should pass only if:

| field | expected |
| --- | ---: |
| `input_materialized_spec_count` | 180 |
| `targeted_reset_executable_spec_count` | 180 |
| `role_count` | 4 |
| `surface_count` | 2 |
| `role_surface_count` | 8 |
| `profile_count` | 8 |
| `reset_ready_spec_count` | 180 |
| `reset_validation_required_count` | 180 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `measured_execution_admissible_count` | 0 |
| `controller_family_ranking_admissible_count` | 0 |
| `missing_required_field_count` | 0 |
| `duplicate_key_count` | 0 |
| `guardrail_violation_count` | 0 |

Expected output artifacts:

```text
summary.json
support_first_reset_executable_v2_panel_specs.json
support_first_reset_executable_v2_panel_specs.csv
support_first_reset_validation_matrix.csv
support_first_reset_missing_field_rows.csv
support_first_reset_duplicate_key_rows.csv
support_first_reset_validation_claim_boundary.csv
```

The converted JSON payload must contain:

```text
executable_v2_panel_specs
```

so a later milestone can run reset-only validation over a standard
`executable_v2_panel_specs` payload.

## Pass Criteria

M1866 passes if the adapter result class is:

```text
executable_v2_support_first_reset_validation_adapter_pass
```

and all expected counts match. M1866 does not prove reset feasibility. It only
proves that the M1861 support-first materialized specs can be represented as
standard reset-validation payload rows.

## Follow-Up

If M1866 passes, route to:

```text
m1867-executable-v2-support-first-reset-validation-adapter-result-audit
```

The audit should decide whether to run reset-only validation over:

```text
runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json
```

with target counts:

```text
--target-spec-count 180
--target-profile-count 8
--target-role-surface-count 8
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
- reset validation result;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
