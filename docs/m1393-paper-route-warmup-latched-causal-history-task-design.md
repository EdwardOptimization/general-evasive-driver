# M1393 Paper-Route Warmup-Latched Causal History Task Design

## Summary

M1393 designs a warmup-latched causal-history task/source route after M1392
showed that M1391 candidates are outcome-sensitive but not source-diverse
history-causal.

Decision:

```text
warmup_latched_causal_history_task_design_admit_config_smoke
```

M1393 performs no training, PPO, new evaluation, promotion, private holdout,
actor-input expansion, or corpus export.

## M1392 Blocker

M1392 result:

```text
accepted_outcome_rows: 633
accepted_self_id_rows: 24
accepted_self_id_unique_seeds: 1
accepted_reset_rows: 363
accepted_zero_current_rows: 246
wrong_same_current_history accepted rows: 0
same_recent_wrong_older_history accepted rows: 0
```

This means the current M1375/M1391 source family is not enough. It has broad
reset/zero-current sensitivity, but the self-ID-relevant delayed-history signal
is seed-narrow and margin-only. Training on it would likely teach public-row
artifacts, not general history use.

## Core Design

Create a two-phase source distribution:

```text
Phase A: warmup capability evidence
  hidden dynamics are already randomized or faulted;
  the driver experiences mild steering/braking/throttle response;
  no emergency claim is made in this phase.

Phase B: emergency reveal
  obstacle/corridor pressure appears after warmup;
  current frame is matched or bucketed across hidden capability families;
  correct action should depend on what the warmup response revealed.
```

The task is not to add an oracle planner. The actor still receives only the P0
human-view observation and recurrent history. The task generator may use hidden
capability labels for sampling, matching, logging, and source selection only.

## Why Warmup

The current matched-current source route often makes older observation history
nearly identical:

```text
M1391 older_history_l2_p95: 0.02730
M1392 wrong_same_current_history accepted rows: 0
```

Warmup should create outcome-relevant history without relying on current-frame
differences:

```text
brake tap response -> braking authority estimate
mild steering response -> yaw/lateral authority estimate
throttle/brake transition -> rear stability estimate
actuator state lag -> delay estimate
```

The emergency reveal then asks whether that evidence changes the maneuver.

## Task Phases

### Phase A: Warmup

Initial public design:

```text
duration: 0.6s to 1.5s
speed range: 12 m/s to 22 m/s
road: straight or mild curvature
obstacle: absent, inactive, or far outside outcome window
control cost: mild, to avoid unsafe active probing
fault activation: before or at warmup start
```

Warmup stimulus should be natural, not a scripted controller mode:

```text
small lane-centering demand;
small obstacle-free corridor offset;
mild curvature entry;
optional low-risk decel zone.
```

The policy still directly outputs steer/throttle/brake. Any scripted component
belongs to scenario geometry or initial conditions, not actor input or action
reference.

### Phase B: Emergency Reveal

At reveal:

```text
obstacle distance bucket: close enough that current-only reaction is stressed;
obstacle lateral offset bucket: source-diverse left/right/center;
road boundary: leaves stable AES and drift-AES possibilities;
current ego state: matched or bucketed across capability families;
hidden dynamics: not exposed to actor.
```

Reveal buckets:

```text
obstacle_distance: 8m to 35m, bucketed by 4m
obstacle_lateral_offset: -1.5m to 1.5m, bucketed by 0.5m
speed: 12m/s to 22m/s, bucketed by 2m/s
yaw_rate: bucketed by 0.15 normalized units
steer actuator state: bucketed by 0.05 normalized units
```

## Capability Families

Current-model public fault families:

```text
global_mu_drop
brake_authority_drop
front_lateral_authority_drop
rear_lateral_authority_drop
drive_authority_drop
steering_fault
mass_cg_shift
delay_noise_fault
combined_fault
```

These are simulator/source labels only. Actor input remains unchanged.

Future high-fidelity families remain future-only until model support exists:

```text
single-wheel puncture or blowout;
split-mu left/right;
single-wheel brake pull;
halfshaft torque loss;
suspension/tire damage.
```

## Matching Controls

M1394 implementation must materialize matching metrics at reveal:

```text
ego_response_l2 <= 0.08
actuator_state_l2 <= 0.05
previous_command_l2 <= 0.05
scene_context_l2 <= 0.10
obstacle_position_l2 <= 0.10
road_boundary_l2 <= 0.12
recent_window_l2 <= 0.10
warmup_history_l2 reported separately
```

Required controls:

```text
normal
reset_hidden
zero_current_response
delayed_warmup_history
wrong_warmup_history_same_reveal
same_recent_wrong_warmup_history
warmup_removed_or_shortened
```

Interpretation:

```text
zero_current_response: positive control for current feedback;
reset_hidden: history/remembrance control but not enough alone;
wrong_warmup_history and same_recent_wrong_warmup_history: primary self-ID
tests;
warmup_removed_or_shortened: tests whether history evidence duration matters.
```

## Metrics

Primary outcome metrics:

```text
success_drop
collision_gap
road_departure_gap
obstacle_completion_drop
min_clearance_margin_gap
terminal_margin_gap
return_gap
first_action_l2
sequence_action_l2_mean
termination_reason histogram
```

A row is warmup-history positive only if:

```text
normal rollout succeeds or has nonnegative margin;
current/recent matching passes;
wrong_warmup or same_recent_wrong_warmup changes action;
wrong_warmup or same_recent_wrong_warmup causes success drop or margin gap >= 0.02;
effect is not counted solely from zero_current_response or reset_hidden;
source diversity caps pass.
```

## Source-Diversity Thresholds

Structural smoke:

```text
source_rows >= 512
matched_or_bucketed_reveal_rows >= 160
unique_source_seeds >= 24
unique_capability_pairs >= 8
unique_reveal_buckets >= 8
all metrics finite
```

Public diagnostic positive:

```text
warmup_history_positive_rows >= 48
accepted_seeds >= 12
accepted_capability_pairs >= 6
accepted_reveal_buckets >= 4
accepted_intervention_families >= 2
max_single_seed_share <= 0.25
max_single_capability_pair_share <= 0.35
```

Corpus-export threshold:

```text
warmup_history_positive_rows >= 128
accepted_seeds >= 24
accepted_capability_pairs >= 8
accepted_reveal_buckets >= 6
train_eval_split_by_seed_possible == true
private_holdout_not_used == true
```

## Failure Routes

Pre-register outcomes:

```text
no_matched_reveal_surface:
  warmup task cannot produce matched/bucketed current states.
  route to task geometry and reveal timing redesign.

current_feedback_only_signal:
  zero_current/reset are strong but wrong_warmup is weak.
  route to longer or more informative warmup.

action_only_warmup_signal:
  wrong_warmup changes action but not outcome.
  route to closer obstacle or tighter boundary timing.

source_narrow_warmup_signal:
  history rows exist but are seed/fault narrow.
  route to source-diversity refresh.

warmup_history_positive_public:
  source-diverse wrong_warmup or same_recent_wrong_warmup outcome gaps appear.
  route to corpus design, not direct training.
```

## Implementation Route

Admit:

```text
m1394-paper-route-warmup-latched-config-smoke
```

M1394 should implement or run a no-training warmup-latched config/source smoke:

```text
input: M1362 public-base checkpoint;
output: warmup/reveal snapshots, matching metrics, source-diversity summary;
no training, no PPO, no private holdout, no corpus export, no actor input change.
```

The smoke should first prove the simulator/source route can express:

```text
warmup phase;
emergency reveal phase;
matched or bucketed reveal current frame;
wrong_warmup and same_recent_wrong_warmup intervention targets.
```

## Claim Boundary

Allowed from M1393:

```text
warmup-latched causal-history task/source design;
next no-training config smoke route.
```

Forbidden:

```text
history necessity proof;
level3 self-identification;
training-corpus export;
checkpoint promotion;
private-holdout or paper-level evidence;
real vehicle or high-fidelity per-wheel claims.
```

## Decision

```text
warmup_latched_causal_history_task_design_admit_config_smoke
```

Next:

```text
m1394-paper-route-warmup-latched-config-smoke
```
