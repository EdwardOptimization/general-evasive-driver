# M1195 Paper-Route Train Entrypoint Profile Mask Integration

## Summary

M1195 integrates controller-profile observation masks into train/eval vector
paths. This closes the blocker identified by M1193/M1194: `L0_current_masked`
could not be trained safely until `train_ppo` and vector env construction
applied the same runtime mask that M1191/M1192 verified in single-env smoke.

M1195 does not train controllers, run PPO, run candidate replay, use private
holdout, promote, evaluate driver performance, or add hidden/oracle actor
inputs.

## Implementation

Files:

```text
src/autodrift/vector_env.py
src/autodrift/train_ppo.py
tests/test_controller_profile_train_entrypoint_mask.py
```

Vector env integration:

```text
SyncAutoDriftVectorEnv(..., observation_mask_spec=...)
ParallelAutoDriftVectorEnv(..., observation_mask_spec=...)
```

Both reset and step observations pass through the optional
`ObservationMaskSpec`. Done-triggered reset observations are also masked.

Train/eval entrypoint integration:

```text
train_ppo main reads top-level controller_profile metadata
mask_spec_from_config(raw_config)
make_vector_env(..., observation_mask_spec=profile_mask_spec)
train(..., observation_mask_spec=profile_mask_spec)
evaluate_actor(..., observation_mask_spec=profile_mask_spec)
```

Old configs without `controller_profile` keep the old behavior because the mask
spec is optional.

## Verification

Focused command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_profile_train_entrypoint_mask.py tests/test_controller_profile_runtime.py tests/test_controller_profile_runtime_smoke.py
```

Result:

```text
15 passed
```

The focused tests verify:

```text
sync vector env masks L0 reset and step observations
sync vector env raw L0 step has nonzero previous-command signal
sync vector env masked L0 step zeros fields [9,10,11]
sync vector env leaves unmasked L1 observations unchanged
parallel vector env masks L0 reset and step observations
```

## Decision

```text
train_entrypoint_profile_mask_integration_ready_for_stage_a_training_smoke
```

The next milestone may run the M1193 Stage A bounded training smoke:

```text
L0_current_masked
L1_one_step
L2_window_25
L3_online_gru
1024 steps
2 envs
1 seed
CPU
no performance claim
no promotion
no private holdout
```

## What Is Not Claimed

M1195 does not claim:

- any controller has trained successfully;
- PPO improves any profile;
- finite-window or GRU superiority;
- driver performance;
- self-identification evidence;
- private-holdout readiness;
- paper-result readiness.
