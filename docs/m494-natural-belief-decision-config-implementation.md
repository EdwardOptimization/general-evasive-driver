# M494 Natural Belief Decision Config Implementation

## Purpose

M494 implements and sampling-validates the natural belief decision-window
configs selected by M493.

No proof mining, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## Configs

Added:

```text
configs/m494_natural_belief_short_reveal_zero_relvel.json
configs/m494_natural_belief_warmup_capability_zero_relvel.json
```

Both configs preserve the P0 actor contract:

```text
history_length = 1
action_history_mode = full
obstacle_relative_velocity_mode = zero
no wheel/slip/mu/oracle actor inputs
```

### Short Reveal

The short-reveal config makes the obstacle visible late and keeps the scenario
high-energy:

```text
track_width: 7.6
speed_range: [13.8, 18.0]
obstacle.distance_range: [4.5, 20.0]
obstacle.perception_reveal_distance: 6.5
obstacle.half_width_range: [0.70, 1.45]
obstacle.max_threshold_score: 0.55
friction_step.step_range: [4, 28]
obstacle.min_time_after_friction_step: 0.35
```

### Warm-Up Capability Evidence

The warm-up config gives more pre-reveal response evidence while preserving a
late decision window:

```text
track_width: 7.8
speed_range: [12.8, 17.6]
obstacle.distance_range: [7.0, 24.0]
obstacle.perception_reveal_distance: 8.0
obstacle.half_width_range: [0.60, 1.35]
obstacle.max_threshold_score: 0.40
friction_step.step_range: [4, 30]
obstacle.min_time_after_friction_step: 0.55
```

## Sampling Stress

Command class:

```text
reset each config over seed blocks 11800, 11900, 12000
128 resets per block
```

Artifacts:

```text
runs/m494_natural_belief_decision_config_validation/sampling_rows.csv
runs/m494_natural_belief_decision_config_validation/sampling_summary.csv
runs/m494_natural_belief_decision_config_validation/sampling_summary.json
```

Results:

```text
short_reveal:
  rows: 384
  reset failures: 0
  label count: 2
  single-label share: 0.747396
  labels: unavoidable 287, drift_required 97
  threshold_score_mean: 0.291253
  time_to_obstacle_mean: 1.028893
  hidden_at_reset_count: 384
  friction_step_before_reveal_count: 358
  sampling gate: pass

warmup_capability:
  rows: 384
  reset failures: 0
  label count: 3
  single-label share: 0.565104
  labels: drift_required 217, unavoidable 141, aes_feasible 26
  threshold_score_mean: 0.191418
  time_to_obstacle_mean: 1.199203
  hidden_at_reset_count: 384
  friction_step_before_reveal_count: 376
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
runs/m494_short_reveal_behavior_seed11800
runs/m494_short_reveal_behavior_seed11900
runs/m494_warmup_capability_behavior_seed11800
runs/m494_warmup_capability_behavior_seed11900
```

Aggregate artifacts:

```text
runs/m494_natural_belief_decision_config_validation/behavior_summary_rows.csv
runs/m494_natural_belief_decision_config_validation/behavior_summary_agg.csv
runs/m494_natural_belief_decision_config_validation/behavior_summary.json
```

Aggregate results:

```text
short_reveal:
  m399 success:              0.515625
  m399 reset success:        0.546875
  m399 zero-current success: 0.546875
  heuristic success:         0.046875
  random success:            0.046875
  m399 clearance mean:       0.566540

warmup_capability:
  m399 success:              0.843750
  m399 reset success:        0.859375
  m399 zero-current success: 0.812500
  heuristic success:         0.281250
  random success:            0.234375
  m399 clearance mean:       1.525112
```

The short-reveal config is harder and non-saturated. The warm-up config is
easier for M399 but still nontrivial relative to heuristic and random
baselines. Aggregate reset/zero-current deltas remain weak; this is expected
because M494 is config validation, not self-ID proof.

## Decision

```text
natural_belief_configs_sampling_pass_admit_m495_matched_current_mining
```

M495 should run source-diverse natural matched-current mining on both M494
configs before any wrong-history outcome gate, proof expansion, or training.

No checkpoint is promoted.
