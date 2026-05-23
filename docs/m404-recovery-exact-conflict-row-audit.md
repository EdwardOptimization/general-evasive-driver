# M404 Recovery Exact-Conflict Row Audit

M404 attributes exact M297/M270 regressions under the recovery-heavy direction.
It does not run PPO, promote a checkpoint, lower thresholds, or change actor
inputs.

## Candidate

Base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Smallest recovery-heavy exact failure:

```text
runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_025.pt
```

This candidate already fails exact no-regression:

```text
exact M297 delta: +0.000015497
exact M270 delta: +0.000009298
old-key surrogate delta: -0.000042439
```

## Attribution Artifacts

```text
runs/m404_recovery_exact_conflict_row_audit/m297_row_deltas.csv
runs/m404_recovery_exact_conflict_row_audit/m270_row_deltas.csv
runs/m404_recovery_exact_conflict_row_audit/m297_positive_contributors.csv
runs/m404_recovery_exact_conflict_row_audit/m270_positive_contributors.csv
```

## M297

M297 row attribution:

```text
rows: 17
positive rows: 17
weighted loss delta: +0.000015497
positive contribution sum: +0.000015497
top-5 positive contribution sum: +0.000011415
```

Top positive contributors:

| Index | Row id | Weight | Delta | Weighted contribution |
| ---: | ---: | ---: | ---: | ---: |
| 6 | 6 | 0.327499 | +0.000020 | +0.000006403 |
| 15 | 15 | 0.138130 | +0.000012 | +0.000001696 |
| 11 | 11 | 0.056911 | +0.000029 | +0.000001628 |
| 3 | 3 | 0.024612 | +0.000035 | +0.000000863 |
| 2 | 2 | 0.024055 | +0.000034 | +0.000000826 |

M297 is broad-positive: every row regresses, although rows `6`, `15`, and `11`
carry most of the weighted contribution.

## M270

M270 row attribution:

```text
rows: 99
positive rows: 99
weighted loss delta: +0.000009298
positive contribution sum: +0.000009298
top-5 positive contribution sum: +0.000002034
```

M270 is even broader: every row regresses and the positive contribution is
distributed across the corpus. This is not a sparse exact-row conflict.

## Classification

The active blocker is:

```text
broad_exact_anchor_conflict_with_recovery_direction
```

Not:

```text
sparse_exact_row_conflict
single_bad_row
old_key_replay_first_failure
wrong_history_sensitivity_loss
actor_input_contract_issue
```

## Decision

Do not solve this by only hard-row reweighting. The recovery-heavy direction is
globally outside the current exact M297/M270 feasible tangent. The next task
should design a recovery-aware exact projection, where recovery movement is a
secondary merit objective under exact M297/M270 feasibility, instead of another
scalar weight sweep.

Admit:

```text
m405-recovery-aware-exact-projection-design
```
