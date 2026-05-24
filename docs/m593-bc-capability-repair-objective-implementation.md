# M593 BC Capability Repair Objective Implementation

## Purpose

M593 implements the first capability-supervised hidden repair objective
infrastructure selected by M592.

This milestone is infrastructure-only:

```text
no real checkpoint training
no PPO
no route evaluation
no checkpoint promotion
```

## Implementation

M593 adds:

```text
src/autodrift/bc_capability_repair.py
tests/test_bc_capability_repair.py
```

The new module provides:

- `CapabilityHead`: training-only MLP head from recurrent hidden state to
  future-response capability targets;
- z-score Huber capability regression loss;
- matched-current capability ranking loss;
- action BC and action-anchor losses;
- weighted total repair loss;
- metadata helper that preserves P0 actor contract and marks outputs as
  unpromoted/non-PPO.

The target names are the existing simulator-probe targets:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
```

These remain training/evaluation labels only. They are not actor inputs.

## Objective

The implemented total loss is:

```text
L = w_bc     * L_action_bc
  + w_reg    * L_capability_regression
  + w_rank   * L_capability_rank
  + w_anchor * L_action_anchor
```

Where:

```text
L_action_bc = ||action - teacher_action||^2
L_capability_regression = SmoothL1(zscore(prediction) - zscore(target))
L_capability_rank = softplus(target_margin - signed_prediction_delta)
L_action_anchor = ||action - anchor_action||^2
```

This implements the M592 principle:

```text
make hidden state informative before forcing actions apart
```

## Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_bc_capability_repair.py \
  tests/test_l3_behavior_cloning.py
```

Result:

```text
7 passed
```

The tests verify:

- capability regression loss decreases on a synthetic hidden-to-target mapping;
- capability ranking loss is lower for correctly ordered predictions;
- total repair loss is finite and differentiable through action and capability
  predictions;
- metadata preserves `P0_human_view_no_wheel_no_oracle`,
  `human_view_online_gru`, `actor_history_length = 1`, and marks `ppo_used =
  false`, `promoted = false`.

## Scope Limit

M593 intentionally does not train a real checkpoint.

Reason:

```text
the real repair needs a corpus/runner that aligns future-response capability
targets with rollout hidden states and action anchors.
```

The existing BC corpora contain:

```text
student_obs_seq
teacher_action_seq
episode/step metadata
```

They do not directly contain simulator state or future-response targets. M594
therefore needs to design the real capability corpus/runner before any smoke
training.

## Decision

```text
bc_capability_repair_objective_implementation_admit_corpus_design
```

M593 passes because it implements and tests the training-only objective
building blocks while preserving the P0 actor contract and avoiding PPO,
promotion, or driver-performance claims.

## Next

```text
M594: design the capability repair corpus/runner for a real smoke.
```
