# M503 Natural Boundary-Pressure Matched-Current Mining

## Purpose

M503 mines matched-current ambiguity surfaces on the two M502
boundary-pressure natural belief configs.

No targeted pair triage, wrong-history outcome gate, training, PPO,
actor-input change, checkpoint update, or checkpoint promotion is performed.

## Commands

M503 uses the same mining settings as M485/M495:

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
12400, 12500, 12600
```

Both configs produced large surfaces, but only `3` probe seeds. M503 therefore
added fresh source-diversity blocks:

```text
12700, 12800, 12900
```

This is source-diversity expansion, not parameter retuning.

## Artifacts

Per-run artifacts:

```text
runs/m503_boundary_short_reveal_matched_current
runs/m503_boundary_warmup_matched_current
runs/m503_boundary_short_reveal_matched_current_fresh12700
runs/m503_boundary_warmup_matched_current_fresh12700
```

Combined artifacts:

```text
runs/m503_natural_boundary_pressure_matched_current_summary/combined_matched_pairs.csv
runs/m503_natural_boundary_pressure_matched_current_summary/combined_summary.json
runs/m503_natural_boundary_pressure_matched_current_summary/per_run_summary.csv
```

## Per-Run Results

```text
boundary_short_reveal, seeds 12400-12600:
  accepted pairs: 1437
  physical pairs: 1376
  left steps: 20
  obstacle buckets: 21

boundary_warmup, seeds 12400-12600:
  accepted pairs: 1405
  physical pairs: 1321
  left steps: 22
  obstacle buckets: 21

boundary_short_reveal, seeds 12700-12900:
  accepted pairs: 1469
  physical pairs: 1305
  left steps: 20
  obstacle buckets: 21

boundary_warmup, seeds 12700-12900:
  accepted pairs: 1416
  physical pairs: 1251
  left steps: 23
  obstacle buckets: 22
```

## Combined Surface

```text
accepted_pair_count:            5727
accepted_physical_pair_count:   3716
probe_seed_count:                  6
obstacle_label_count:              3
target_count:                      3
config_count:                      2
seed_window_count:                 2
left_step_count:                  24
obstacle_bucket_proxy_count:      26

single_seed_share:             0.185088
single_label_share:            0.479483
single_target_share:           0.519993
single_config_share:           0.507421
single_window_share:           0.503754
```

Counts:

```text
labels:
  aes_feasible:     331
  drift_required:  2650
  unavoidable:     2746

targets:
  future_braking_deceleration:    2343
  future_lateral_accel_response:   406
  future_yaw_response:            2978

configs:
  boundary_short_reveal: 2906
  boundary_warmup:       2821
```

The combined surface passes the M503 source-diversity gate:

```text
surface_gate_pass: true
```

The boundary-pressure surface is also closer in obstacle geometry than the M495
natural surface:

```text
left_obstacle_distance_mean: 13.509874
left_obstacle_distance_p10:   8.044611
left_obstacle_distance_p50:  13.492078
left_obstacle_distance_p90:  19.527809
```

## Decision

```text
boundary_pressure_matched_surface_pass_admit_m504_targeted_pair_triage
```

M504 should select targeted boundary-action-sensitive pairs from the M503
surface. It should not train or promote a checkpoint.
