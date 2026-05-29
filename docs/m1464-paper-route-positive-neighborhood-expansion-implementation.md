# M1464 Paper-Route Positive Neighborhood Expansion Implementation

## Summary

M1464 implements the no-training positive-neighborhood expansion generator
designed by M1463.

Decision:

```text
positive_neighborhood_expansion_generator_implemented_admit_proposal_smoke
```

M1464 does not run source preflight, bounded replay, training, PPO, promotion,
private holdout, corpus export, or actor-input changes.

## Implementation

Added:

```text
src/autodrift/positive_neighborhood_expansion.py
tests/test_positive_neighborhood_expansion.py
```

The generator consumes:

```text
history_positive_rows.csv
control_positive_rows.csv
candidate_pool.csv
```

and emits:

```text
positive_anchor_rows.csv
control_positive_source_rows.csv
positive_neighborhood_proposal_rows.csv
positive_neighborhood_candidate_rows.csv
summary.json
```

It:

```text
filters history-positive anchors so zero-current control positives cannot become anchors;
builds a local body-frame target grid around each positive anchor;
maps source-diverse candidate bases into that target neighborhood;
preserves source_step and candidate_step_column == source_step;
tags anchor_source, neighbor_source, and control_source proposals separately;
applies seed / capability-pair / anchor / variant caps during selection.
```

## Tests

Focused command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_positive_neighborhood_expansion.py tests/test_research_validate.py
```

Result:

```text
30 passed in 0.89s
```

Covered behavior:

```text
control positives are excluded from anchor rows
anchor target grid expands x / y / half-width locally
candidate_step_column and source_step are preserved
control-positive source diagnostics remain separate
selection caps enforce seed and capability-pair diversity
```

## Guardrails

M1464 guardrail status:

```text
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
m1465-paper-route-positive-neighborhood-expansion-smoke
```

M1465 should run the proposal generator only. It must not run source preflight,
bounded replay, training, PPO, promotion, private holdout, corpus export, or
actor-input changes.
