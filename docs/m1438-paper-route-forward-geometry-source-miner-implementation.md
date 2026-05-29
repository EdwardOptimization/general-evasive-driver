# M1438 Paper-Route Forward Geometry Source Miner Implementation

## Summary

M1438 implements the row-level forward-geometry source miner foundation.

Decision:

```text
forward_geometry_source_miner_row_level_implemented_route_to_trace_materialization_design
```

M1438 does not run source mining, source preflight, bounded replay, outcome
interventions, training, PPO, promotion, private holdout, corpus export, or
actor-input changes.

## Implementation

Added:

```text
src/autodrift/forward_geometry_source_miner.py
tests/test_forward_geometry_source_miner.py
```

Implemented:

```text
source_steps_for_reveal
validate_forward_longitudinal_offsets
forward_relocation_grid
prepare_source_geometry_frame
expand_forward_geometry_sources
select_forward_geometry_source_rows
build_forward_geometry_source_summary
run_forward_geometry_source_miner_from_rows
```

The implementation enforces geometry-first ordering for precomputed
source-geometry rows:

```text
source geometry -> forward relocation geometry -> selection
```

It does not reconstruct traces yet. That boundary is intentional: source
geometry materialization must be designed separately before a real source smoke.

## Guarded Behavior

The miner rejects negative longitudinal offsets:

```text
validate_forward_longitudinal_offsets((-1.0, 0.0)) -> ValueError
```

The miner applies source geometry gates before selection:

```text
source_body_x >= 4.0
raw_relocated_body_x >= 4.0
relocation_body_x_clipped == false
history_variant == true
sequence_action_l2_mean >= 0.025
```

The selector caps:

```text
per seed
per capability pair
per reveal bucket
per history variant
```

## Tests

Focused tests cover:

```text
source-step offset generation
negative longitudinal offset rejection
geometry-first rejection
history/control filtering
seed and variant caps
summary guardrail flags
artifact writing
```

Focused result:

```text
tests/test_forward_geometry_source_miner.py: 6 passed
```

## Boundary

This is not yet a full public source smoke. The current implementation consumes
rows that already contain:

```text
source_body_x
source_body_y
source_half_width
source_step
reveal_step
```

The next step must design trace-backed materialization of those fields from the
checkpoint/config/source-step offsets. Do not run a public source smoke until
that materialization path is explicit.

## Guardrails

M1438 guardrail status:

```text
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
m1439-paper-route-trace-backed-source-geometry-materialization-design
```

M1439 should design how to materialize source-geometry rows from traces at
earlier source steps before any public source-mining smoke.
