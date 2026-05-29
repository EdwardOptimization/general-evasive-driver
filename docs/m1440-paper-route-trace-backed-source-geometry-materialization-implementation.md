# M1440 Paper-Route Trace-Backed Source Geometry Materialization Implementation

## Summary

M1440 implements the trace-backed source geometry materializer designed in
M1439.

Decision:

```text
trace_backed_source_geometry_materializer_implemented_route_to_action_divergence_enrichment_design
```

M1440 does not run public source materialization, source mining, source
preflight, bounded replay, outcome interventions, training, PPO, promotion,
private holdout, corpus export, or actor-input changes.

## Implementation

Added:

```text
src/autodrift/trace_source_geometry_materializer.py
tests/test_trace_source_geometry_materializer.py
```

Implemented:

```text
prepare_reveal_source_frame
trace_point_to_outcome_snapshot
emergency_obstacle_geometry_from_trace_point
active_obstacle_diagnostics
trace_point_at_step
materialize_source_geometry_for_row
materialize_trace_source_geometry_from_rows
build_trace_source_geometry_summary
write_trace_source_geometry_outputs
run_trace_source_geometry_materializer_from_rows
```

The implementation computes canonical source geometry from the preferred
branch emergency obstacle:

```text
TracePoint -> OutcomeSnapshot -> obstacle_body_geometry
```

Active-obstacle fields are diagnostic-only. This matters because the active
obstacle can be the warmup gate, while bounded relocation replay relocates the
emergency obstacle.

## CLI Guard

The module exposes a guarded CLI parser, but M1440 does not implement public
checkpoint-backed execution:

```text
python -m autodrift.trace_source_geometry_materializer --source-rows ... --run-dir ... --no-run
```

Calling the module without `--no-run` exits with a message that execution must
wait for a later run milestone.

## Output Schema

Synthetic or later run outputs use:

```text
source_geometry_rows.csv
rejected_rows.csv
source_step_summary.csv
source_diversity_summary.csv
summary.json
```

Canonical output fields include:

```text
source_geometry_index
upstream_source_index
seed
reveal_step
source_step
source_step_offset
source_to_reveal_steps
preferred_fault
wrong_fault
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

## Tests

Focused tests cover:

```text
emergency obstacle geometry extraction from TracePoint
active-obstacle diagnostic-only behavior
source reveal schema validation
source-step offset materialization
missing trace-step rejection
trace callback integration
artifact writing
guardrail flags
```

Focused result:

```text
tests/test_trace_source_geometry_materializer.py: 7 passed
```

## Boundary

M1440 intentionally does not make the materialized rows directly usable as an
M1438 source-smoke input. Source-step action-divergence enrichment is still
missing. The next step must design how to compute:

```text
variant
sequence_action_l2_mean
first_action_l2
matched_current_pass / bucketed_current_pass at source-step context
```

after geometry passes, without reusing M1425 reveal-step pressure metrics as
source-step evidence.

## Guardrails

M1440 guardrail status:

```text
source_materialization_run_started: false
source_mining_started: false
source_preflight_started: false
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

Admit:

```text
m1441-paper-route-geometry-first-action-divergence-enrichment-design
```

M1441 should design source-step action-divergence enrichment after
trace-backed geometry materialization and before any public source smoke.
