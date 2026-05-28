# M1192 Paper-Route Controller Profile Runtime Smoke Run

## Summary

M1192 runs the integrated no-training runtime smoke for all generated
controller-profile configs:

```text
configs/paper_route_profiles/m1190_*_smoke.json
```

It verifies that config metadata, runtime observation masking, `AutoDriftEnv`
instantiation, and `ActorCritic` instantiation are compatible before any
controller training starts.

M1192 does not train controller weights, run PPO, run candidate replay, use
private holdout, promote, evaluate driver performance, or add hidden/oracle
actor inputs.

## Artifacts

```text
src/autodrift/controller_profile_runtime_smoke.py
tests/test_controller_profile_runtime_smoke.py
runs/m1192_controller_profile_runtime_smoke/summary.json
runs/m1192_controller_profile_runtime_smoke/profile_runtime_rows.csv
```

## Smoke Result

Command:

```text
PYTHONPATH=src python -m autodrift.controller_profile_runtime_smoke --config-dir configs/paper_route_profiles --run-dir runs/m1192_controller_profile_runtime_smoke --seed 1192
```

Result:

```text
result_class: controller_profile_runtime_smoke_pass
config_count: 8
all_configs_instantiated: true
l0_mask_observed: true
unmasked_profiles_unchanged: true
contract_ok: true
model_forward_ok: true
training_started: false
optimizer_started: false
ppo_used: false
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
```

Profile rows:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
L3_reset_control
```

L0 runtime-mask observation:

```text
raw_step_previous_command_abs_sum: 1.4500000476837158
wrapped_step_previous_command_abs_sum: 0.0
```

This confirms the wrapper is doing real runtime work after a nonzero control
step, not merely observing naturally-zero reset fields.

## Verification

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_profile_runtime_smoke.py tests/test_controller_profile_runtime.py tests/test_controller_profile_configs.py tests/test_controller_profiles.py
```

Result:

```text
25 passed
```

## Decision

```text
controller_profile_runtime_smoke_pass_route_to_training_smoke_design
```

M1193 should design a bounded fair training-smoke protocol for the L0/L1/L2/L3
profile comparison before any controller training run is launched.

## What Is Not Claimed

M1192 does not claim:

- any profile has been trained;
- any profile performs well;
- finite-window or GRU superiority;
- recurrent belief advantage;
- self-identification evidence;
- private-holdout readiness;
- paper-level result readiness.
