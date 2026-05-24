# M596 BC Capability Corpus Export Smoke

## Purpose

M596 exports separate train and validation capability corpora using the M595
closed-loop BC5660 corpus runner.

This milestone is export-only:

```text
no repair training
no PPO
no route evaluation
no checkpoint promotion
```

## Commands

Train export:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_capability_corpus \
  --base-checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config configs/ppo_m541_matched_l3_variance_4096.json \
  --seeds 26000:26007 \
  --horizon-steps 8 \
  --sample-stride 4 \
  --nearest-k 16 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 80 \
  --max-visible-quantile 0.5 \
  --device cpu \
  --run-dir runs/m596_bc_capability_corpus_train_smoke
```

Validation export:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_capability_corpus \
  --base-checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config configs/ppo_m541_matched_l3_variance_4096.json \
  --seeds 26040:26043 \
  --horizon-steps 8 \
  --sample-stride 4 \
  --nearest-k 16 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 80 \
  --max-visible-quantile 0.5 \
  --device cpu \
  --run-dir runs/m596_bc_capability_corpus_validation_smoke
```

## Artifacts

Train:

```text
runs/m596_bc_capability_corpus_train_smoke/capability_corpus.npz
runs/m596_bc_capability_corpus_train_smoke/pairs.csv
runs/m596_bc_capability_corpus_train_smoke/target_summary.csv
runs/m596_bc_capability_corpus_train_smoke/pair_summary.csv
runs/m596_bc_capability_corpus_train_smoke/summary.json
```

Validation:

```text
runs/m596_bc_capability_corpus_validation_smoke/capability_corpus.npz
runs/m596_bc_capability_corpus_validation_smoke/pairs.csv
runs/m596_bc_capability_corpus_validation_smoke/target_summary.csv
runs/m596_bc_capability_corpus_validation_smoke/pair_summary.csv
runs/m596_bc_capability_corpus_validation_smoke/summary.json
```

## Summary

| split | seeds | rows | obs dim | action dim | target dim | hidden dim | pair rows | labels enter actor input |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| train | 8 | 112 | 72 | 3 | 3 | 64 | 240 | false |
| validation | 4 | 58 | 72 | 3 | 3 | 64 | 240 | false |

Both corpora also report:

```text
contains_privileged_actor_inputs = false
```

## Target Summary

Train target statistics:

| target | count | mean | std | min | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| future_braking_deceleration | 112 | 1.379531 | 0.918413 | 0.041724 | 5.443414 |
| future_yaw_response | 112 | 0.203583 | 0.315063 | 0.000985 | 1.354947 |
| future_lateral_accel_response | 112 | 1.983547 | 1.846627 | 0.310667 | 7.936461 |

Validation target statistics:

| target | count | mean | std | min | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| future_braking_deceleration | 58 | 2.342116 | 0.918623 | 0.529608 | 5.165878 |
| future_yaw_response | 58 | 0.351557 | 0.326228 | 0.021075 | 1.331926 |
| future_lateral_accel_response | 58 | 2.146792 | 1.958234 | 0.144227 | 6.195657 |

## Pair Summary

Train pair rows:

| target | pair count | mean target z delta | max target z delta |
| --- | ---: | ---: | ---: |
| future_braking_deceleration | 80 | 1.482964 | 1.896359 |
| future_yaw_response | 80 | 3.663589 | 4.297427 |
| future_lateral_accel_response | 80 | 1.421671 | 2.966628 |

Validation pair rows:

| target | pair count | mean target z delta | max target z delta |
| --- | ---: | ---: | ---: |
| future_braking_deceleration | 80 | 1.965566 | 4.545902 |
| future_yaw_response | 80 | 2.750540 | 4.004647 |
| future_lateral_accel_response | 80 | 2.439844 | 2.983659 |

## Interpretation

M596 confirms the corpus runner can produce non-empty train and validation
capability datasets with same-corpus matched-current pair rows.

This is still not hidden repair evidence. It is data readiness evidence:

```text
the next repair smoke has aligned P0 observations, base action anchors,
future-response labels, recurrent hidden diagnostics, and pair-ranking rows.
```

No checkpoint was trained or promoted.

## Decision

```text
bc_capability_corpus_export_smoke_admit_repair_smoke_design
```

M596 passes because both train and validation corpora are non-empty, have P0
actor observation dimension `72`, have non-zero pair rows, and keep capability
labels out of actor inputs.

## Next

```text
M597: design the first capability repair objective smoke.
```
