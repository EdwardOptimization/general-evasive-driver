# M1442 Paper-Route Geometry-First Action-Divergence Enrichment Implementation

## Summary

M1442 implements source-step action-divergence enrichment after trace-backed
source geometry materialization.

Decision:

```text
geometry_first_action_divergence_enrichment_implemented_admit_public_source_pipeline_smoke
```

M1442 does not run public source materialization, source enrichment, source
preflight, bounded replay, outcome interventions, training, PPO, promotion,
private holdout, corpus export, or actor-input changes.

## Implementation

Added:

```text
src/autodrift/source_action_divergence_enrichment.py
tests/test_source_action_divergence_enrichment.py
```

Updated:

```text
src/autodrift/trace_source_geometry_materializer.py
```

The materializer update adds checkpoint/config-backed execution support so the
next smoke can generate source geometry rows before enrichment. No public
materialization run occurred in M1442.

Implemented source-step enrichment functions:

```text
prepare_source_geometry_frame
trace_prefix_to_step
build_source_step_variant_hiddens
evaluate_source_step_variant_actions
enrich_source_geometry_row
enrich_source_geometry_rows
select_enriched_source_rows
build_enrichment_summary
write_enrichment_outputs
run_source_action_divergence_enrichment_from_rows
run_source_action_divergence_enrichment
```

## Enrichment Semantics

The implemented ordering is:

```text
trace-backed source geometry
  -> source-step variant hidden construction
  -> action-distance enrichment
  -> selected M1438-compatible rows
```

Every enriched row uses:

```text
variant_time_anchor: source_step
```

The implementation computes first-action and short-sequence action-distance
metrics only:

```text
first_action_l2
first_steer_delta
first_throttle_delta
first_brake_delta
sequence_action_l2_mean
sequence_action_l2_max
sequence_action_l2_rms
sequence_steps
```

It does not classify success, collision, clearance margin, obstacle completion,
terminal reason, or history-positive outcome. Those remain bounded replay
questions.

## Variant Coverage

Implemented variants:

```text
normal
reset_hidden
zero_current_response
delayed_warmup_history_8
delayed_warmup_history_16
wrong_warmup_history_same_reveal
same_recent_wrong_warmup_history
warmup_removed
warmup_shortened_8
```

Rows selected for M1438-compatible downstream use must satisfy:

```text
history_variant == true
action_divergent == true
source_body_x >= 4.0
```

Default divergence thresholds:

```text
min_sequence_action_l2: 0.025
min_first_action_l2: 0.014
```

## Tests

Focused tests cover:

```text
source geometry row schema validation
source-step variant hidden construction
first-action and sequence action-distance metrics
source-step variant row enrichment
M1438-compatible selected row schema
artifact writing
guardrail flags
```

Focused result:

```text
tests/test_source_action_divergence_enrichment.py: 7 passed
tests/test_trace_source_geometry_materializer.py + tests/test_source_action_divergence_enrichment.py: 14 passed
```

## Guardrails

M1442 guardrail status:

```text
source_materialization_run_started: false
source_enrichment_run_started: false
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
m1443-paper-route-geometry-first-source-pipeline-smoke
```

M1443 should run a public, no-training source pipeline smoke:

```text
M1419 matched/bucketed source rows
  -> trace-backed source geometry materialization
  -> source-step action-divergence enrichment
```

It must not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.
