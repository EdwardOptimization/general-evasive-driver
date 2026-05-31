# M1936 Executable V2 Task-Quality Measured Runner Adapter Implementation

- status: completed
- decision: `task_quality_measured_runner_adapter_implementation_pass_admit_command_design`
- branch: `paper_route_task_quality_reset_execution`
- source: `src/autodrift/executable_v2_task_quality_measured_runner.py`
- tests: `tests/test_executable_v2_task_quality_measured_runner.py`
- focused tests: `3 passed`
- real M1928 measured execution in M1936: `false`
- rollout over real 960-cell workload: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## What Changed

M1936 adds a focused measured runner adapter for the reset-valid M1928
task-quality scenario panel.

New helper:

```text
src/autodrift/executable_v2_task_quality_measured_runner.py
```

New tests:

```text
tests/test_executable_v2_task_quality_measured_runner.py
```

The helper is designed for the M1928 schema:

```text
executable_task_specs.json
executable_workload_matrix.csv
```

It does not route through the older generic full-rollout output schema, the
support-first measured schema, or the repair-axis matrix schema.

## Adapter Behavior

The adapter can:

- load M1928 executable specs and workload rows;
- join workload rows to specs by `task_source_id`;
- validate required workload fields and duplicate workload IDs;
- preserve tier, role, split, surface, boundary-mode, accepted-cell-rule, and
  source metadata in every episode and failure row;
- load real profile configs/checkpoints when no synthetic rollout function is
  injected;
- run an injectable synthetic rollout path for tests;
- write `episode_rows.csv`, `failure_rows.csv`, metric-completeness failures,
  claim boundary, run state, and summary;
- write aggregates by profile, tier, role, surface, sampled label, outcome, and
  termination reason;
- fail closed on schema mismatch or rollout exceptions.

The adapter preserves the claim boundary:

```text
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Synthetic Test Coverage

Focused tests cover:

```text
test_task_quality_measured_runner_preserves_metadata_and_aggregates
test_task_quality_measured_runner_preserves_rollout_failures
test_task_quality_measured_runner_fails_closed_on_schema_mismatch
```

Command:

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests/test_executable_v2_task_quality_measured_runner.py
```

Result:

```text
3 passed
```

The tests use synthetic specs/workloads and an injected fake rollout function.
They do not run the real M1928 960-cell workload and do not execute real policy
actions.

## Later Real Execution Command Shape

M1937 should freeze a command equivalent to:

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

M1937 should be command design only. M1938 should be the first real measured
execution milestone.

## Claim Boundary

M1936 supports only:

```text
metadata-preserving measured runner infrastructure exists and has focused
synthetic tests.
```

It does not support:

- real rollout success;
- controller-family ranking;
- policy improvement;
- finite-window vs GRU comparison;
- paper-level benchmark evidence;
- level3 self-identification.

## Next

Next milestone:

```text
m1937-executable-v2-task-quality-measured-execution-command-design
```

M1937 should freeze the exact real measured execution command and pass gates
before M1938 runs the 960-cell public diagnostic workload.
