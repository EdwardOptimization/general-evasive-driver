# M1761 Seed-Repair Completion Runner Implementation

- status: completed
- decision: `admit_single_cell_completion_execution_design`
- no policy rollout: true
- training/replay/PPO: false

## Summary

M1761 implements the provenance layer needed before a one-cell seed-repair
completion execution. It does not run the missing policy episode and does not
merge M1756 rows. The implementation is a pure artifact helper for selecting the
pre-registered replacement seed, validating the single failure, augmenting rows
with seed-repair provenance, and writing a fresh completed-output directory once
a later milestone produces the repaired row.

## Implemented

New module:

```text
src/autodrift/seed_repair_completion.py
```

Main pieces:

- `SeedRepairPlan`
- `select_seed_repair_plan`
- `require_single_failure_row`
- `augment_episode_rows_with_seed_repair`
- `seed_repair_provenance_rows`
- `write_seed_repair_completion_outputs`
- `load_seed_repair_plan_from_probe_rows`

The default plan matches M1760:

```text
workload_id: m1728-s4-02::L2_window_13_current_tiled
original_eval_seed: 175761
replacement_eval_seed: 175760
replacement_seed_offset: -1
expected_sampled_obstacle_label: unavoidable
seed_repair_rule: nearest_successful_neighbor_tie_lower
seed_repair_source: m1758_single_sampling_failure_reset_only_probe
```

## Provenance Fields

The helper requires these fields on every completed episode row:

```text
seed_repair_applied
seed_repair_source
seed_repair_rule
original_eval_seed
replacement_eval_seed
replacement_seed_offset
original_failure_error_type
original_failure_error_message
original_workload_id
```

Copied M1756 rows receive `seed_repair_applied=false`; the repaired row receives
`seed_repair_applied=true` and the M1760 replacement-seed metadata.

## Validation

Focused tests:

```text
tests/test_seed_repair_completion.py
5 passed
```

Compile check:

```text
python -m compileall -q src tests
```

Covered behavior:

- nearest-successful-neighbor lower-seed tie-break selects `175760`;
- unexpected failure workload is rejected;
- copied rows receive blank/non-applied provenance;
- repaired row receives original failure and replacement seed provenance;
- wrong sampled label is rejected;
- standalone provenance rows preserve original failure error fields.

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

## Claim Boundary

Supported:

- seed-repair completion provenance helper exists;
- helper preserves the M1760 replacement-seed rule;
- helper can write fresh completion artifacts after a repaired row is produced.

Unsupported:

- missing-cell policy rollout;
- completed `864`-row matrix;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification evidence.

## Decision

Admit M1762 single-cell completion execution design. M1762 should pre-register
the exact one-row execution and helper invocation before any policy episode is
run.
