# M474 Combined Fresh-Anchor Adversarial Search

## Purpose

M474 tests whether the source-diverse fresh anchors from M473 fix the
same-window imbalance that blocked M471. The goal is to build a source-diverse
adversarial wrong-history pair surface that is strong enough for a later
action/outcome proof probe.

No training, PPO, actor-input change, outcome probe, or checkpoint promotion is
performed.

## Inputs

Combined anchors:

```text
runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv
runs/m473_combined_fresh_window_anchor_summary/near_boundary_candidates_combined.csv
```

Combined candidate-pair pools:

```text
runs/m471_expanded_matched_current_seed10200/candidate_pairs.csv
runs/m473a_fresh_window_matched_current_seed10500/candidate_pairs.csv
runs/m473b_fresh_window_matched_current_seed10800/candidate_pairs.csv
```

Combined input artifact:

```text
runs/m474_combined_fresh_anchor_adversarial_search/input_build_summary.json
runs/m474_combined_fresh_anchor_adversarial_search/combined_near_boundary_anchors.csv
runs/m474_combined_fresh_anchor_adversarial_search/combined_candidate_pairs.csv
```

## Input Build Result

```text
combined anchors:             139
combined candidate pairs: 1142403
anchor probe seeds:             9
anchor labels:                  2
anchor targets:                 3
```

By anchor source:

```text
m467:        35
m473_fresh: 104
```

By candidate source:

```text
m471:  380877
m473a: 380421
m473b: 381105
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.adversarial_wrong_history_pair_search \
  --near-boundary-csv runs/m474_combined_fresh_anchor_adversarial_search/combined_near_boundary_anchors.csv \
  --candidate-pairs-csv runs/m474_combined_fresh_anchor_adversarial_search/combined_candidate_pairs.csv \
  --normal-margin-ceiling 0.75 \
  --min-target-z-delta 1.0 \
  --max-rows 240 \
  --max-per-anchor 4 \
  --max-per-probe-seed 80 \
  --max-per-label 144 \
  --max-per-target 96 \
  --max-per-obstacle-bucket 32 \
  --min-adversarial-pairs 96 \
  --min-left-state-count 32 \
  --min-probe-seed-count 6 \
  --min-obstacle-label-count 2 \
  --min-target-count 2 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.70 \
  --run-dir runs/m474_combined_fresh_anchor_adversarial_search
```

## Results

```text
search candidates:               289
adversarial pairs:               197
near-boundary left states:        82
probe seeds:                       9
labels:                            2
targets:                           3
single seed share:          0.197970
single label share:         0.548223
search_pass:                    True
```

By probe seed:

```text
10200: 31
10300:  9
10400: 13
10500: 33
10600:  8
10700: 39
10800: 22
10900:  5
11000: 37
```

By label:

```text
drift_required: 89
unavoidable:   108
```

By target:

```text
future_braking_deceleration:   63
future_lateral_accel_response: 54
future_yaw_response:           80
```

Artifacts:

```text
runs/m474_combined_fresh_anchor_adversarial_search/summary.json
runs/m474_combined_fresh_anchor_adversarial_search/search_candidates.csv
runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv
```

## Interpretation

M474 fixes the M471 source-balance blocker. The adversarial pair surface grows
from `67` to `197` rows, near-boundary left states grow from `24` to `82`, and
single-seed share drops from `0.671642` to `0.197970`.

This is still not wrong-history outcome proof. It is a source-diverse
adversarial pair surface that can now be tested by action and continuation
outcome gates.

## Decision

```text
combined_adversarial_surface_pass_admit_m475
```

M475 should run action and continuation outcome probes on
`runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv`.

No checkpoint is promoted.
