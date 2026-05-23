# M345 Old-Key Neighborhood Replay Gate Adapter

M345 makes the old-key neighborhood gate candidate-level. It does not run PPO,
repair, promote, or change actor inputs.

## Problem

M342/M343 validated the M341 old-key neighborhood surface, but the first gate
read saved audit columns:

```text
selected_*
endpoint_*
```

That was enough to prove the surface distinguishes M335 alpha from the repaired
endpoint, but not enough to evaluate arbitrary future PPO candidates.

## Implementation

New module:

```text
src/autodrift/old_key_neighborhood_replay_gate.py
```

Focused tests:

```text
tests/test_old_key_neighborhood_replay_gate.py
```

The adapter reads replay `guard_results.csv` rows, filters them to the M341
compact corpus, and compares:

```text
baseline policy
candidate policy
```

It computes candidate-level old-key metrics:

```text
candidate accepted regressions
candidate normal-success regressions
candidate gap mean / p10 / min
candidate gate pass / failure reasons
candidate repair-needed reasons
source-diversity metrics
M133 / 9944 diagnostic visibility
```

This means future checkpoints can be evaluated once replay rows exist. The gate
no longer depends on static `selected_*` / `endpoint_*` columns.

## Smoke: M335 Alpha

Command:

```bash
PYTHONPATH=src python -m autodrift.old_key_neighborhood_replay_gate \
  --compact-corpus-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv \
  --infer-guard-results-from-compact \
  --candidate-pool-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv \
  --baseline-policy m335_a0075 \
  --candidate-policy m335_a0075 \
  --run-dir runs/m345_old_key_neighborhood_replay_gate_alpha
```

Result:

```text
overall_pass: true
candidate_gate_pass: true
candidate_repair_needed: false
failure_types: none
```

Compact candidate metrics:

```text
rows: 40
seed blocks: 5
physical pairs or keys: 40
source steps: 19
target buckets: 28
max seed-block dominance: 0.25
max physical-pair dominance: 0.025
candidate accepted regressions: 0
candidate normal-success regressions: 0
candidate gap p10: 0.0
candidate gap min: 0.0
```

The zero gap deltas are expected because this smoke compares `m335_a0075`
against itself. It verifies schema coverage and pass-threshold aggregation.

## Smoke: M335 Repaired Endpoint

Command:

```bash
PYTHONPATH=src python -m autodrift.old_key_neighborhood_replay_gate \
  --compact-corpus-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv \
  --infer-guard-results-from-compact \
  --candidate-pool-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv \
  --baseline-policy m335_a0075 \
  --candidate-policy m335_repaired \
  --run-dir runs/m345_old_key_neighborhood_replay_gate_repaired
```

Result:

```text
overall_pass: false
candidate_gate_pass: false
candidate_repair_needed: true
failure_types: protected_key_window_failure
```

Compact candidate metrics:

```text
candidate accepted regressions: 15
candidate normal-success regressions: 3
candidate gap mean: -0.0021984656
candidate gap p10: -0.0040401765
candidate gap min: -0.0506202397
```

Failure reasons:

```text
candidate_accepted_regressions>0
candidate_gap_p10<-0.0005
candidate_gap_min<-0.002
```

Repair-needed reasons:

```text
candidate_accepted_regressions>=2
candidate_gap_p10<=-0.001
candidate_gap_min<=-0.01
```

## Diagnostic Visibility

Both smoke runs include the M341 candidate pool diagnostic summary:

```text
M133 diagnostic rows: 12
old_key_9944_included: true
```

The adapter keeps `9944` visible while replacing singleton-veto dominance with
distributional old-key evidence.

## Tests

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_old_key_neighborhood_replay_gate.py \
  tests/test_old_key_neighborhood_gate.py
```

Result:

```text
11 passed
```

The tests cover candidate deltas, pass aggregation, fail / repair-needed
aggregation, summary artifact writing, missing-diagnostic failure, and
`source_csv` inference.

## Decision

M345 passes. The old-key neighborhood gate is now usable as a candidate-level
adapter once replay `guard_results.csv` rows exist.

Decision:

```text
admit_m346_old_key_neighborhood_alpha_sweep_design
```

M346 should design a no-PPO alpha sweep over the M335 interpolation family using
the replayable old-key neighborhood gate. The immediate question is whether the
distributional old-key gate permits a larger accepted movement than the old
singleton `9944` floor did, while still rejecting the repaired endpoint.
