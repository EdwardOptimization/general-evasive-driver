# M385 Old-Key Recovery Residual Repair Probe

M385 tests the M384 replay-selected local-action recovery residual in exact
repair before any PPO continuation. It does not promote a checkpoint, lower
old-key thresholds, change actor inputs, or change the direct
steer/throttle/brake output contract.

## Inputs

Current public-gate base:

```text
runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
```

Known cumulative old-key boundary:

```text
runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
```

M384 recovery corpus:

```text
runs/m384_old_key_local_recovery_targets/old_key_recovery_corpus.npz
```

Supporting exact objectives:

```text
runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz
```

## Direct Repair Endpoint

Run dir:

```text
runs/m385_old_key_recovery_repair_from_alpha01_s80_seed10122
```

The direct exact-repair endpoint improves all exact objectives:

| Metric | Delta vs M378 base |
| --- | ---: |
| exact M297 | -0.014961360 |
| exact M270 | -0.009343028 |
| old-key surrogate | -0.001996040 |

Recovery residual terms at the selected endpoint:

| Term | Value |
| --- | ---: |
| old-key recovery loss | 0.000957745 |
| preferred recovery loss | 0.000707257 |
| wrong-anchor loss | 0.000250488 |
| exact lexicographic pass | true |

Closed-loop cumulative old-key replay rejects the direct endpoint:

```text
runs/m385_old_key_recovery_replay_gate
```

| Metric | Value |
| --- | ---: |
| overall pass | false |
| accepted regressions | 10 |
| normal-success regressions | 3 |
| gap mean | -0.003078792 |
| gap p10 | -0.014791661 |
| gap min | -0.054187642 |

This is a proof-washout endpoint. Exact loss improvement is not sufficient for
closed-loop proof retention.

## Bounded Interpolation

M385 interpolated from the M378 base toward the exact-repair endpoint:

```text
runs/m385_recovery_repair_interpolation
```

The cumulative old-key replay gate alone permits alpha `0.01`; alpha `0.02`
is the first tested old-key failure:

| Alpha | Old-key pass | Accepted regressions | Gap p10 | Gap min |
| ---: | --- | ---: | ---: | ---: |
| 0.001 | true | 0 | -0.000000937 | -0.000112900 |
| 0.0025 | true | 0 | -0.000002398 | -0.000283784 |
| 0.005 | true | 0 | -0.000004773 | -0.000572526 |
| 0.010 | true | 0 | -0.000011227 | -0.001166343 |
| 0.020 | false | 0 | -0.000022510 | -0.002408282 |

But broader proof gates reject alpha `0.01`: source-diverse protected gates
pass and M183/M170 first replay passes, while M267/M264 first replay loses two
wrong-history success drops.

| Candidate | M267/M264 success drops | Gate |
| --- | ---: | --- |
| alpha 0.010 | 15 / 17 | fail |
| alpha 0.005 | 15 / 17 | fail |
| alpha 0.0025 | 16 / 17 | fail |
| alpha 0.001 | 16 / 17 | fail |

The failure is concentrated on M267/M264 row `15`, whose base wrong-history
terminal margin is only about `-0.000016`. Alpha `0.001` moves it to
`+0.000004`, so this direction is bounded by a current-family knife-edge row,
not by the cumulative old-key gate.

## Micro-Alpha Probe

M385 therefore generated a micro interpolation grid:

```text
runs/m385_recovery_repair_micro_interpolation
```

M267/M264 first replay results:

| Alpha | Success drops | Gate |
| ---: | ---: | --- |
| 0.0001 | 17 / 17 | pass |
| 0.00025 | 17 / 17 | pass |
| 0.0005 | 17 / 17 | pass |
| 0.00075 | 17 / 17 | pass |
| 0.001 | 16 / 17 | fail |

Selected proof-gate candidate:

```text
runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
```

Exact eval for the selected micro-alpha:

```text
runs/m385_micro_a0_00075_exact_eval_vs_m378
```

| Objective | Delta vs M378 base | Pass |
| --- | ---: | --- |
| exact M297 | -0.000011206 | true |
| exact M270 | -0.000006974 | true |
| old-key surrogate | -0.000010490 | true |
| old-key recovery loss | 0.002265145 | true |

## Proof Gates For Selected Candidate

Selected candidate:

```text
runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
```

| Gate | Result |
| --- | --- |
| cumulative old-key replay | pass |
| source-diverse protected gate | 5 / 5 pass |
| M183/M170 first replay | 17 / 17 success drops retained |
| M267/M264 first replay | 17 / 17 success drops retained |

Cumulative old-key replay:

```text
runs/m385_micro_a0_00075_old_key_replay_gate
```

| Metric | Value |
| --- | ---: |
| accepted regressions | 0 |
| normal-success regressions | 0 |
| gap mean | +0.000000493 |
| gap p10 | -0.000000720 |
| gap min | -0.000084587 |

First replay deltas:

| Surface | Normal margin delta | Margin gap delta | Gate |
| --- | ---: | ---: | --- |
| M183/M170 | +0.000014965 | -0.000000804 | pass |
| M267/M264 | +0.000014459 | -0.000000986 | pass |

## Interpretation

The M384 recovery residual has a real exact-objective signal, but its direct
endpoint and ordinary bounded alphas are too aggressive for the current-family
wrong-history proof surface. The binding row is M267/M264 row `15`, not the
cumulative old-key compact gate. The acceptable movement is therefore a
micro-step: alpha `0.00075` is the largest tested alpha that preserves exact
objectives, cumulative old-key replay, source-diverse protected replay, and
both first replay surfaces.

This remains proof-safe incremental progress, not meaningful driver behavior
improvement. M385 admits a full public gate for the selected micro-alpha before
any promotion or PPO continuation.

## Decision

Admit:

```text
m386-full-public-gate-for-m385-a00075
```

Decision:

```text
admit_m386_full_public_gate_for_m385_micro_a00075
```
