# M374 Gap-Tail Weighted Repair Probe

M374 probes the M373 hard-row plus gap-tail weighted old-key repair path. It is
a no-PPO proof-gate milestone and does not promote a checkpoint.

## Inputs

Current public-gate base:

```text
runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
```

Known alpha `0.6` old-key lower-tail failure:

```text
runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_6.pt
```

M373 weighted old-key corpus:

```text
runs/m373_old_key_preference_corpus_gap_tail/old_key_preference_corpus.npz
```

## Exact Repair

The first exact repair run used `best_feasible` selection from alpha `0.6`.
Because the parameter trust term made the start point the best total-loss
feasible row, it selected step `0`. That candidate is effectively alpha `0.6`.

Result versus M370 base:

| Metric | Value |
| --- | ---: |
| selected step | 0 |
| exact M297 delta | -0.000068545 |
| exact M270 delta | -0.000033081 |
| old-key surrogate delta | -0.004263401 |
| exact lexicographic pass | true |

Run dir:

```text
runs/m374_gap_tail_weighted_repair_from_alpha06_s40_seed10110
```

To test whether the gap-tail update direction itself contains useful signal,
M374 also ran the same no-PPO repair with `selection-policy final`.

Final repair result versus M370 base:

| Metric | Value |
| --- | ---: |
| selected step | 40 |
| exact M297 delta | -0.000140786 |
| exact M270 delta | -0.000066221 |
| old-key surrogate delta | -0.031692505 |
| exact lexicographic pass | true |

Run dir:

```text
runs/m374_gap_tail_weighted_repair_final_from_alpha06_s40_seed10110
```

The final endpoint is too aggressive in closed loop, so M374 bounded it by
interpolating from the M370 base to the final repair endpoint.

## Old-Key Replay

The selected bounded candidate is:

```text
runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
```

Important distinction:

- relative to the current M370 base, raw alpha `0.6` passes the incremental
  old-key replay gate;
- relative to the cumulative M365 reference used by the original M369/M371
  old-key failure, raw alpha `0.6` still fails gap p10;
- therefore M374 uses the cumulative old-key gate to avoid accepting a stale
  failure by merely shifting the baseline.

Cumulative old-key interpolation sweep:

| Alpha toward final repair | Pass | Accepted regressions | Gap p10 | Gap min |
| ---: | --- | ---: | ---: | ---: |
| 0.000 | true | 0 | -0.000379703 | -0.000796145 |
| 0.025 | true | 0 | -0.000397898 | -0.000836727 |
| 0.050 | true | 0 | -0.000416075 | -0.000877116 |
| 0.100 | true | 0 | -0.000452864 | -0.000958016 |
| 0.200 | false | 0 | -0.000526953 | -0.001119853 |
| 0.400 | false | 0 | -0.000678013 | -0.001442987 |
| 0.600 | false | 1 | -0.000831539 | -0.001766536 |
| 0.800 | false | 2 | -0.000987458 | -0.002088374 |
| 1.000 | false | 2 | -0.001146751 | -0.002409362 |

Gate run for selected alpha `0.1`:

```text
runs/m374_gap_tail_final_interp_a010_cumulative_old_key_replay_gate
```

Selected result:

```text
overall_pass: true
candidate_accepted_regressions: 0
candidate_gap_p10: -0.000452864
candidate_gap_min: -0.000958016
```

## Exact Eval For Selected Candidate

Run dir:

```text
runs/m374_gap_tail_a010_exact_eval_vs_m370
```

Result:

| Objective | Delta vs M370 base | Pass |
| --- | ---: | --- |
| exact M297 | -0.000014186 | true |
| exact M270 | -0.000006795 | true |
| old-key surrogate | -0.003163815 | true |

## Source-Diverse Protected Gate

Run dir:

```text
runs/m374_gap_tail_a010_source_diverse_protected_gate
```

All five source-diverse protected replay gates pass.

| Replay gates passed | Replay gate count |
| ---: | ---: |
| 5 | 5 |

## First Replay Gates

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M170 | 17 | 17 / 17 | +0.000018281 | +0.000006612 | true |
| M267/M264 | 17 | 17 / 17 | +0.000014889 | +0.000006350 | true |

Run dirs:

```text
runs/m374_gap_tail_a010_m183_m170_first_replay
runs/m374_gap_tail_a010_m267_m264_first_replay
```

## Interpretation

M374 is positive as a proof-gate probe, but only after bounding the final
repair endpoint. The weighted exact objective has useful signal, yet the
unbounded final endpoint damages closed-loop old-key rows. The safe region is
small: alpha `0.1` toward the final repair passes the cumulative old-key gate,
while alpha `0.2` is the first tested failure.

This is not a promotion. It only says `m374gt_a010` is eligible for a full
public gate.

## Decision

Admit:

```text
m375-full-public-gate-for-m374-a010
```

Decision:

```text
admit_m375_full_public_gate_for_m374_a010
```
