# M1191 Paper-Route Observation Mask Runtime Wrapper Implementation

## Summary

M1191 implements runtime observation-mask support for controller-profile
configs. The implementation is:

```text
src/autodrift/controller_profile_runtime.py
tests/test_controller_profile_runtime.py
```

This turns the M1190 L0 mask metadata into executable runtime behavior. It
does not train controllers, run PPO, run candidate replay, use private holdout,
promote, or add hidden/oracle actor inputs.

## Runtime Support

The new runtime module provides:

```text
ObservationMaskSpec
mask_spec_from_config
mask_spec_from_profile_name
apply_runtime_observation_mask
ControllerProfileObservationWrapper
wrap_env_with_profile_mask
profile_runtime_summary
assert_profile_mask_matches_scaffold
```

The wrapper applies profile-declared observation masks at env reset/step time.
For `L0_current_masked`, it zeros the previous-command fields:

```text
indices: [9, 10, 11]
mask: zero_previous_command_fields
```

Unmasked profiles return unchanged observations and `wrap_env_with_profile_mask`
returns the original env instance.

## Verification

Focused command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_profile_runtime.py tests/test_controller_profile_configs.py tests/test_controller_profiles.py
```

Result:

```text
22 passed
```

The tests verify:

- L0 runtime mask zeros fields `9,10,11`;
- stacked-frame masking works;
- L1 and L2 unmasked profiles are unchanged;
- all generated unmasked L1/L2/L3 configs leave observations unchanged;
- `AutoDriftEnv` reset and step observations are masked through
  `ControllerProfileObservationWrapper`;
- runtime masks match the scaffold profile masks;
- runtime summary reports no training, PPO, private holdout, hidden/oracle
  inputs, or wheel/slip inputs.

## Decision

```text
runtime_observation_mask_ready_route_to_profile_runtime_smoke
```

Next milestone:

```text
experiments/manifests/m1192-paper-route-controller-profile-runtime-smoke-run.json
```

M1192 should instantiate the generated L0/L1/L2/L3 configs with runtime mask
handling and write a smoke artifact. It should not train or evaluate
performance.

## What Is Not Claimed

M1191 does not claim:

- L0/L1/L2/L3 training has started;
- generated configs produce good policies;
- finite-window or GRU superiority;
- driver-performance improvement;
- self-identification evidence;
- private-holdout readiness.
