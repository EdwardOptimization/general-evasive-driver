# M502 Natural Boundary-Pressure Config Implementation

## Purpose

M502 implements and sampling-validates boundary-pressured natural belief
configs after M501 showed that the M500 surface lacks enough rows that are
both action-sensitive and terminal-boundary-sensitive.

No matched-current mining, outcome gate, training, PPO, actor-input change,
checkpoint update, or checkpoint promotion is performed.

## Configs

Added:

```text
configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json
configs/m502_natural_boundary_pressure_warmup_zero_relvel.json
```

Both preserve the P0 actor contract:

```text
history_length = 1
action_history_mode = full
obstacle_relative_velocity_mode = zero
no wheel/slip/mu/oracle actor inputs
```

### Boundary Short-Reveal

Key settings:

```text
track_width: 7.5
speed_range: [13.8, 18.0]
obstacle.distance_range: [4.5, 24.0]
obstacle.half_width_range: [0.65, 1.45]
obstacle.max_threshold_score: 0.50
obstacle.perception_reveal_distance: 6.0
obstacle.min_time_after_friction_step: 0.20
randomization.mu_range: [0.16, 0.68]
actuator_tau_scale_range: [1.00, 4.20]
```

### Boundary Warm-Up

Key settings:

```text
track_width: 7.5
speed_range: [13.0, 17.8]
obstacle.distance_range: [6.0, 24.0]
obstacle.half_width_range: [0.60, 1.40]
obstacle.max_threshold_score: 0.38
obstacle.perception_reveal_distance: 7.5
obstacle.min_time_after_friction_step: 0.30
randomization.mu_range: [0.16, 0.70]
actuator_tau_scale_range: [0.90, 4.00]
```

## Sampling Validation

Seed blocks:

```text
12400, 12500, 12600
```

Resets per block:

```text
128
```

Artifacts:

```text
runs/m502_natural_boundary_pressure_config_validation/sampling_rows.csv
runs/m502_natural_boundary_pressure_config_validation/sampling_summary.csv
runs/m502_natural_boundary_pressure_config_validation/sampling_summary.json
```

Results:

```text
boundary_short_reveal:
  reset_ok: 384 / 384
  label_count: 3
  labels: unavoidable 219, drift_required 154, aes_feasible 11
  single_label_share: 0.5703125
  hidden_at_reset_count: 384
  friction_step_before_reveal_count: 362
  threshold_score_mean: 0.229615
  threshold_score_max: 0.499242
  time_to_obstacle_mean: 1.145237
  sampling_gate_pass: true

boundary_warmup:
  reset_ok: 384 / 384
  label_count: 3
  labels: drift_required 200, unavoidable 166, aes_feasible 18
  single_label_share: 0.520833
  hidden_at_reset_count: 384
  friction_step_before_reveal_count: 354
  threshold_score_mean: 0.191020
  threshold_score_max: 0.374809
  time_to_obstacle_mean: 1.201366
  sampling_gate_pass: true
```

Compared with M494, the boundary-pressure configs keep sampling robust and keep
threshold-score means at or below the prior natural configs:

```text
M494 short_reveal threshold_score_mean: 0.291253
M502 boundary_short threshold_score_mean: 0.229615

M494 warmup threshold_score_mean: 0.191418
M502 boundary_warmup threshold_score_mean: 0.191020
```

## Behavior Smoke

Artifacts:

```text
runs/m502_natural_boundary_pressure_config_validation/behavior_summary_rows.csv
runs/m502_natural_boundary_pressure_config_validation/behavior_summary_agg.csv
runs/m502_natural_boundary_pressure_config_validation/behavior_summary.json
```

Runs:

```text
episodes: 32
seed: 12400
policies: m399 checkpoint, heuristic, random
```

Aggregate results:

```text
boundary_short_reveal:
  m399 success:      0.78125
  heuristic success: 0.21875
  random success:    0.12500
  m399 collision:    0.21875
  m399 margin mean:  1.074506

boundary_warmup:
  m399 success:      0.87500
  heuristic success: 0.34375
  random success:    0.15625
  m399 collision:    0.12500
  m399 margin mean:  1.124653
```

The new configs are not saturated above `0.90`, M399 remains nonzero, and
heuristic/random do not dominate M399.

## Decision

```text
boundary_pressure_configs_sampling_pass_admit_m503_matched_current_mining
```

M503 should mine matched-current ambiguity surfaces on both M502 configs before
any targeted pair triage, outcome gate, training, or checkpoint promotion.
