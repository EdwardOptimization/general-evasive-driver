# M1762 Single-Cell Seed-Repair Completion Execution Design

- status: completed
- decision: `admit_seed_repair_completion_execution_cli_implementation`
- no policy rollout: true
- training/replay/PPO: false

## Summary

M1762 pre-registers the exact one-cell completion execution route, but still
does not run the missing episode. The current helper can select the replacement
seed and write provenance-aware completion artifacts once a repaired row exists;
the next step is a small execution CLI that produces that repaired row through
the existing scenario-taxonomy workload-cell path.

## Fixed Inputs

Source partial run:

```text
runs/m1756_revised_scenario_taxonomy_execution_after_wrapper_repair
```

Source completed rows:

```text
runs/m1756_revised_scenario_taxonomy_execution_after_wrapper_repair/episode_rows.csv
```

Source failure row:

```text
runs/m1756_revised_scenario_taxonomy_execution_after_wrapper_repair/failure_rows.csv
```

Seed-repair probe:

```text
runs/m1758_single_sampling_failure_reset_only_probe/probe_rows.csv
```

Metadata scenario specs:

```text
runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_specs.json
```

Executable scenario specs:

```text
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json
```

Workload matrix:

```text
runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_matrix.csv
```

Unsupported-feature boundary:

```text
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/unsupported_scenario_features.csv
```

Completion output directory for the later execution:

```text
runs/m1764_revised_scenario_taxonomy_single_seed_completion
```

## Fixed Seed Repair

```text
workload_id: m1728-s4-02::L2_window_13_current_tiled
scenario_spec_id: m1728-s4-02
profile_name: L2_window_13_current_tiled
original_eval_seed: 175761
replacement_eval_seed: 175760
replacement_seed_offset: -1
expected_sampled_obstacle_label: unavoidable
seed_repair_rule: nearest_successful_neighbor_tie_lower
seed_repair_source: m1758_single_sampling_failure_reset_only_probe
```

## Required CLI Implementation

M1763 should implement:

```text
python -m autodrift.seed_repair_completion_execution
```

The CLI should:

- read M1756 source rows and validate `863` completed rows plus exactly one
  failure row;
- select/validate the M1760 seed repair plan from M1758 probe rows;
- reconstruct the single workload row from M1743 metadata and M1734 executable
  specs;
- load only the required `L2_window_13_current_tiled` checkpoint/config;
- run only the missing workload cell at replacement seed `175760`;
- call the M1761 helper to write a fresh completion output directory;
- preserve seed-repair provenance and original failure diagnostics;
- recompute summary, metric completeness, and aggregates from the completed
  rows.

The CLI must not mutate M1756 artifacts in place.

## Later Execution Command

After M1763 implements and validates the CLI, M1764 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.seed_repair_completion_execution \
  --output-dir runs/m1764_revised_scenario_taxonomy_single_seed_completion \
  --source-run-dir runs/m1756_revised_scenario_taxonomy_execution_after_wrapper_repair \
  --probe-rows runs/m1758_single_sampling_failure_reset_only_probe/probe_rows.csv \
  --scenario-specs runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_specs.json \
  --executable-scenario-specs runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json \
  --workload runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_matrix.csv \
  --unsupported-features runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/unsupported_scenario_features.csv \
  --workload-id m1728-s4-02::L2_window_13_current_tiled \
  --original-eval-seed 175761 \
  --replacement-eval-seed 175760 \
  --expected-sampled-obstacle-label unavoidable \
  --device cpu \
  --next-blocker m1765-single-cell-seed-repair-completion-result-audit
```

## Completion Pass Gate

The later M1764 execution passes only if:

- source completed rows are `863`;
- source failure rows are `1`;
- final completed rows are `864`;
- final failure rows are `0`;
- exactly one final row has `seed_repair_applied=true`;
- that row is `m1728-s4-02::L2_window_13_current_tiled`;
- replacement seed is `175760`;
- sampled obstacle label is `unavoidable`;
- metric completeness passes;
- guardrail violation count is `0`;
- actor inputs, reward, dynamics, termination behavior, profile configs, and
  scenario specs are unchanged;
- no controller-family ranking, private-holdout, paper-level, or level3 self-ID
  claim is made.

## Guardrails

- policy rollout started: `false`
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

## Decision

Admit M1763 seed-repair completion execution CLI implementation. M1763 should
add the minimal CLI and focused tests only; the one-cell policy execution remains
blocked until M1764.
