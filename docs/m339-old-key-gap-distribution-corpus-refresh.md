# M339 Old-Key Gap Distribution Corpus Refresh

M339 is a no-PPO corpus refresh for the old-key gap bottleneck. It does not
train, repair, promote, or change actor inputs.

## Commands

Endpoint replay scans were run before this document was written:

```text
runs/m339_endpoint_replay_scan/*
runs/m337_m335_repaired_endpoint_source_diverse_gate
```

M339 also replayed every M133 protected case instead of only `9944`:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.critical_key_replay_guard \
  --reference-manifest runs/m133_zero_relvel_s60_strict_60ep_seed9900/manifest.json \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv \
  --checkpoint-policy m333_base=runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt \
  --checkpoint-policy m335_a0075=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt \
  --checkpoint-policy m335_repaired=runs/m335_exact_repair_from_raw_s40_seed10099/candidate_checkpoint.pt \
  --reference-policy m333_base \
  --device cpu \
  --run-dir runs/m339_m133_all_old_key_guard
```

Aggregation artifacts:

```text
runs/m339_old_key_gap_distribution_refresh/old_key_gap_candidate_pool.csv
runs/m339_old_key_gap_distribution_refresh/old_key_gap_compact_corpus.csv
runs/m339_old_key_gap_distribution_refresh/summary.json
```

## Broad Pool

The broad pool is large enough for an audit:

| Metric | Value |
| --- | ---: |
| Rows | 195 |
| Source families | 12 |
| Physical pairs or protected keys | 30 |
| Source steps | 19 |
| Target buckets | 116 |
| Max source-family dominance | 0.087179 |

The broad pool passes the M338 minimums.

## Compact Draft

The severity compact draft includes rows with old-key diagnostics, M133
historical protected cases, endpoint gap regression, endpoint accepted-case
regression, or endpoint success-drop regression.

| Metric | Value |
| --- | ---: |
| Rows | 26 |
| Source families | 4 |
| Physical pairs or protected keys | 19 |
| Source steps | 15 |
| Target buckets | 19 |
| Max source-family dominance | 0.461538 |

The compact draft has enough rows, pairs, steps, and target buckets, but it
fails the `<= 0.25` source-dominance requirement. The dominant source is the
M133 all-key protected-case guard (`12 / 26` rows). The remaining severity rows
come mostly from duplicated M183 surfaces plus two M267/M264 success-drop
regressions.

Therefore this draft is useful diagnostic evidence, but it is not a valid
source-diverse replacement for the singleton `9944` floor.

## Endpoint Diagnostics

M335 repaired endpoint versus M333 base:

| Diagnostic | Value |
| --- | ---: |
| Mean gap delta | 0.000161 |
| Min gap delta | -0.024795 |
| Gap-regression rows `< 0` | 23 |
| Gap-regression rows `<= -0.001` | 3 |
| Success-drop regressions | 2 |
| M133 accepted-case regressions | 1 |

The endpoint is distinguishable, but not through a source-diverse old-gap
distribution yet.

The historical `9944|perturbed|28|28` row remains the strongest single
diagnostic:

| Policy | Margin gap |
| --- | ---: |
| M333 base | 0.090155 |
| M335 alpha 0.0075 | 0.090021 |
| M335 repaired endpoint | 0.065360 |

Endpoint gap delta on `9944`:

```text
-0.02479489280545555
```

## Interpretation

M339 does not support replacing the old singleton floor yet.

The evidence says:

```text
existing broad pool is adequate for inspection
severity compact draft is too source dominated for a new gate
M335 endpoint is unsafe or repair-needed under old-key/M133 diagnostics
M335 alpha 0.0075 remains the correct current public base
9944 floor must stay active until a wider neighborhood corpus exists
```

This is classified as:

```text
lineage_invalid
```

More specifically, the existing corpora are insufficient lineage for a
source-diverse old-key/gap replacement gate.

## Decision

Do not run more PPO from this state.

Do not lower the `9944` gap floor ad hoc.

Admit:

```text
m340-old-key-neighborhood-mining-design
```

M340 should design a wider old-key neighborhood mining stage that can find
less dominated old-gap rows around M133 and `9944`-like cases before any gate
replacement or PPO continuation.
