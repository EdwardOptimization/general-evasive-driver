# M495 Natural Belief Matched-Current Mining

## Purpose

M495 runs source-diverse matched-current ambiguity mining on the two M494
natural belief decision-window configs.

No wrong-history outcome gate, proof expansion, training, PPO, actor-input
change, checkpoint update, or checkpoint promotion is performed.

## Commands

M495 runs `autodrift.matched_current_response_ambiguity` on both configs with
the same mining settings used by the critical-window branch:

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
11800, 11900, 12000
```

Both configs produced large surfaces, but only `3` probe seeds. Because the
pre-registered gate requires `>= 6` probe seeds, M495 added fresh source
diversity blocks:

```text
12100, 12200, 12300
```

This is a source-diversity expansion, not parameter retuning.

## Artifacts

Per-run artifacts:

```text
runs/m495_short_reveal_matched_current
runs/m495_warmup_capability_matched_current
runs/m495_short_reveal_matched_current_fresh12100
runs/m495_warmup_capability_matched_current_fresh12100
```

Combined artifacts:

```text
runs/m495_natural_belief_matched_current_summary/combined_matched_pairs.csv
runs/m495_natural_belief_matched_current_summary/combined_summary.json
runs/m495_natural_belief_matched_current_summary/per_run_summary.csv
```

## Per-Run Results

```text
short_reveal, seeds 11800-12000:
  accepted pairs:          1293
  physical pairs:          1196
  left steps:                26
  obstacle buckets:          15

warmup_capability, seeds 11800-12000:
  accepted pairs:          1436
  physical pairs:          1350
  left steps:                25
  obstacle buckets:          22

short_reveal, seeds 12100-12300:
  accepted pairs:          1269
  physical pairs:          1162
  left steps:                24
  obstacle buckets:          16

warmup_capability, seeds 12100-12300:
  accepted pairs:          1582
  physical pairs:          1439
  left steps:                27
  obstacle buckets:          25
```

## Combined Surface

```text
accepted pairs:                  5580
accepted physical pairs:         1620
probe seeds:                        6
obstacle labels:                    3
targets:                            3
configs:                            2
seed windows:                       2
left steps:                        54
obstacle bucket proxy count:       90
single-seed share:              0.175
single-label share:             0.480
single-target share:            0.502
single-config share:            0.541
single-window share:            0.511
```

Label distribution:

```text
unavoidable:    2678
drift_required: 2546
aes_feasible:    356
```

Target distribution:

```text
future_yaw_response:         2800
future_braking_deceleration: 2520
future_lateral_accel:         260
```

Seed distribution:

```text
11800: 894
11900: 915
12000: 920
12100: 967
12200: 976
12300: 908
```

Config distribution:

```text
warmup_capability: 3018
short_reveal:      2562
```

## Gate Decision

The combined surface passes the M495 source-diversity gate:

```text
accepted_pair_count >= 512
probe_seed_count >= 6
obstacle_label_count >= 2
target_count >= 2
config_count >= 2
single_seed_share <= 0.50
single_label_share <= 0.70
```

This is not self-ID proof. It is an admission surface for natural targeted
wrong-history pair triage and later outcome gates.

## Decision

```text
natural_belief_matched_surface_pass_admit_m496_targeted_pair_triage
```

M496 should run source-diverse targeted wrong-history triage over the combined
M495 matched-current surface before any natural wrong-history outcome gate.

No checkpoint is promoted.
