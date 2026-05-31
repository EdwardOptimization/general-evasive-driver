# M1909 Executable V2 Support-First Task-Quality Repair-Axis Measured Wrapper Implementation

- status: completed
- decision: `task_quality_repair_axis_measured_wrapper_implementation_pass_admit_command_design`
- branch: `paper_route_repair_axis_measured_wrapper`
- parent synthesis: `docs/m1908-executable-v2-support-first-task-quality-repair-axis-branch-synthesis.md`
- source: `src/autodrift/executable_v2_support_first_task_quality_repair_axis_execution.py`
- tests: `tests/test_executable_v2_support_first_task_quality_repair_axis_execution.py`
- focused tests: `5 passed`
- real M1902 workload run: `false`
- environment reset/rollout/measured execution in M1909: `false`
- mocked rollout helper used in tests: `true`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M1909 extends the M1905/M1906 dry-run wrapper with measured execution extension
points while keeping real execution deferred. The new extension point is a
callable boundary:

```text
rollout_fn(planned_row, eval_seed) -> measured episode row
```

The wrapper owns:

- planning rollout rows from repair-axis geometry rows;
- calling the supplied rollout function for geometry rows;
- overlaying task-quality repair-axis metadata onto measured rows;
- row-level failure persistence when the supplied rollout function raises;
- import/postprocess joins for original and semantics-only rows;
- combined panel summaries and aggregate artifacts;
- claim-boundary flags that keep ranking, paper, and level3 self-ID claims
  blocked.

New functions:

- `measured_rollout_episode_rows`
- `measured_prepare_execution`
- `write_measured_artifacts`

Existing dry-run behavior is preserved.

## Test Evidence

Command:

```bash
PYTHONPATH=src python -m pytest -q tests/test_executable_v2_support_first_task_quality_repair_axis_execution.py
```

Result:

```text
5 passed in 1.01s
```

The focused tests verify:

- dry-run split/import behavior remains intact;
- a mocked rollout function is called through the new extension point;
- measured rollout rows preserve and overlay repair-axis metadata;
- claim-boundary flags remain false;
- measured rollout rows and import/postprocess rows are combined into a panel;
- measured artifacts can be written without touching the real M1902 workload.

## Supported Claims

Supported:

- the task-quality repair-axis wrapper now has measured rollout extension
  points;
- mocked tests validate row metadata preservation and panel merging;
- the next branch step may design an exact measured-wrapper command.

Supported paper-route category:

```text
scenario/task-quality execution infrastructure: improved
workflow or complexity reduction: improved
engineering driver performance: unchanged
mechanism evidence for history dependence: unchanged
high-fidelity validation readiness: unchanged
```

## Unsupported Claims

Still blocked:

- task-quality repair success;
- controller-family ranking;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification;
- real measured execution of the M1902 matrix.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- measured execution started: `false`
- real M1902 workload executed: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted checkpoint: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Next

Next milestone:

```text
m1910-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-command-design
```

M1910 should register the exact command, target counts, output directory,
pass/fail gates, and claim boundaries for running the real measured-wrapper
execution in a later milestone. M1910 itself should still not run reset,
rollout, measured execution, training, PPO, controller ranking, paper-level
claim, or level3 self-ID claim.
