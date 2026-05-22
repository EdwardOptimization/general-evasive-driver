# M257 Trajectory-Anchored Projection Implementation

M257 is an infrastructure milestone. It adds trajectory action anchor support
to `outcome_intervention_optimize` so the next post-PPO projection can protect
closed-loop trajectory rows such as M183/M170 row16 while repairing protected
source loss. No PPO was run and no driver checkpoint was promoted.

## Context

M256 showed that protected-source projection from the M254 raw PPO checkpoint
can strongly improve exact source losses, but the projection direction breaks
the knife-edge M183/M170 row16 proof surface at every tested interpolation
alpha. The M235 trajectory anchor surface already contains row16 and the
protected key, but `outcome_intervention_optimize` could not use that anchor.

M257 closes that tooling gap only.

## Implementation

`src/autodrift/outcome_intervention_optimize.py` now supports:

```text
--trajectory-action-anchor-snapshot-npz
--trajectory-action-anchor-coef
--trajectory-action-anchor-batch-size
```

When enabled, the optimizer loads the existing
`TrajectoryActionAnchor` NPZ format from `intervention_objectives`, adds
`trajectory_action_anchor_loss` to the projection loss, and records:

```text
trajectory_action_anchor_loss
trajectory_action_anchor_coef
before_trajectory_action_anchor_mse
after_trajectory_action_anchor_mse
trajectory_action_anchor_snapshot_npz
trajectory_action_anchor_batch_size
```

The implementation reuses the same trajectory-anchor semantics already used by
`train_ppo`; it does not change actor inputs or trajectory anchor format.

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_outcome_intervention_optimize.py \
  tests/test_intervention_objectives.py \
  tests/test_checkpoints.py
```

Result:

```text
65 passed in 3.68s
```

Compile check:

```text
python -m compileall -q src tests
```

Result: pass.

Real-anchor smoke, using the M253 base and M235 trajectory anchor:

```text
runs/m257_trajectory_anchor_optimizer_smoke
```

Key summary values:

| Metric | Value |
| --- | ---: |
| trajectory anchor coef | 0.1 |
| trajectory anchor batch size | 2 |
| before trajectory anchor MSE | 0.0000000961 |
| after trajectory anchor MSE | 0.0000001322 |
| sampled loss improvement | 0.000003040 |

The smoke confirms the optimizer can load the real M235 trajectory anchor and
log the new trajectory-anchor metrics.

## Decision

Complete M257 as infrastructure. It does not prove a driver improvement. The
next research step is to retry the M256 post-PPO projection with the M235
trajectory anchor enabled and gate it with exact source metrics before public
proof gates.

Next task:

```text
m258-trajectory-anchored-projection-retry
```
