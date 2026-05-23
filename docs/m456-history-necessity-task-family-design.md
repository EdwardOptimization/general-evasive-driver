# M456 History-Necessity Task Family Design

## Purpose

M455 showed that the M451 robust challenge family is useful for boundary mining
but weak for self-identification evidence. The combined disjoint-window corpus
selected `96` compact rows, but `94/96` were `mixed_dependency`. Aggregate
ablation deltas were also small:

```text
m399_base          0.812500 mean success
m399_reset         0.805990 mean success
m399_zero_response 0.799479 mean success
m399_noact         0.815104 mean success
```

The current robust challenge distribution therefore does not create enough
situations where recurrent command-response history is uniquely useful. M456
designs the next task family to create that evidence directly.

This milestone does not train or promote a checkpoint.

## Diagnosis

The current challenge family has three limitations:

1. The obstacle is visible immediately. The policy can react from current scene
   geometry and current ego response without needing much pre-emergency memory.
2. The same boundary rows often fail under multiple ablations. That produces
   `mixed_dependency`, not clean recurrent-history necessity.
3. The current-response frame is strong. Resetting recurrent hidden still lets
   the GRU consume current `vx`, `vy`, yaw rate, acceleration, actuator state,
   and previous command at every step.

The fix is not to train longer. The fix is to create scenarios where the driver
has useful pre-emergency command-response evidence before the emergency becomes
visible, then evaluate whether replacing or deleting that history changes the
emergency decision.

## Task Family

M456 defines a three-layer history-necessity family.

### Layer A: Late-Reveal Warm-Up Challenge

Use existing env capabilities:

- `obstacle.perception_reveal_distance`
- `obstacle.perception_reveal_step`
- `friction_step.enabled`
- `obstacle.min_time_after_friction_step`

The episode starts with randomized hidden vehicle/road conditions and a short
pre-emergency driving period. The obstacle exists in the simulator, but the
actor does not receive obstacle slot features until it is near enough. A friction
step or hidden-dynamics disturbance happens before reveal, leaving the recurrent
state a chance to encode how the vehicle responded to its own commands.

Actor input remains P0 human-view/no-wheel:

```text
ego response + actuator state + previous commands + road geometry +
ego-frame obstacle geometry after reveal + recurrent hidden
```

No hidden params, labels, TTC, required clearance, reference trajectory, or
feasibility answers are exposed to the actor.

Initial M457 config target:

```text
track_width: 8.0-8.4
speed_range: 12.0-17.0
obstacle.distance_range: 18.0-42.0
obstacle.perception_reveal_distance: 18.0-22.0
obstacle.min_time_after_friction_step: 0.35-0.60
friction_step.step_range: 6-34
friction_step.mu_range: 0.18-1.05
obstacle_relative_velocity_mode: zero
history_length: 1
action_history_mode: full
```

The reveal distance should be late enough that the emergency decision matters,
but not so late that sampling or all policies collapse.

### Layer B: Matched-Current Ambiguity Mining

After Layer A produces runnable episodes, mine snapshots where current visible
state is similar but hidden dynamics/history differ.

Use or extend existing tools:

- `autodrift.matched_current_response_ambiguity`
- `autodrift.hidden_envelope_probe`
- `autodrift.matched_history_intervention_gate`

The mining target is not simply a hard seed. A useful row should satisfy:

```text
current response close
visible context close
obstacle bucket close after reveal
hidden dynamics or recent response history different
future response envelope different
candidate action or outcome sensitive to wrong/delayed/reset history
```

Preferred target signals:

- braking envelope;
- yaw authority;
- lateral acceleration response;
- recovery margin after avoidance;
- terminal obstacle clearance margin;
- road-boundary margin.

This converts “history seems useful” into a matched-current POMDP belief test:
the current observation is nearly the same, but the right action depends on what
the driver learned from prior command-response history.

### Layer C: Wrong-History Intervention Gate

Layer B rows should be replayed with interventions:

```text
normal history
reset recurrent hidden
delayed history
wrong matched history
zero current response
zero action history
```

Promotion-grade evidence requires normal history to beat ablations on the same
matched-current rows. The most important intervention is `wrong matched
history`: if the policy is truly using its belief state, injecting another
vehicle/history should shift the action and reduce margin in a predictable way.

The gate should report separately:

- normal vs reset margin gap;
- normal vs delayed margin gap;
- normal vs wrong-history margin gap;
- normal vs zero-current margin gap;
- normal vs zero-action-history margin gap;
- action divergence and whether wrong history moves toward the wrong pair's
  action.

## Evidence Standard

Do not treat the following as enough:

- aggregate success only;
- broad benchmark tie or small return shift;
- mixed-dependency rows where all ablations fail together;
- current-response-only sensitivity;
- hand-picked single seed success.

Useful evidence starts when a source-diverse corpus contains:

```text
>= 32 matched-current rows
>= 3 seed windows
>= 2 obstacle labels
>= 2 mu buckets
>= 8 wrong-history sensitive rows
>= 8 reset/delayed-history sensitive rows
normal-vs-wrong mean margin gap > 0.02
normal-vs-reset or normal-vs-delayed mean margin gap > 0.01
wrong-history action moves toward paired wrong action in > 60% of rows
```

These thresholds are intentionally preregistered as first-pass diagnostic
targets, not final paper thresholds.

## Redirect Rules

If Layer A cannot sample robustly:

```text
classify as scenario_sampling_failure
repair the config before any training
```

If Layer A runs but M399 and ablations still have tiny differences:

```text
expand matched-current mining before training
```

If matched-current rows remain mostly mixed-dependency:

```text
redesign the task family again:
longer warm-up,
active probing,
mid-episode hidden dynamics changes,
or tighter matched-current pairing.
```

If wrong-history intervention produces strong margin/action degradation:

```text
admit a self-ID gate expansion and only then consider training or objective work.
```

## M457 Implementation Plan

M457 should implement the first runnable Layer A config and run sampling/benchmark
smokes only.

Artifacts:

```text
configs/m457_history_necessity_late_reveal_zero_relvel.json
docs/m457-history-necessity-config-implementation.md
```

Smokes:

```text
reset stress: seeds 9600, 9900, 10150
tiny benchmark: heuristic + M399 base + reset + zero-current + no-action
```

Pass criteria:

- no sampling failures;
- obstacle reveal is not always immediate;
- M399 base success is neither trivially 0 nor trivially 1;
- no actor contract change;
- no checkpoint promotion.

M457 should not claim self-ID. It only establishes that the task family is
runnable enough for matched-current mining.

## Decision

M456 admits:

```text
m457-history-necessity-config-implementation
```

No training and no checkpoint promotion.
