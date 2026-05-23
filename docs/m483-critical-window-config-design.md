# M483 Critical-Window Config Design

## Purpose

M483 designs the next critical-window task/config step after M482 produced a
tail-aligned event signal that is still source-narrow.

No training, PPO, actor-input change, proof mining run, checkpoint update, or
checkpoint promotion is performed.

## M482 Diagnosis

M482 improves the diagnostic over M480:

```text
M480 late one-shot event rows: 0
M482 tail-aligned event rows:  3
```

But M482 still fails the natural wrong-history proof gate:

```text
wrong_tail_once proof-style rows: 14
wrong_tail_once event rows:       3
event physical pairs:             1
event probe seeds:                1
event label count:                1
event target count:               1
```

All event rows are the same pair repeated at offsets `8`, `12`, and `16`:

```text
pair_id: 150
probe_seed: 11000
label: unavoidable
target: future_yaw_response
```

This is useful diagnostic evidence, but it is not source-diverse proof.

## Design Choice

Do not train, and do not expand the proof claim from M482. The next step should
create critical-window configurations that make natural one-shot or
tail-aligned wrong-history mistakes more likely to matter across many sources.

The first M484 step should only validate config sampling and smoke behavior.
Proof mining comes later if the configs are robust.

## Config Family

Both configs must preserve the P0 human-view input contract:

```text
history_length = 1
action_history_mode = full
obstacle_relative_velocity_mode = zero
road/free-space/obstacle geometry remains ego-frame
no wheel/slip/mu/oracle inputs
```

### Config A: critical-window near-threshold

Purpose: increase near-boundary event opportunities while keeping labels mixed.

Proposed file:

```text
configs/m484_critical_window_near_threshold_zero_relvel.json
```

Proposed changes relative to M457:

```text
track_width: 8.0
speed_range: [12.4, 17.0]
friction_step.step_range: [6, 34]
friction_step.mu_range: [0.20, 1.00]
obstacle.distance_range: [6.0, 24.0]
obstacle.half_width_range: [0.55, 1.25]
obstacle.max_sample_attempts: 30000
obstacle.max_threshold_score: 0.22
obstacle.min_time_after_friction_step: 0.0
obstacle.perception_reveal_distance: 10.0
randomization.mu_range: [0.20, 0.75]
randomization.actuator_tau_scale_range: [0.75, 3.60]
```

### Config B: critical-window late high-energy

Purpose: make obstacle reveal and high-energy handling-limit decisions closer to
the maneuver while retaining AEB-infeasible label variety.

Proposed file:

```text
configs/m484_critical_window_late_high_energy_zero_relvel.json
```

Proposed changes relative to M457/M451:

```text
track_width: 7.8
speed_range: [13.0, 17.4]
friction_step.step_range: [6, 34]
friction_step.mu_range: [0.18, 1.00]
obstacle.distance_range: [5.0, 22.0]
obstacle.half_width_range: [0.65, 1.35]
obstacle.max_sample_attempts: 30000
obstacle.max_threshold_score: 0.40
obstacle.min_time_after_friction_step: 0.0
obstacle.perception_reveal_distance: 8.0
randomization.mu_range: [0.18, 0.70]
randomization.tire_stiffness_scale_range: [0.42, 1.35]
randomization.brake_scale_range: [0.42, 1.30]
randomization.actuator_tau_scale_range: [0.90, 3.80]
```

The two configs are intentionally not identical. Config A is more
near-threshold; Config B is later, faster, and more handling-limit.

## M484 Validation Plan

M484 should implement both configs and run only sampling/behavior smokes.

Sampling stress:

```text
seed blocks: 11200, 11300, 11400
resets per block: 128
required: 0 sampling failures
required: at least 2 obstacle labels per config
required: single-label share <= 0.80
record: speed, obstacle distance, threshold score, time_to_obstacle
```

M399 behavior smoke:

```text
episodes: 32 per config
seed blocks: 11200 and 11300
policy: m399 checkpoint only
record: success, collision, obstacle completion, min clearance margin
```

Response diagnostic smoke:

```text
variants: normal, reset_hidden, zero_current_response
episodes: 32 per config
purpose: confirm the config is not trivially saturated or unsampleable
```

No matched-current mining or tail-aligned proof gate should run until the
sampling stress passes.

## M485 If M484 Passes

Only after M484 config validation should M485 run proof mining:

```text
matched-current mining on each critical-window config
targeted wrong-history pair triage
tail-aligned wrong-history gate
near-boundary/event selector
```

M485 source-diverse event criteria should remain strict:

```text
wrong_tail_once proof_candidate_count >= 16
event rows >= 4
probe_seed_count >= 6
obstacle_label_count >= 2
target_count >= 2
single_seed_share <= 0.50
single_label_share <= 0.70
```

If M484 configs fail sampling or saturate behavior, repair config ranges before
any proof mining.

## Guardrails

M484 must not:

```text
train or update a checkpoint
promote a checkpoint
change actor inputs
count M482's single-source events as proof
relax source-diversity thresholds
run private holdout tuning
```

## Decision

```text
admit_m484_critical_window_config_implementation
```

No checkpoint is promoted.
