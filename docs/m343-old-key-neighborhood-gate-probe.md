# M343 Old-Key Neighborhood Gate Probe

M343 formally runs the M342 old-key neighborhood gate on the M341 corpus. It is
a proof-gate probe only: no PPO, no actor update, no checkpoint repair, no
promotion, and no actor-input change.

## Command

```bash
PYTHONPATH=src python -m autodrift.old_key_neighborhood_gate \
  --candidate-pool-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv \
  --compact-corpus-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv \
  --run-dir runs/m343_old_key_neighborhood_gate_probe \
  --pass-decision admit_m344_old_key_neighborhood_policy_integration_design
```

## Result

```text
overall_pass: true
replacement_gate_ready: true
selected_alpha_passes: true
endpoint_repair_needed: true
failure_types: none
```

The run artifact is:

```text
runs/m343_old_key_neighborhood_gate_probe/summary.json
```

## Broad Pool

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

## Compact Corpus

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

## Diagnostic Visibility

The M133 diagnostic block remains visible:

```text
diagnostic rows: 12
old_key_9944_included: true
```

This matters because the new gate is meant to remove singleton-veto dominance,
not hide the historical `9944|perturbed|28|28` diagnostic row.

## Interpretation

The formal probe confirms the replacement surface from M341 is usable as a
gate:

- the promoted M335 alpha `0.0075` passes broad and compact source-diverse
  thresholds;
- the repaired endpoint is still rejected by distributional old-key evidence;
- the old `9944` row remains a diagnostic signal;
- no actor contract or checkpoint changed.

## Decision

M343 passes.

Decision:

```text
admit_m344_old_key_neighborhood_policy_integration_design
```

M344 should define how this old-key neighborhood gate enters the acceptance
stack and how the old singleton `9944` floor is handled going forward.
