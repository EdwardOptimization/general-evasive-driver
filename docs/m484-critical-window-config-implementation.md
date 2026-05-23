# M484 Critical-Window Config Implementation

## Purpose

M484 implements the critical-window zero-relvel configs designed in M483 and
runs only sampling and behavior smokes.

No matched-current proof mining, training, PPO, actor-input change, checkpoint
update, or checkpoint promotion is performed.

## Configs

Added:

```text
configs/m484_critical_window_near_threshold_zero_relvel.json
configs/m484_critical_window_late_high_energy_zero_relvel.json
```

Both configs preserve the P0 actor contract:

```text
history_length = 1
action_history_mode = full
obstacle_relative_velocity_mode = zero
no wheel/slip/mu/oracle actor inputs
```

The near-threshold config uses a milder critical window:

```text
speed_range: [12.4, 17.0]
obstacle.distance_range: [6.0, 24.0]
obstacle.max_threshold_score: 0.22
obstacle.perception_reveal_distance: 10.0
```

The late high-energy config is harder:

```text
speed_range: [13.0, 17.4]
obstacle.distance_range: [5.0, 22.0]
obstacle.max_threshold_score: 0.40
obstacle.perception_reveal_distance: 8.0
```

## Sampling Stress

Command class:

```text
reset each config over seed blocks 11200, 11300, 11400
128 resets per block
```

Artifacts:

```text
runs/m484_critical_window_config_validation/sampling_rows.csv
runs/m484_critical_window_config_validation/sampling_summary.csv
runs/m484_critical_window_config_validation/sampling_summary.json
```

Results:

```text
near_threshold:
  rows: 384
  reset failures: 0
  label count: 3
  single-label share: 0.557292
  labels: drift_required 214, unavoidable 141, aes_feasible 29
  threshold_score_mean: 0.109244
  time_to_obstacle_mean: 1.210832
  sampling gate: pass

late_high_energy:
  rows: 384
  reset failures: 0
  label count: 3
  single-label share: 0.588542
  labels: unavoidable 226, drift_required 145, aes_feasible 13
  threshold_score_mean: 0.200936
  time_to_obstacle_mean: 1.146677
  sampling gate: pass
```

Both configs pass the pre-registered sampling stress:

```text
0 sampling failures
at least 2 labels
single-label share <= 0.80
```

## Behavior Smoke

Runs:

```text
runs/m484_near_threshold_behavior_seed11200
runs/m484_near_threshold_behavior_seed11300
runs/m484_late_high_energy_behavior_seed11200
runs/m484_late_high_energy_behavior_seed11300
```

Aggregate artifacts:

```text
runs/m484_critical_window_config_validation/behavior_summary_rows.csv
runs/m484_critical_window_config_validation/behavior_summary_agg.csv
runs/m484_critical_window_config_validation/behavior_summary.json
```

Aggregate M399 results:

```text
near_threshold:
  m399 success:        0.796875
  m399 reset success:  0.828125
  m399 zero-current:   0.812500
  heuristic success:   0.218750
  random success:      0.203125

late_high_energy:
  m399 success:        0.687500
  m399 reset success:  0.687500
  m399 zero-current:   0.671875
  heuristic success:   0.125000
  random success:      0.203125
```

The configs are not trivial smoke failures. They are harder than the earlier
M457 distribution, especially late high-energy, while M399 still succeeds often
enough to allow near-boundary proof mining.

The reset/zero-current aggregate deltas are weak, so this is not self-ID proof.
That is expected for M484: it only validates that the configs are usable.

## Decision

```text
critical_window_configs_sampling_pass_admit_m485_matched_current_mining
```

M485 should run source-diverse matched-current mining on both critical-window
configs, then only proceed to wrong-history/tail-aligned proof gates if the
candidate surfaces are sufficiently balanced.

No checkpoint is promoted.
