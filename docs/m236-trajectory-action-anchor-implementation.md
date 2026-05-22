# M236 Trajectory Action Anchor Implementation

M236 implements a trajectory-level action anchor path for PPO. No PPO is run in
this milestone.

Actor inputs are unchanged.

## Implementation

`src/autodrift/intervention_objectives.py` now includes:

```text
TrajectoryActionAnchor
load_trajectory_action_anchor
trajectory_action_anchor_loss
```

The loader validates:

```text
observation:       N x obs_dim
hidden:            N x hidden_size
reference_action:  N x act_dim
source_index:      N
step_index:        N
weight:            N
```

The loss samples saved trajectory rows and anchors:

```text
tanh(policy_mean(observation, hidden)) -> reference_action
```

using positive finite weights.

`src/autodrift/train_ppo.py` now supports:

```text
trajectory_action_anchor_coef
trajectory_action_anchor_snapshot_npz
trajectory_action_anchor_batch_size
```

When enabled, training logs:

```text
trajectory_action_anchor_loss_mean
```

and prints the loaded trajectory-anchor artifact and row count.

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_intervention_objectives.py tests/test_checkpoints.py
```

Result:

```text
58 passed in 3.13s
```

Syntax check:

```text
python -m compileall -q src tests
```

Result: pass.

## Interpretation

This path is different from the M228/M229 snippet action anchor. Snippet
anchoring protects one decision snapshot. M236 can anchor many teacher-forced
states along a fragile rollout, which directly addresses the M234 diagnosis:
near-boundary proof failures can happen after the first anchored action.

M236 does not claim driver improvement.

## Decision

M236 completes as infrastructure.

Next blocker:

```text
m237-trajectory-anchored-ppo-smoke-from-m224
```

M237 should run exactly one 1024-step PPO smoke from M224 with:

- M232 combined snippet anchor;
- M235 trajectory action anchor;
- existing rollout-state M224 anchor;
- unchanged actor inputs.

It must gate fixed objective, replay, behavior, and protected key before any
repeat or longer PPO.
