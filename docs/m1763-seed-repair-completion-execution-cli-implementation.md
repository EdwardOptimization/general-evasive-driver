# M1763 Seed-Repair Completion Execution CLI Implementation

- status: completed
- decision: `admit_single_cell_completion_execution`
- no real missing-cell rollout: true
- training/replay/PPO: false

## Summary

M1763 implements the CLI required by M1762:

```text
python -m autodrift.seed_repair_completion_execution
```

The CLI is wired to the existing scenario-taxonomy workload-cell execution path
and the M1761 provenance helper. This milestone does not run the CLI on the real
M1756/M1758 artifacts and does not execute the missing policy episode.

## Implemented

New module:

```text
src/autodrift/seed_repair_completion_execution.py
```

The CLI:

- loads source M1756 episode/failure rows;
- selects and validates the M1760 seed-repair plan from M1758 probe rows;
- reconstructs the target workload row from metadata and executable specs;
- loads only the required controller profile;
- runs the repaired workload cell at replacement seed `175760`;
- rejects unexpected sampled obstacle labels;
- delegates artifact writing and provenance to `seed_repair_completion`.

Default fixed route:

```text
output_dir: runs/m1764_revised_scenario_taxonomy_single_seed_completion
source_run_dir: runs/m1756_revised_scenario_taxonomy_execution_after_wrapper_repair
probe_rows: runs/m1758_single_sampling_failure_reset_only_probe/probe_rows.csv
workload_id: m1728-s4-02::L2_window_13_current_tiled
original_eval_seed: 175761
replacement_eval_seed: 175760
expected_sampled_obstacle_label: unavoidable
next_blocker: m1765-single-cell-seed-repair-completion-result-audit
```

## Verification

Focused tests:

```text
tests/test_seed_repair_completion.py tests/test_seed_repair_completion_execution.py
7 passed
```

Compile check:

```text
python -m compileall -q src tests
```

The execution-CLI tests monkeypatch checkpoint loading, workload-cell execution,
and completion writing. They verify wiring and fixed seed behavior without
running a real policy episode.

## Guardrails

- real missing-cell policy rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile configs changed: `false`
- scenario specs changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- the completion execution CLI exists;
- the CLI preserves fixed inputs and seed-repair provenance requirements;
- focused tests pass without real policy rollout.

Unsupported:

- M1764 completion execution result;
- completed `864`-row matrix;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification evidence.

## Decision

Admit M1764 single-cell seed-repair completion execution using the M1762 fixed
command and pass gates.
