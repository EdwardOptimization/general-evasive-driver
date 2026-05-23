# M376 M374 Alpha02 Cumulative Old-Key Boundary Audit

M376 audits the first tested cumulative old-key failure beyond the newly
promoted M375 base. It does not run PPO, promote alpha `0.2`, lower thresholds,
or change actor inputs.

## Inputs

Current promoted base:

```text
runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
```

First tested failing candidate:

```text
runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_2.pt
```

Old-key gate:

```text
runs/m374_gap_tail_final_interp_a020_cumulative_old_key_replay_gate
```

## Gate Result

Alpha `0.2` fails the cumulative old-key compact gate:

| Metric | Value |
| --- | ---: |
| accepted regressions | 0 |
| normal-success regressions | 0 |
| candidate gap mean | -0.000093679 |
| candidate gap p10 | -0.000526953 |
| candidate gap min | -0.001119853 |
| rows with gap delta <= -0.0005 | 4 |
| rows with gap delta <= -0.001 | 1 |

This is not accepted-regression washout. It is lower-tail margin-gap erosion.

## Worst Rows

| Case | Gap delta | Normal delta | Wrong delta |
| --- | ---: | ---: | ---: |
| `10033|perturbed|29|23|9.500000|-1.200000|0.700000` | -0.001119853 | -0.000912755 | +0.000207098 |
| `9982|perturbed|45|39|9.500000|-1.200000|0.700000` | -0.000873140 | -0.001203350 | -0.000330210 |
| `10033|perturbed|26|23|9.500000|-1.200000|0.700000` | -0.000862490 | -0.001218420 | -0.000355930 |
| `10033|perturbed|26|23|9.500000|-1.200000|0.800000` | -0.000835770 | -0.001261750 | -0.000425980 |
| `9907|perturbed|27|18|10.500000|-1.200000|0.700000` | -0.000493160 | -0.000209140 | +0.000284020 |

Artifacts:

```text
runs/m376_alpha02_cumulative_old_key_boundary_audit/worst_gap_rows.csv
runs/m376_alpha02_cumulative_old_key_boundary_audit/gap_tail_rows.csv
runs/m376_alpha02_cumulative_old_key_boundary_audit/summary.json
```

## Interpretation

Alpha `0.2` is close to the M375 promoted base, but it is already outside the
cumulative old-key lower-tail floor. The failure is source-local and
gap-distribution based, not a broad proof surface washout.

The row-level pattern has two contributors:

- several rows lose normal-history margin more quickly than wrong-history
  margin;
- the worst row also makes wrong history slightly safer, shrinking the proof
  gap from both sides.

This matches the M372/M373 feedback model. The next step should refresh the
gap-tail overlay/corpus for the current M375 family, using the alpha `0.2`
boundary rows as training-time repair metadata. Do not lower the `-0.0005`
gap-p10 floor.

## Decision

Admit:

```text
m377-cumulative-gap-tail-v2-corpus-refresh
```

Decision:

```text
admit_m377_cumulative_gap_tail_v2_corpus_refresh
```
