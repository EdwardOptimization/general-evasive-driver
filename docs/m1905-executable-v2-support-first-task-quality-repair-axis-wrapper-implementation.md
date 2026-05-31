# M1905 Executable V2 Support-First Task-Quality Repair-Axis Wrapper Implementation

- status: completed
- decision: `task_quality_repair_axis_wrapper_implementation_pass_admit_preflight`
- manifest: `experiments/manifests/m1905-executable-v2-support-first-task-quality-repair-axis-wrapper-implementation.json`
- wrapper: `src/autodrift/executable_v2_support_first_task_quality_repair_axis_execution.py`
- tests: `tests/test_executable_v2_support_first_task_quality_repair_axis_execution.py`
- focused tests: `3 passed`
- real M1902 workload run: false
- reset/rollout in M1905: false
- measured execution in M1905: false
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## What Changed

M1905 implements the wrapper infrastructure required by M1904 without running
the real M1902 matrix. The wrapper now supports:

```text
matrix loading
row splitting by execution_row_kind
planned rollout-row preparation
import/postprocess source-episode joins
axis metadata overlay
guardrail reset for imported/postprocessed rows
near-miss diagnostic recomputation for imported/postprocessed rows
dry-run/preflight summary generation
basic count aggregates by axis, variant, and row kind
```

The implementation deliberately does not execute the real environment. It
prepares the protocol and dry-run artifacts needed before a later rollout
milestone.

## Focused Tests

Command:

```bash
PYTHONPATH=src python -m pytest -q tests/test_executable_v2_support_first_task_quality_repair_axis_execution.py
```

Result:

```text
3 passed
```

The tests cover:

```text
1. split_axis_matrix_rows and planned_rollout_rows preserve axis metadata.
2. import_postprocess_episode_rows joins source_episode_workload_id, overlays
   axis metadata, recomputes near-miss flags, and resets parent rollout
   provenance flags.
3. dry_run_prepare_execution summarizes the wrapper contract without rollout.
```

## Wrapper Boundary

Implemented:

```text
src/autodrift/executable_v2_support_first_task_quality_repair_axis_execution.py
```

Key functions:

```text
split_axis_matrix_rows
planned_rollout_rows
import_postprocess_episode_rows
aggregate_count_rows
dry_run_prepare_execution
write_dry_run_artifacts
```

The module has a CLI for dry-run/preflight artifact generation. That CLI still
does not run environment reset or rollout.

## Important Scope Note

M1905 is not a measured execution implementation. It creates a preflight-capable
wrapper layer. The next step should run that wrapper in no-rollout dry-run mode
over the real M1902 matrix to validate counts and joins before any measured
execution wrapper is admitted.

## Decision

Route to:

```text
m1906-executable-v2-support-first-task-quality-repair-axis-wrapper-preflight
```

M1906 should run only the dry-run/preflight command over the real M1902 matrix:

```text
expected planned rollout rows: 960
expected import/postprocess rows: 576
expected combined panel rows: 1536
expected failure count: 0
```

M1906 must not run environment reset, rollout, measured execution, training,
replay, PPO, private holdout, controller ranking, paper-level claims, or level3
self-ID claims.

## Claim Boundary

Supported:

- wrapper infrastructure exists and passes focused tests;
- real matrix execution remains deferred;
- controller ranking remains blocked.

Unsupported:

- successful real M1902 preflight before M1906;
- task-quality repair success;
- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.
