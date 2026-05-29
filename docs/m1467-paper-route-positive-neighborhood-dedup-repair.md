# M1467 Paper-Route Positive Neighborhood Dedup Repair

## Summary

M1467 repairs the M1465 duplicate-key metric artifact.

Decision:

```text
positive_neighborhood_dedup_repair_implemented_admit_rerun
```

M1467 does not run source preflight, bounded replay, training, PPO, promotion,
private holdout, corpus export, or actor-input changes.

## Implementation

Changed:

```text
src/autodrift/positive_neighborhood_expansion.py
tests/test_positive_neighborhood_expansion.py
```

Repair:

```text
select_positive_neighborhood_candidates now skips duplicate
positive_neighborhood_key values before applying selection caps.
```

The summary now reports:

```text
selected_unique_positive_neighborhood_keys
selected_duplicate_positive_neighborhood_key_rows
```

## Tests

Focused command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_positive_neighborhood_expansion.py tests/test_research_validate.py
```

Result:

```text
31 passed in 0.99s
```

Covered repair behavior:

```text
duplicate candidate-pool rows no longer create duplicate selected keys
selected positive_neighborhood_key count equals selected row count
source_step preservation and control separation remain covered
```

## Guardrails

M1467 guardrail status:

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
m1468-paper-route-positive-neighborhood-dedup-smoke
```

M1468 should rerun the proposal smoke and verify that selected duplicate keys
are zero before any preflight or replay.
