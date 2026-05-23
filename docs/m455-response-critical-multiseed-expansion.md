# M455 Response-Critical Multiseed Expansion

## Purpose

M455 expands the M454 response-critical corpus beyond one seed window. The goal
is to determine whether standalone recurrent-hidden or action-history
sensitivity remains sparse when the same robust challenge ablation diagnostic is
run over disjoint seed windows.

This is diagnostic only:

- no training;
- no checkpoint promotion;
- no actor input/output changes;
- no use of corpus labels as actor inputs.

## Seed Discipline

An initial local attempt used seed starts `9800`, `9900`, and `10000`. That is
not clean for 128-episode windows because the seed ranges overlap:

```text
9800-9927
9900-10027
10000-10127
```

Before committing M455 evidence, the benchmark was rerun with disjoint windows:

```text
9600-9727
9900-10027
10150-10277
```

Only the disjoint-window results are used below.

## Benchmark Runs

Additional M455 runs:

- `runs/m455_near_robust_ablation_seed9600`
- `runs/m455_late_robust_ablation_seed9600`
- `runs/m455_near_robust_ablation_seed10150`
- `runs/m455_late_robust_ablation_seed10150`

M452 seed `9900` runs are reused:

- `runs/m452_near_robust_ablation_seed9900`
- `runs/m452_late_robust_ablation_seed9900`

All six runs use 128 episodes and the same policy set:

```text
heuristic
m399_base
m399_reset
m399_zero_current
m399_zero_all
m399_noact
```

No sampling failures occurred.

## Aggregate Ablation Results

| run | policy | success | collision | mean margin | return |
| --- | --- | ---: | ---: | ---: | ---: |
| near_9600 | m399_base | `0.843750` | `0.148438` | `1.711719` | `70.868301` |
| near_9600 | m399_reset | `0.835938` | `0.148438` | `1.700255` | `68.884880` |
| near_9600 | m399_zero_current | `0.820312` | `0.148438` | `1.715139` | `68.263685` |
| near_9600 | m399_noact | `0.851562` | `0.140625` | `1.712200` | `71.392201` |
| near_9900 | m399_base | `0.906250` | `0.085938` | `2.149732` | `76.764253` |
| near_9900 | m399_reset | `0.882812` | `0.093750` | `2.119200` | `74.166128` |
| near_9900 | m399_zero_current | `0.859375` | `0.093750` | `2.148677` | `73.260145` |
| near_9900 | m399_noact | `0.906250` | `0.085938` | `2.149458` | `76.781216` |
| near_10150 | m399_base | `0.828125` | `0.164062` | `1.796428` | `70.864133` |
| near_10150 | m399_reset | `0.835938` | `0.148438` | `1.790591` | `69.808880` |
| near_10150 | m399_zero_current | `0.835938` | `0.148438` | `1.807557` | `70.028300` |
| near_10150 | m399_noact | `0.828125` | `0.164062` | `1.802345` | `70.809400` |
| late_9600 | m399_base | `0.703125` | `0.296875` | `1.474903` | `64.754414` |
| late_9600 | m399_reset | `0.703125` | `0.296875` | `1.466911` | `63.043605` |
| late_9600 | m399_zero_current | `0.703125` | `0.296875` | `1.474704` | `63.239503` |
| late_9600 | m399_noact | `0.703125` | `0.296875` | `1.473383` | `65.092105` |
| late_9900 | m399_base | `0.859375` | `0.140625` | `1.864845` | `76.240945` |
| late_9900 | m399_reset | `0.851562` | `0.148438` | `1.860257` | `74.143938` |
| late_9900 | m399_zero_current | `0.851562` | `0.148438` | `1.869915` | `74.178656` |
| late_9900 | m399_noact | `0.867188` | `0.132812` | `1.860293` | `76.920184` |
| late_10150 | m399_base | `0.734375` | `0.257812` | `1.553354` | `65.861129` |
| late_10150 | m399_reset | `0.726562` | `0.265625` | `1.540441` | `63.772064` |
| late_10150 | m399_zero_current | `0.726562` | `0.257812` | `1.548314` | `64.103944` |
| late_10150 | m399_noact | `0.734375` | `0.257812` | `1.556903` | `65.887110` |

Across the six disjoint source windows:

| policy | mean success |
| --- | ---: |
| m399_base | `0.812500` |
| m399_reset | `0.805990` |
| m399_zero_current | `0.799479` |
| m399_noact | `0.815104` |

The aggregate deltas remain small. `zero_current` is weakest on average, but
the gap from base is only about `1.30` percentage points.

## Combined Corpus Export

Command:

```bash
PYTHONPATH=src python -m autodrift.response_critical_ablation_corpus \
  --episodes-csv runs/m455_near_robust_ablation_seed9600/episodes.csv \
  --source-config near_robust_9600 \
  --track-width 8.2 \
  --episodes-csv runs/m455_late_robust_ablation_seed9600/episodes.csv \
  --source-config late_robust_9600 \
  --track-width 8.0 \
  --episodes-csv runs/m452_near_robust_ablation_seed9900/episodes.csv \
  --source-config near_robust_9900 \
  --track-width 8.2 \
  --episodes-csv runs/m452_late_robust_ablation_seed9900/episodes.csv \
  --source-config late_robust_9900 \
  --track-width 8.0 \
  --episodes-csv runs/m455_near_robust_ablation_seed10150/episodes.csv \
  --source-config near_robust_10150 \
  --track-width 8.2 \
  --episodes-csv runs/m455_late_robust_ablation_seed10150/episodes.csv \
  --source-config late_robust_10150 \
  --track-width 8.0 \
  --baseline-policy m399_base \
  --candidate-policy m399_reset \
  --candidate-policy m399_zero_current \
  --candidate-policy m399_zero_all \
  --candidate-policy m399_noact \
  --max-rows 160 \
  --max-rows-per-config 32 \
  --run-dir runs/m455_response_critical_multiseed_corpus
```

Run directory:

```text
runs/m455_response_critical_multiseed_corpus
```

Core counts:

| metric | value |
| --- | ---: |
| rows compared | `3072` |
| accepted rows | `1996` |
| compact rows | `96` |
| max config dominance | `0.208333` |
| max policy dominance | `0.250000` |
| max failure-class dominance | `0.333333` |
| max obstacle-label dominance | `0.333333` |

Selected compact rows by source:

| source config | rows |
| --- | ---: |
| late_robust_10150 | `18` |
| late_robust_9600 | `15` |
| late_robust_9900 | `11` |
| near_robust_10150 | `20` |
| near_robust_9600 | `14` |
| near_robust_9900 | `18` |

Selected compact rows by dependency class:

| dependency class | rows |
| --- | ---: |
| action_history_sensitive | `2` |
| mixed_dependency | `94` |

Selected compact rows by failure class:

| failure class | rows |
| --- | ---: |
| ablation_rescue | `7` |
| clearance_margin_shift | `32` |
| near_boundary_obstacle_margin | `30` |
| obstacle_collision_margin_crossing | `7` |
| road_boundary_failure | `20` |

Selected compact rows by divergence type:

| divergence type | rows |
| --- | ---: |
| beta_peak_delta | `10` |
| collision_flip | `14` |
| large_margin_delta | `78` |
| lateral_boundary_flip | `20` |
| lateral_peak_delta | `27` |
| margin_sign_flip | `14` |
| near_boundary_margin_delta | `43` |
| return_delta | `78` |
| success_flip | `34` |

Selected compact rows by label and mu:

| bucket | counts |
| --- | --- |
| obstacle label | `aes_feasible=32`, `drift_required=32`, `unavoidable=32` |
| mu bucket | `high=32`, `low=32`, `medium=32` |

## Interpretation

M455 strengthens the negative conclusion from M452/M454.

Positive:

- The robust challenge family is useful for finding boundary rows.
- The exporter produces a balanced corpus across source windows, policies,
  labels, and mu buckets.
- There are real high-value rows: `34` selected success flips, `14` collision
  flips, `14` margin sign flips, and `20` lateral-boundary flips.

Negative:

- Aggregate ablation deltas remain small.
- The selected compact corpus is dominated by `mixed_dependency`.
- Standalone recurrent-hidden evidence does not survive compact selection.
- Standalone action-history evidence remains tiny (`2` selected rows).

This means the current robust challenge distribution is useful as a boundary
corpus source, but it is still not a strong self-identification gate. It mostly
finds fragile states where several ablations change behavior together, not
states where recurrent command-response history is uniquely necessary.

Evidence quality:

```text
weak-to-moderate for self-identification;
moderate for boundary-corpus mining.
```

## Decision

M455 completes as a diagnostic gate and does not promote a checkpoint.

The next step should be task-family redesign, not training. The new task family
must create clearer history necessity, likely through pre-emergency warm-up,
hidden dynamics variation, matched-current state construction, or wrong-history
interventions.

Next blocker:

```text
m456-history-necessity-task-family-design
```
