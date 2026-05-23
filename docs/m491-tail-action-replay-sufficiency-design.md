# M491 Tail Action-Replay Sufficiency Design

## Purpose

M491 designs the next diagnostic after M490. M490 showed that artificially
holding the wrong hidden state alive can create outcome degradation:

```text
wrong_tail_once:          11 proof rows, 0 event rows
wrong_tail_hidden_hold_K: 90 proof rows, 4 event rows
```

The remaining question is:

```text
Are those M490 event rows caused by the wrong physical action sequence itself,
or by the artificially persistent wrong hidden state?
```

No training, PPO, actor-input change, checkpoint update, proof expansion, or
checkpoint promotion is performed.

## Diagnostic Split

M492 should split the hidden-hold signal into two mechanisms:

```text
1. action-sequence sufficiency:
   The wrong K-step physical commands move the vehicle into a worse state, even
   if the actor hidden is allowed to remain an observer/normal hidden.

2. hidden-state persistence:
   The wrong physical commands alone are not enough; degradation requires
   repeatedly forcing the actor to act from the wrong hidden state.
```

This matters because only the first case points toward action-sequence boundary
mining. The second case points toward recurrent latent/belief objectives.

## Required Variants

M492 should keep M490 controls:

```text
normal_tail
wrong_tail_once
reset_tail
zero_current_tail
wrong_tail_hidden_hold_2
wrong_tail_hidden_hold_4
wrong_tail_hidden_hold_8
wrong_tail_hidden_hold_12
```

Add action-replay variants:

```text
wrong_tail_action_replay_2
wrong_tail_action_replay_4
wrong_tail_action_replay_8
wrong_tail_action_replay_12
```

## Action-Replay Semantics

For each left-tail/right-tail matched pair and K:

```text
1. Start from the left-tail env snapshot.
2. Generate the K-step wrong action sequence using the same policy branch as
   wrong_tail_hidden_hold_K.
3. Reset to a fresh copy of the same left-tail env snapshot.
4. Execute those K physical actions open-loop.
5. During the forced-action window, update an observer hidden state from the
   left-tail normal hidden using the actual observations, but ignore its action
   output.
6. After K forced actions, resume the normal policy from that observer hidden.
```

The key point is step 5. The actor hidden is not kept wrong. It observes the
forced maneuver and then controls normally. This makes the variant answer:

```text
Were the wrong physical commands sufficient?
```

not:

```text
What happens if we keep manually injecting the wrong belief?
```

## Hidden Resume Policy

Use `observer_hidden` as the primary resume mode:

```text
observer_hidden starts from left_tail.hidden
at each forced step:
  run actor on current observation and observer_hidden
  ignore actor action
  keep actor next_hidden as observer_hidden
  execute the forced wrong-tail action in env
after K:
  resume actor from observer_hidden
```

Why this is preferred:

```text
It lets the recurrent state see the actual left observations during the forced
maneuver, including actuator/command consequences in subsequent observations.
It does not preserve the wrong hidden state artificially.
It is less artificial than hidden-hold, but still diagnostic because actions are
forced.
```

Do not use this as the main mode:

```text
resume from right/wrong hidden after K
```

That would collapse back into hidden-hold.

Optional comparison mode:

```text
wrong_tail_action_replay_reset_K
```

This would reset hidden after forced actions. It can be useful later, but M492
should start with observer-hidden replay to keep the interpretation clean.

## Expected Outcomes

If action replay produces source-diverse event rows:

```text
wrong physical action sequence is sufficient;
next step should mine naturally action-divergent tail rows or build a
sequence-level objective that protects wrong-action branch separation.
```

If hidden-hold produces events but action replay does not:

```text
persistent wrong hidden state is the causal mechanism;
next step should focus on recurrent latent/belief correction and not just
action-sequence boundary mining.
```

If neither action replay nor hidden-hold is source-diverse:

```text
the M486/M487 surface is still too narrow and the task/pair selector must be
rebuilt around terminal outcome sensitivity.
```

## Thresholds

M492 remains diagnostic. It should not promote a checkpoint.

Action-replay diagnostic signal:

```text
wrong_tail_action_replay_K event rows >= 4 for at least one K
wrong_tail_action_replay_K proof rows >= 16 for at least one K
probe_seed_count >= 4
obstacle_label_count >= 2
target_count >= 2
single_seed_share <= 0.65
single_label_share <= 0.85
```

Because this is not promotion proof, event rows may be config-narrow, but the
doc must report config coverage explicitly.

## Implementation Path

M492 should implement a new module or extend M490:

```text
src/autodrift/tail_action_replay_sufficiency_gate.py
```

Recommended helper:

```text
replay_forced_action_prefix(
  model,
  snapshot,
  env_config,
  forced_actions,
  observer_hidden,
  response_dim,
  max_continuation_steps,
  device,
)
```

It should return the same fields as existing replay helpers:

```text
success
collision
obstacle_completed
min_clearance_margin
first_action_distance
action_trajectory_distance_mean/rms/max
terminal_reason
```

## Decision

```text
admit_m492_tail_action_replay_sufficiency_gate_implementation
```

M492 should implement and run this diagnostic on the same M487 critical-window
splits. No checkpoint is promoted.
