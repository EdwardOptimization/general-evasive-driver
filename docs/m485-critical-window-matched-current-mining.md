# M485 Critical-Window Matched-Current Mining

## Purpose

M485 runs matched-current ambiguity mining on the two M484 critical-window
configs before any wrong-history or tail-aligned proof gate.

No training, PPO, actor-input change, checkpoint update, or checkpoint promotion
is performed.

## Commands

M485 runs `autodrift.matched_current_response_ambiguity` on both configs with
expanded M471-style settings:

```text
episodes: 80
horizon_steps: 15
sample_stride: 3
max_samples: 2400
nearest_k: 32
match_feature_set: current_response_context
max_visible_quantile: 0.05
min_target_z_delta: 1.0
max_pairs_per_target: 640
max_pairs_per_physical_pair: 2
max_pairs_per_left_step: 40
max_pairs_per_source_obstacle_bucket: 80
```

The first pass used seed blocks:

```text
11200, 11300, 11400
```

That produced large surfaces, but only `3` probe seeds. Because the
pre-registered M485 gate requires `>= 6` probe seeds, M485 added fresh blocks:

```text
11500, 11600, 11700
```

This is a source-diversity expansion, not a parameter retune.

## Artifacts

Per-run artifacts:

```text
runs/m485_near_threshold_matched_current
runs/m485_late_high_energy_matched_current
runs/m485_near_threshold_matched_current_fresh11500
runs/m485_late_high_energy_matched_current_fresh11500
```

Combined artifacts:

```text
runs/m485_critical_window_matched_current_summary/combined_matched_pairs.csv
runs/m485_critical_window_matched_current_summary/combined_summary.json
runs/m485_critical_window_matched_current_summary/per_run_summary.csv
```

## Per-Run Results

```text
near_threshold, seeds 11200-11400:
  accepted pairs:          1551
  physical pairs:          1434
  left steps:                31
  obstacle buckets:          29

late_high_energy, seeds 11200-11400:
  accepted pairs:          1388
  physical pairs:          1282
  left steps:                27
  obstacle buckets:          23

near_threshold, seeds 11500-11700:
  accepted pairs:          1436
  physical pairs:          1301
  left steps:                28
  obstacle buckets:          27

late_high_energy, seeds 11500-11700:
  accepted pairs:          1427
  physical pairs:          1299
  left steps:                25
  obstacle buckets:          20
```

## Combined Surface

```text
accepted pairs:                  5802
accepted physical pairs:         4321
probe seeds:                        6
obstacle labels:                    3
targets:                            3
configs:                            2
seed windows:                       2
left steps:                        31
obstacle bucket proxy count:      107
single-seed share:              0.178
single-label share:             0.547
single-target share:            0.474
single-config share:            0.515
single-window share:            0.507
```

Label distribution:

```text
drift_required: 3172
unavoidable:    2194
aes_feasible:    436
```

Target distribution:

```text
future_braking_deceleration: 2748
future_yaw_response:        2610
future_lateral_accel:        444
```

Seed distribution:

```text
11500: 1032
11200: 1027
11300: 1007
11600:  929
11400:  905
11700:  902
```

## Gate Decision

The combined surface passes the M485 source-diversity gate:

```text
accepted_pair_count >= 512
probe_seed_count >= 6
obstacle_label_count >= 2
target_count >= 2
single_seed_share <= 0.50
single_label_share <= 0.70
```

This is not self-ID proof. It is an admission surface for targeted
wrong-history pair selection and tail-aligned outcome gates.

## Decision

```text
critical_window_matched_surface_pass_admit_m486_targeted_wrong_history_triage
```

M486 should run source-diverse targeted wrong-history triage over the combined
matched-current surface before any outcome/tail-aligned proof gate.

No checkpoint is promoted.
