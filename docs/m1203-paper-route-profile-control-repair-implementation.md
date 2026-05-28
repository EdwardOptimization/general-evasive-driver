# M1203 Paper-Route Profile Control Repair Implementation

## Summary

M1203 implements the diagnostic-control plumbing designed in M1202.

Decision:

```text
profile_control_repair_implementation_ready_for_corrected_runtime_smoke
```

No training, PPO, replay, promotion, or private holdout was run.

## Code Changes

Runtime profile controls:

```text
src/autodrift/controller_profile_runtime.py
```

Changes:

```text
ObservationMaskSpec.history_transform
ObservationMaskSpec.reset_hidden_policy
CURRENT_TILED_HISTORY = "current_tiled"
profile_runtime_summary now records history_transform and reset_hidden_policy
```

`current_tiled` semantics:

```text
frames = obs.reshape(history_length, frame_dim)
frames[1:] = frames[0]
```

This preserves observation shape and actor input contract while removing older
history information for capacity-matched L2 controls.

Evaluation reset policy:

```text
src/autodrift/evaluate.py
```

`ActorPolicy` now accepts `reset_hidden_policy`. For online recurrent actors:

```text
episode_persistent -> carry hidden through the episode
every_step_control -> reset hidden before every action
```

`evaluate_policy` reads `metadata.controller_profile_runtime.reset_hidden_policy`
from checkpoints when available. Older checkpoints without the metadata default
to `episode_persistent`; corrected M1199-style runners should use configs or
newly trained checkpoints that include the runtime summary.

## Tests

Focused verification:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_controller_profile_runtime.py \
  tests/test_controller_profile_train_entrypoint_mask.py \
  tests/test_evaluate_reset_hidden_policy.py
```

Result:

```text
17 passed, 1 warning
```

Covered behavior:

```text
current_tiled preserves shape
current_tiled keeps frame 0 unchanged
current_tiled replaces older frames with frame 0
batched current_tiled observations work
existing L0 previous-command mask still works
unmasked L1/L2 profiles remain unchanged
profile runtime summary records reset_hidden_policy
ActorPolicy carries episode-persistent hidden
ActorPolicy resets every-step-control hidden
```

## Remaining Limits

M1203 does not yet generate committed current-tiled configs and does not rerun
the corrected pilot. It only implements the runtime/eval semantics needed for
those controls.

Unsupported:

```text
L2 history necessity
L3 recurrent-belief advantage
self-identification
profile superiority
promotion
paper-level result
```

## Next Milestone

```text
experiments/manifests/m1204-paper-route-profile-control-repair-smoke-run.json
```

M1204 should smoke test the corrected controls without training:

```text
1. create temporary current-tiled L2 control configs;
2. verify vector/env runtime transforms apply in reset and step paths;
3. verify evaluation reset policy is honored for L3_reset_control;
4. write a small runtime smoke summary before any PPO or pilot rerun.
```
