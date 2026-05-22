# M148 P0-Close Ambiguity Miner

Date: 2026-05-22

## Question

M147 showed that many M146 H1-ambiguous pairs are separated by channels that H1
removed from the current actor contract. M148 asks the stricter question:

```text
Do target-divergent pairs remain close under the current P0 human-view input?
```

If yes, the current P0 input may still be information-limited. If no, M146's
ambiguity was mostly caused by narrowing H1 too far.

This is still a supervised mining gate. It does not train PPO and does not
promote a new input profile.

## Method

For each seed, M148 reuses the deterministic M146/M147 collection recipe:

```text
env config: configs/m143_driver_like_profile_audit.json
episodes: 40
policy: heuristic
horizon steps: 15
sample stride: 3
max samples: 1000
history window: 25
max search samples: 450
feature quantile: 0.05
target quantile: 0.90
```

For the same sample subset it computes:

```text
H1 feature distance
P0 feature distance
future-envelope target distance
```

Accepted surfaces:

```text
H1-close target-divergent:
  H1 distance <= H1 5% threshold
  target distance >= target 90% threshold

P0-close target-divergent:
  P0 distance <= P0 5% threshold
  target distance >= target 90% threshold
```

No hidden parameters, oracle labels, feasibility labels, TTC, path error, or
required clearance are used as actor-like inputs.

## Implementation

New module:

```text
src/autodrift/p0_close_ambiguity_miner.py
```

New tests:

```text
tests/test_p0_close_ambiguity_miner.py
```

## Commands

Seed runs:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_ambiguity_miner \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 --seed 9480 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 25 \
  --post-slip-beta-threshold 0.06 --max-search-samples 450 \
  --feature-quantile 0.05 --target-quantile 0.90 --max-export-pairs 80 \
  --run-dir runs/m148_p0_close_ambiguity_seed9480

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_ambiguity_miner \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 --seed 9481 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 25 \
  --post-slip-beta-threshold 0.06 --max-search-samples 450 \
  --feature-quantile 0.05 --target-quantile 0.90 --max-export-pairs 80 \
  --run-dir runs/m148_p0_close_ambiguity_seed9481

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_ambiguity_miner \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 --seed 9482 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 25 \
  --post-slip-beta-threshold 0.06 --max-search-samples 450 \
  --feature-quantile 0.05 --target-quantile 0.90 --max-export-pairs 80 \
  --run-dir runs/m148_p0_close_ambiguity_seed9482
```

Aggregate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_ambiguity_miner \
  --mode aggregate \
  --summary-jsons runs/m148_p0_close_ambiguity_seed9480/summary.json,runs/m148_p0_close_ambiguity_seed9481/summary.json,runs/m148_p0_close_ambiguity_seed9482/summary.json \
  --run-dir runs/m148_p0_close_ambiguity_multiseed
```

## Artifacts

```text
runs/m148_p0_close_ambiguity_seed9480/accepted_pairs.csv
runs/m148_p0_close_ambiguity_seed9481/accepted_pairs.csv
runs/m148_p0_close_ambiguity_seed9482/accepted_pairs.csv
runs/m148_p0_close_ambiguity_multiseed/summary.json
runs/m148_p0_close_ambiguity_multiseed/aggregate_metric_summary.csv
```

## Results

Per-seed counts:

| Seed | H1-close target-divergent | P0-close target-divergent | Both | H1-only | P0-only | P0 episode pairs |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9480 | 105 | 97 | 83 | 22 | 14 | 39 |
| 9481 | 134 | 118 | 100 | 34 | 18 | 34 |
| 9482 | 136 | 131 | 109 | 27 | 22 | 35 |

Multiseed totals:

| Metric | Value |
| --- | ---: |
| H1-close target-divergent count | 375 |
| P0-close target-divergent count | 346 |
| Both H1/P0-close target-divergent count | 292 |
| H1-only target-divergent count | 83 |
| P0-only target-divergent count | 54 |
| H1 unique episode-pairs | 117 |
| P0 unique episode-pairs | 108 |
| P0 / H1 count ratio | 0.922667 |

Thresholds:

| Seed | H1 distance threshold | P0 distance threshold | Target distance threshold |
| ---: | ---: | ---: | ---: |
| 9480 | 0.442443 | 0.480301 | 2.066745 |
| 9481 | 0.468006 | 0.506773 | 2.065129 |
| 9482 | 0.455872 | 0.496806 | 2.072214 |

## Interpretation

M148 is a positive diagnostic result for current-input ambiguity:

```text
P0-close target-divergent pairs remain numerous and source-diverse.
```

The P0-close count is `346`, almost as high as H1-close's `375`. Therefore the
M146 ambiguity is not explained away by saying H1 was too narrow. The current
P0 human-view contract still admits many cases where the deployable observation
history is close while future braking/yaw/lateral envelope differs strongly.

This does not yet prove the actor needs a new sensor. It proves the next probe
must operate on P0-close pairs, not H1-close pairs.

## Decision

Complete M148 as a positive ambiguity-mining gate:

- current P0 may be information-limited on future-envelope prediction;
- do not return to PPO yet;
- do not promote raw wheel or `v_parallel` from this result alone;
- next step: evaluate whether candidate signals, longer history, or active
  probing resolve the P0-close pairs.
