# M378 Cumulative Gap-Tail V2 Repair Probe

M378 probes whether the refreshed M377 cumulative gap-tail v2 old-key corpus
can move beyond the M375 alpha `0.1` base without PPO. It does not promote a
checkpoint, lower old-key thresholds, or change actor inputs.

## Inputs

Current public-gate base:

```text
runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
```

Known M376 cumulative old-key boundary:

```text
runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_2.pt
```

M377 v2 old-key corpus:

```text
runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz
```

## Exact Repair

The first run used `best_feasible` selection from alpha `0.2`. It selected
step `0`, which confirms the alpha `0.2` starting point is exact-feasible but
does not create a new repair movement.

Run dir:

```text
runs/m378_v2_gap_tail_repair_from_alpha02_s40_seed10113
```

| Metric | Value |
| --- | ---: |
| selected step | 0 |
| exact M297 delta | -0.000014186 |
| exact M270 delta | -0.000006676 |
| old-key surrogate delta | -0.003332615 |
| exact lexicographic pass | true |

M378 therefore also ran the same no-PPO repair with `selection-policy final`.
The endpoint has stronger exact improvement, so the useful question becomes how
far toward that endpoint closed-loop old-key replay permits movement.

Run dir:

```text
runs/m378_v2_gap_tail_repair_final_from_alpha02_s40_seed10113
```

| Metric | Value |
| --- | ---: |
| selected step | 40 |
| exact M297 delta | -0.000128388 |
| exact M270 delta | -0.000060201 |
| old-key surrogate delta | -0.032300949 |
| exact lexicographic pass | true |

## Cumulative Old-Key Replay

M378 interpolated from the M375 base to the final repair endpoint:

```text
runs/m378_v2_gap_tail_final_interpolation
```

The cumulative old-key gate remains measured against the M365 reference, so
the test cannot pass merely because the local base shifted.

| Alpha toward final repair | Pass | Accepted regressions | Gap p10 | Gap min |
| ---: | --- | ---: | ---: | ---: |
| 0.000 | true | 0 | -0.000452864 | -0.000958016 |
| 0.025 | true | 0 | -0.000470559 | -0.000997122 |
| 0.050 | true | 0 | -0.000488253 | -0.001036272 |
| 0.100 | false | 0 | -0.000523942 | -0.001114611 |
| 0.200 | false | 0 | -0.000595965 | -0.001270601 |
| 0.400 | false | 0 | -0.000742483 | -0.001581976 |

Selected bounded candidate:

```text
runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
```

The first tested failure is alpha `0.1`, again by cumulative old-key lower-tail
erosion, not by accepted-regression loss.

## Exact Eval For Selected Candidate

Run dir:

```text
runs/m378_v2_a005_exact_eval_vs_m375
```

| Objective | Delta vs M375 base | Pass |
| --- | ---: | --- |
| exact M297 | -0.000006557 | true |
| exact M270 | -0.000003099 | true |
| old-key surrogate | -0.001610756 | true |

## Source-Diverse Protected Gate

Run dir:

```text
runs/m378_v2_a005_source_diverse_protected_gate
```

All five source-diverse protected replay gates pass.

| Replay gates passed | Replay gate count |
| ---: | ---: |
| 5 | 5 |

## First Replay Gates

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M170 | 17 | 17 / 17 | +0.000010214 | +0.000003361 | true |
| M267/M264 | 17 | 17 / 17 | +0.000008376 | +0.000003264 | true |

Run dirs:

```text
runs/m378_v2_a005_m183_m170_first_replay
runs/m378_v2_a005_m267_m264_first_replay
```

## Interpretation

M378 is a positive proof-gate probe. The M377 v2 corpus exposes a useful repair
direction, but closed-loop old-key replay still bounds acceptable motion:
alpha `0.05` passes, while alpha `0.1` is the first tested cumulative old-key
failure. This supports a full public gate for the bounded candidate, not direct
promotion.

## Decision

Admit:

```text
m379-full-public-gate-for-m378-a005
```

Decision:

```text
admit_m379_full_public_gate_for_m378_a005
```
