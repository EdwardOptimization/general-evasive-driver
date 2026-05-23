# M380 M378 Alpha01 Cumulative Old-Key Boundary Audit

M380 audits the first tested cumulative old-key failure beyond the newly
promoted M379 base. It does not run PPO, promote alpha `0.1`, lower thresholds,
or change actor inputs.

## Inputs

Current promoted base:

```text
runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
```

First tested failing candidate:

```text
runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
```

Old-key gate:

```text
runs/m378_v2_final_interp_a010_cumulative_old_key_replay_gate
```

## Gate Result

Alpha `0.1` fails the cumulative old-key compact gate:

| Metric | Value |
| --- | ---: |
| accepted regressions | 0 |
| normal-success regressions | 0 |
| candidate gap mean | -0.000093591 |
| candidate gap p10 | -0.000523942 |
| candidate gap min | -0.001114611 |
| rows with gap delta <= -0.0005 | 4 |
| rows with gap delta <= -0.001 | 1 |

This is not accepted-regression washout. It is lower-tail margin-gap erosion.

## Worst Rows

| Case | Gap delta | Normal delta | Wrong delta |
| --- | ---: | ---: | ---: |
| `10033|perturbed|29|23|9.500000|-1.200000|0.700000` | -0.001114611 | -0.000918787 | +0.000195824 |
| `9982|perturbed|45|39|9.500000|-1.200000|0.700000` | -0.000877685 | -0.001222663 | -0.000344978 |
| `10033|perturbed|26|23|9.500000|-1.200000|0.700000` | -0.000856736 | -0.001221601 | -0.000364866 |
| `10033|perturbed|26|23|9.500000|-1.200000|0.800000` | -0.000830338 | -0.001264640 | -0.000434302 |
| `9907|perturbed|27|18|10.500000|-1.200000|0.700000` | -0.000489920 | -0.000210932 | +0.000278988 |

Artifacts:

```text
runs/m380_alpha01_cumulative_old_key_boundary_audit/worst_gap_rows.csv
runs/m380_alpha01_cumulative_old_key_boundary_audit/gap_tail_rows.csv
runs/m380_alpha01_cumulative_old_key_boundary_audit/summary.json
```

## Interpretation

Alpha `0.1` is outside the cumulative old-key lower-tail floor even though it
has zero accepted regressions and zero normal-success regressions. The pattern
is similar to M376: the lower tail is driven mainly by normal-history margin
erosion, with some rows also making wrong history slightly safer.

This is the second gap-tail boundary after adding branch-weight feedback. The
next step should not blindly add another v3 weight overlay. First audit whether
the exact old-key surrogate improvements are aligned with closed-loop old-key
replay tail metrics across the recent interpolation families. If alignment is
weak, the next repair objective should add terminal-margin or local-action
recovery residuals rather than only stronger branch weights.

## Decision

Admit:

```text
m381-old-key-surrogate-replay-alignment-audit
```

Decision:

```text
admit_m381_old_key_surrogate_replay_alignment_audit
```
