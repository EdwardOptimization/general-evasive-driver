# M469 Adversarial Wrong-History Pair Search

## Purpose

M469 implements the adversarial pair search designed in M468. It anchors on
M467 near-boundary no-effect left states and searches the full M462
`candidate_pairs.csv` pool for stronger right histories.

No policy rollout, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## Implementation

Added:

```text
src/autodrift/adversarial_wrong_history_pair_search.py
tests/test_adversarial_wrong_history_pair_search.py
```

The CLI consumes:

```text
runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv
runs/m462_late_reveal_matched_current_fresh_seed10200/candidate_pairs.csv
```

and writes:

```text
search_candidates.csv
adversarial_pairs.csv
summary.json
```

Join keys:

```text
probe_seed
target
left_seed
left_step
```

Hard filters:

```text
0 < normal_margin <= 0.75
target_z_delta >= 1.0
visible_distance <= row visible_threshold
left_episode != right_episode
```

Score:

```text
adversarial_wrong_history_score =
  hidden/current separation
+ hidden-more-than-current bonus
+ target_z_delta score
+ visible similarity score
+ right-label mismatch bonus
+ low-normal-margin score
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.adversarial_wrong_history_pair_search \
  --near-boundary-csv runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv \
  --candidate-pairs-csv runs/m462_late_reveal_matched_current_fresh_seed10200/candidate_pairs.csv \
  --normal-margin-ceiling 0.75 \
  --min-target-z-delta 1.0 \
  --max-rows 128 \
  --max-per-anchor 4 \
  --max-per-probe-seed 64 \
  --max-per-label 96 \
  --max-per-target 64 \
  --max-per-obstacle-bucket 24 \
  --min-adversarial-pairs 64 \
  --min-left-state-count 16 \
  --min-probe-seed-count 3 \
  --min-obstacle-label-count 2 \
  --min-target-count 2 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.70 \
  --run-dir runs/m469_adversarial_wrong_history_pair_search
```

## Results

```text
search candidates:             50
adversarial pairs:             50
near-boundary left states:     26
probe seeds:                    3
labels:                         2
targets:                        3
single seed share:           0.68
single label share:          0.64
search_pass:                False
```

By probe seed:

```text
10200: 34
10300:  7
10400:  9
```

By label:

```text
drift_required: 32
unavoidable:    18
```

By target:

```text
future_yaw_response:           23
future_lateral_accel_response: 16
future_braking_deceleration:   11
```

Artifacts:

```text
runs/m469_adversarial_wrong_history_pair_search/search_candidates.csv
runs/m469_adversarial_wrong_history_pair_search/adversarial_pairs.csv
runs/m469_adversarial_wrong_history_pair_search/summary.json
```

## Interpretation

M469 is a useful negative result. The adversarial search can recover more
right-history alternatives for the M467 near-boundary anchors, but the existing
M462 candidate pool is too small and imbalanced to justify another outcome
probe:

- `50` pairs is below the pre-registered `64` minimum.
- single-seed share is `0.68`, above the `0.50` cap.
- coverage is concentrated in seed `10200`.

The blocker is now data-pool coverage, not selector implementation. The next
step should expand the adversarial search pool with additional fresh seed
windows or a mining command that directly targets near-boundary left states.

## Validation

```text
tests/test_adversarial_wrong_history_pair_search.py: 3 passed
```

## Decision

```text
search_surface_too_small_admit_m470_expanded_pool_design
```

Do not run an outcome probe on this imbalanced 50-row surface. No checkpoint is
promoted.
