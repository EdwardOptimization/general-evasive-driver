# M519 Valid-Offset Projection Outcome Redesign

## Purpose

M519 redesigns the next projection-aware outcome gate after M518 shows that the
pre-registered tail offset set is invalid for near-terminal projected rows.

No gate is run in M519. No training, PPO, actor-input change, checkpoint update,
or checkpoint promotion is performed.

## M518 Blocker

M518 preserved relocated obstacle geometry and produced valid replay rows, but
classified the formal run as:

```text
invalid_projection_replay
```

The invalid audit found:

```text
invalid rows total: 318

by tail_offset:
  8: 239
  4: 48
  2: 31

missing_left_tail:
  true: 318

missing_right_tail:
  false: 318
```

The issue is mechanical: many M516 rows are already near the terminal boundary.
Requesting `left_step + 8` often asks for a left snapshot after the left rollout
has already terminated. Since every `tail_offset=8` row is invalid, M518 cannot
be used as an outcome conclusion about the controller.

## Redesign

M520 should rerun the same projection-aware gate with valid offsets:

```text
tail_offsets: 0,2,4
```

This keeps the M517 semantics intact:

```text
normal_projected
wrong_projected_once
reset_projected
zero_current_projected
zero_action_history_projected
```

It must still:

```text
preserve relocated obstacle geometry
separate wrong-history rows from reset/zero controls
report source/target/config/geometry diversity
classify the result explicitly
avoid training or checkpoint promotion
keep the actor contract unchanged
```

The M518 invalid audit implies `0,2,4` will remove the globally invalid offset
while retaining short-tail history tests. Some `offset=2` and `offset=4` rows
may still be invalid; that is acceptable if invalid rows no longer dominate the
gate. The formal M520 classifier should still report invalid counts and reject
only if invalid rows exceed the validity threshold.

## Decision Rules For M520

M520 should use the M518 classification taxonomy:

```text
positive_projected_wrong_history_outcome_proof
margin_only_projected_history_signal
control_only_projected_sensitivity
fast_correction_no_effect
projected_wrong_history_no_effect
invalid_projection_replay
```

Interpretation:

```text
positive_projected_wrong_history_outcome_proof:
  wrong_projected_once has event rows or source-diverse proof rows.

margin_only_projected_history_signal:
  wrong_projected_once changes margins but has no event rows.

control_only_projected_sensitivity:
  reset/zero controls degrade but wrong_projected_once does not.

fast_correction_no_effect:
  wrong_projected_once changes actions but closed-loop feedback removes
  outcome differences.

invalid_projection_replay:
  valid offsets still cannot replay enough projected rows.
```

If M520 again shows no meaningful wrong-history outcome effect while reset/zero
controls remain stronger, the next branch should not force more artificial
wrong-history proof rows. It should start an L0/L1/L2/L3 history-value ablation:

```text
L0: current observation only
L1: one-step command-response feedback
L2: finite command-response window
L3: online GRU recurrent belief
```

The purpose would be to measure whether multi-step recurrent belief improves
capability-envelope prediction and near-boundary control beyond one-frame
feedback.

## Decision

```text
admit_m520_valid_offset_projection_outcome_gate
```

Next blocker:

```text
m520-valid-offset-projection-outcome-gate
```
