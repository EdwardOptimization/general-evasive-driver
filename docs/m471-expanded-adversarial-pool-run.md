# M471 Expanded Adversarial Pool Run

## Purpose

M471 tests whether simply enlarging the same seed-window matched-current pool
fixes the M469 adversarial wrong-history coverage failure.

No training, PPO, checkpoint update, actor-input change, outcome probe, or
checkpoint promotion is performed.

## Commands

Expanded matched-current mining:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --probe-seeds 10200,10300,10400 \
  --episodes 80 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 2400 \
  --nearest-k 32 \
  --match-feature-set current_response_context \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 640 \
  --max-pairs-per-physical-pair 2 \
  --max-pairs-per-left-step 40 \
  --max-pairs-per-source-obstacle-bucket 80 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 120 \
  --device cpu \
  --run-dir runs/m471_expanded_matched_current_seed10200
```

Adversarial search:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.adversarial_wrong_history_pair_search \
  --near-boundary-csv runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv \
  --candidate-pairs-csv runs/m471_expanded_matched_current_seed10200/candidate_pairs.csv \
  --normal-margin-ceiling 0.75 \
  --min-target-z-delta 1.0 \
  --max-rows 160 \
  --max-per-anchor 4 \
  --max-per-probe-seed 72 \
  --max-per-label 112 \
  --max-per-target 72 \
  --max-per-obstacle-bucket 28 \
  --min-adversarial-pairs 64 \
  --min-left-state-count 16 \
  --min-probe-seed-count 3 \
  --min-obstacle-label-count 2 \
  --min-target-count 2 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.70 \
  --run-dir runs/m471_expanded_adversarial_wrong_history_search
```

## Results

Expanded matched-current mining:

```text
candidate pairs:              380877
accepted pairs:                 1702
accepted physical pairs:        1608
accepted left steps:              31
accepted obstacle buckets:        42
```

This is substantially larger than M462:

```text
M462 candidate pairs:           73281
M462 accepted pairs:              422
```

Adversarial search:

```text
search candidates:                94
adversarial pairs:                67
near-boundary left states:        24
probe seed count:                  3
label count:                       2
target count:                      3
single seed share:          0.671642
single label share:         0.597015
search_pass:                   False
```

By probe seed:

```text
10200: 45
10300:  9
10400: 13
```

By label:

```text
drift_required: 40
unavoidable:    27
```

By target:

```text
future_yaw_response:           33
future_lateral_accel_response: 18
future_braking_deceleration:   16
```

Artifacts:

```text
runs/m471_expanded_matched_current_seed10200/summary.json
runs/m471_expanded_matched_current_seed10200/candidate_pairs.csv
runs/m471_expanded_adversarial_wrong_history_search/summary.json
runs/m471_expanded_adversarial_wrong_history_search/adversarial_pairs.csv
```

## Interpretation

M471 partially improves M469: adversarial pairs increase from `50` to `67`, so
the count threshold is met. However, the surface still fails because seed
balance remains poor. Seed `10200` contributes `45/67` rows, giving a
single-seed share of `0.671642`, above the `0.50` cap.

The failure is now more specific: the same seed window can produce enough rows
but not enough source balance. Therefore the next step should not run an
outcome probe on M471. It should expand to fresh seed windows and discover
their own near-boundary anchors before combining surfaces.

## Decision

```text
expanded_same_window_count_pass_balance_fail_admit_m472
```

No checkpoint is promoted.
