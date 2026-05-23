# M342 Old-Key Neighborhood Gate Implementation

M342 implements the reusable old-key neighborhood gate requested by M341. It is
an infrastructure milestone only: no PPO, no actor update, no checkpoint
promotion, and no actor-input contract change.

## Implemented Gate

New module:

```text
src/autodrift/old_key_neighborhood_gate.py
```

Focused tests:

```text
tests/test_old_key_neighborhood_gate.py
```

The gate reads the M341 CSV artifacts:

```text
runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv
runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv
```

It writes:

```text
summary.json
broad_metrics.csv
compact_metrics.csv
diagnostic_summary.csv
```

The gate does not load checkpoints. It recomputes the saved M341 surface
metrics from CSV and checks whether the selected candidate remains acceptable
while the repaired endpoint is still classified as needing repair.

## Gate Policy

Broad-pool diversity targets:

```text
rows >= 80
seed blocks >= 4
physical pairs or keys >= 20
source steps >= 8
target buckets >= 4
max seed-block dominance <= 0.25
```

Compact-corpus diversity targets:

```text
20 <= rows <= 40
seed blocks >= 4
physical pairs or keys >= 15
source steps >= 6
target buckets >= 4
max seed-block dominance <= 0.25
max physical-pair dominance <= 0.15
```

Selected-alpha thresholds:

```text
accepted regressions == 0
gap p10 >= -0.0005
gap min >= -0.002
```

Endpoint repair-needed triggers:

```text
accepted regressions >= 2
or gap p10 <= -0.001
or gap min <= -0.01
```

The historical M133 / `9944|perturbed|28|28` row remains visible as a
diagnostic. It is not hidden by the replacement gate.

## Smoke Command

```bash
PYTHONPATH=src python -m autodrift.old_key_neighborhood_gate \
  --candidate-pool-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv \
  --compact-corpus-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv \
  --run-dir runs/m342_old_key_neighborhood_gate
```

Result:

```text
overall_pass: true
replacement_gate_ready: true
selected_alpha_passes: true
endpoint_repair_needed: true
failure_types: none
```

## Reproduced Metrics

Broad pool:

| Metric | Value |
| --- | ---: |
| Rows | 179 |
| Seed blocks | 5 |
| Physical pairs or keys | 179 |
| Source steps | 32 |
| Target buckets | 76 |
| Max seed-block dominance | 0.234637 |
| Max physical-pair dominance | 0.005587 |
| Selected accepted regressions | 0 |
| Selected gap p10 | -0.0000037805 |
| Selected gap min | -0.0000489009 |
| Endpoint accepted regressions | 15 |
| Endpoint gap p10 | -0.0005322004 |
| Endpoint gap min | -0.0506599075 |

Compact corpus:

| Metric | Value |
| --- | ---: |
| Rows | 40 |
| Seed blocks | 5 |
| Physical pairs or keys | 40 |
| Source steps | 19 |
| Target buckets | 28 |
| Max seed-block dominance | 0.25 |
| Max physical-pair dominance | 0.025 |
| Selected accepted regressions | 0 |
| Selected gap p10 | -0.0000181822 |
| Selected gap min | -0.0000489009 |
| Endpoint accepted regressions | 15 |
| Endpoint gap p10 | -0.0040711523 |
| Endpoint gap min | -0.0506599075 |

Diagnostic visibility:

```text
M133 diagnostic rows: 12
old_key_9944_included: true
```

## Tests

Focused validation:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_old_key_neighborhood_gate.py
```

Result:

```text
5 passed
```

The tests cover diversity metrics, diagnostic visibility, pass summary output,
compact source-dominance failure, and selected-alpha regression failure.

## Decision

M342 passes. The M341 old-key neighborhood surface is now available as a
reusable gate.

Decision:

```text
admit_m343_old_key_neighborhood_gate_probe
```

M343 should run the new gate as a formal retrospective gate-probe milestone and
then decide how to integrate it into the acceptance stack so future PPO
continuations are no longer dominated by the singleton `9944` floor.
