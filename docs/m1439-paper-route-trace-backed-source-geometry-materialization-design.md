# M1439 Paper-Route Trace-Backed Source Geometry Materialization Design

## Summary

M1439 designs the missing materialization layer between the M1437 forward
geometry source-mining design and the M1438 row-level forward-geometry source
miner.

Decision:

```text
trace_backed_source_geometry_materialization_design_admit_implementation
```

M1439 does not run source mining, source preflight, bounded replay, outcome
interventions, training, PPO, promotion, private holdout, corpus export, or
actor-input changes.

## Problem

M1438 can filter and select rows that already contain:

```text
source_body_x
source_body_y
source_half_width
source_step
reveal_step
```

It intentionally does not reconstruct traces. M1435 showed that using the
M1425 pressure-row pool at reveal time is too late:

```text
source_body_x_max: 3.908281
raw_relocated_body_x_max: 3.495281
geometry_pass_rows: 0
```

The next layer must therefore reconstruct earlier source steps and materialize
the emergency obstacle geometry from simulator state, not infer it from stale
CSV fields.

## Source Inputs

Use source-family rows before M1425 pressure scoring, for example:

```text
runs/m1419_warmup_gate_invasiveness_retune_source_smoke/matched_or_bucketed_rows.csv
runs/m1419_warmup_gate_invasiveness_retune_source_smoke/warmup_reveal_rows.csv
```

Do not use M1425 `outcome_pressure_rows.csv` as the source pool for M1440.
Those rows are useful as a negative diagnostic, but the branch already showed
their reveal-time geometry is invalid for forward replay.

Required upstream columns:

```text
source_index
seed
reveal_step
preferred_fault
wrong_fault
capability_pair
preferred_reveal_bucket
wrong_reveal_bucket
matched_current_pass
bucketed_current_pass
```

Optional diagnostic columns can be carried through, but source-step action
evidence must not be fabricated from reveal-step metrics.

## Trace Reconstruction

For each upstream row:

```text
load checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
load scenario config: configs/m1419_warmup_gate_invasiveness_retune_source_wave.json
load env config through the scenario config
resolve preferred_fault and wrong_fault through fault_map_from_config
collect preferred and wrong traces to reveal_step
```

The source steps are generated from the reveal step:

```text
source_step_offsets_from_reveal:
  -32
  -24
  -16
  -8
  0
```

Clamped source steps should be deduplicated:

```text
source_steps = sorted(unique(max(0, reveal_step + offset)))
source_to_reveal_steps = reveal_step - source_step
```

The trace history length must be at least the largest source-to-reveal window.
For the first implementation, keep the existing `history_length=56` default
unless a manifest explicitly changes it.

## Geometry Definition

The canonical source geometry is the emergency obstacle geometry in the
preferred branch at the chosen source step:

```text
source_body_x
source_body_y
source_half_width
```

Implementation should compute it from a `TracePoint` by constructing an
`OutcomeSnapshot` and using the same emergency-obstacle helper already used by
bounded relocation replay:

```text
obstacle_body_geometry(OutcomeSnapshot(... preferred TracePoint ...))
```

Do not use `active_obstacle_body_x` as the canonical selector field. During
warmup, the active obstacle can be the warmup gate, while bounded relocation
replay relocates the emergency obstacle. Active-obstacle fields can be emitted
only as diagnostics.

The wrong-fault source geometry may be materialized for diagnostics:

```text
wrong_source_body_x
wrong_source_body_y
wrong_source_half_width
```

but the selector must use the preferred emergency obstacle geometry unless a
future manifest explicitly designs a paired-geometry objective.

## Output Schema

The materializer should write:

```text
source_geometry_rows.csv
rejected_rows.csv
source_step_summary.csv
source_diversity_summary.csv
summary.json
```

`source_geometry_rows.csv` must include:

```text
source_geometry_index
upstream_source_index
seed
reveal_step
source_step
source_to_reveal_steps
preferred_fault
preferred_fault_family
wrong_fault
wrong_fault_family
capability_pair
preferred_reveal_bucket
wrong_reveal_bucket
matched_current_pass
bucketed_current_pass
matched_or_bucketed_reveal_pass
source_body_x
source_body_y
source_half_width
wrong_source_body_x
wrong_source_body_y
wrong_source_half_width
preferred_active_obstacle_kind
preferred_active_obstacle_body_x
preferred_active_obstacle_body_y
preferred_active_obstacle_half_width
trace_reconstruction_status
geometry_materialization_status
```

`rejected_rows.csv` should include every upstream row or source step that cannot
be materialized, with:

```text
rejection_reason
error
seed
reveal_step
source_step
preferred_fault
wrong_fault
```

## Guardrail Checks

M1440 implementation tests should cover:

```text
source-step offset generation and clamping
emergency obstacle geometry extraction from TracePoint
active obstacle fields kept diagnostic-only
finite geometry rejection
source row schema validation
summary guardrail flags remain false
no source mining run, preflight, replay, training, PPO, promotion, private holdout, corpus export, or actor-input change
```

The materializer summary must include:

```text
source_materialization_started: false
source_preflight_started: false
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
```

For implementation-only milestones, `source_materialization_started` remains
false because no public run occurs. A later smoke can set it true.

## Relationship To M1438

M1440 should implement trace-backed geometry materialization only. It should
not immediately run M1438 selection, because M1438 selection also expects
history-variant and source-step action-divergence metadata:

```text
variant
sequence_action_l2_mean
matched_current_pass
bucketed_current_pass
```

After M1440, the branch still needs a geometry-first action-divergence
enrichment step before any public source smoke:

```text
trace-backed source geometry rows
  -> geometry-first action-divergence enrichment
  -> M1438 row-level forward-geometry miner
  -> source preflight smoke
  -> bounded replay
```

This avoids reusing reveal-step M1425 action metrics as if they were
source-step evidence.

## Next Route

Admit:

```text
m1440-paper-route-trace-backed-source-geometry-materialization-implementation
```

M1440 should implement the trace-backed materializer and focused tests only.
It must not run the materializer on public data, run source preflight, run
bounded replay, train, run PPO, promote, use private holdout, export a corpus,
or change actor inputs.
