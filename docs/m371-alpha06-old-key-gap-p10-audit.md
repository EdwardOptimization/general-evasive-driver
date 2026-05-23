# M371 Alpha06 Old-Key Gap-P10 Audit

M371 audits the first tested old-key gate failure after the M370 promotion. It
does not run PPO, promote alpha `0.6`, lower thresholds, or change actor inputs.

## Inputs

Promoted candidate:

```text
runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
```

First tested failure:

```text
runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_6.pt
```

Replay artifacts:

```text
runs/m369_hard_row_interpolation_old_key_targeted_replay/guard_results.csv
runs/m369_hard_row_interp_a600_old_key_replay_gate/summary.json
```

Audit output:

```text
runs/m371_alpha06_gap_audit/alpha04_alpha06_gap_audit_rows.csv
runs/m371_alpha06_gap_audit/summary_table.csv
```

## Gate Summary

Alpha `0.6` does not fail by accepted regressions:

```text
accepted rows: 40 / 40
normal-success rows: 40 / 40
candidate accepted regressions: 0
candidate normal-success regressions: 0
candidate gap p10: -0.000573217
failure: candidate_gap_p10<-0.0005
```

Comparison to promoted alpha `0.4`:

| Policy | Accepted | Normal success | Gap mean delta | Gap p10 delta | Gap min delta | Rows below -0.0005 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| m369hr_a400 | 40 / 40 | 40 / 40 | -0.000065 | -0.000380 | -0.000796 | 4 |
| m369hr_a600 | 40 / 40 | 40 / 40 | -0.000099 | -0.000573 | -0.001193 | 5 |

The gate fails because the lower tail of margin-gap deltas shifts further
negative, not because the candidate loses normal success or wrong-history
success-drop structure.

## Worst Alpha 0.6 Rows

| Case | Normal delta | Wrong-history delta | Gap delta |
| --- | ---: | ---: | ---: |
| 10033\|perturbed\|29\|23\|9.500000\|-1.200000\|0.700000 | -0.000812 | +0.000381 | -0.001193 |
| 9982\|perturbed\|45\|39\|9.500000\|-1.200000\|0.700000 | -0.001138 | -0.000202 | -0.000936 |
| 10033\|perturbed\|26\|23\|9.500000\|-1.200000\|0.700000 | -0.001146 | -0.000221 | -0.000925 |
| 10033\|perturbed\|26\|23\|9.500000\|-1.200000\|0.800000 | -0.001196 | -0.000298 | -0.000898 |
| 9907\|perturbed\|27\|18\|10.500000\|-1.200000\|0.700000 | -0.000162 | +0.000375 | -0.000537 |

The first four rows were already below `-0.0005` under alpha `0.4`, but the
compact p10 still passed. Alpha `0.6` adds the `9907` row below `-0.0005` and
pushes the lower tail enough to fail p10.

## Interpretation

This is a distributional old-key gap erosion, not a hard-row accepted
regression:

- alpha `0.6` keeps all 40 compact rows accepted;
- normal success is retained on all 40 rows;
- wrong-history success-drop structure is retained;
- the failing signal is the compact old-key gap lower tail;
- the degradation is concentrated in a small set of rows, dominated by seed
  `10033`, but it is not a single-row sign crossing like M366.

The next repair should not add more pressure only to the M366 hard row. It needs
a gap-distribution retention design that can constrain the lower tail of the
old-key compact distribution while still allowing the exact repair direction to
move.

## Decision

Do not promote alpha `0.6`.

Do not lower the old-key gap-p10 rule.

Admit:

```text
m372-old-key-gap-distribution-retention-design
```

Decision:

```text
admit_m372_old_key_gap_distribution_retention_design
```
