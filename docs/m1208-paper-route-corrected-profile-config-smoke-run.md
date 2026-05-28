# M1208 Paper-Route Corrected Profile Config Smoke Run

## Summary

M1208 runs a no-training runtime smoke over the generated M1207 corrected
profile configs.

Decision:

```text
corrected_profile_config_smoke_pass_route_to_corrected_pilot_run
```

No controller training, PPO, candidate replay, promotion, private holdout, or
profile tuning occurs in M1208.

## Command

```text
PYTHONPATH=src python -m autodrift.controller_profile_runtime_smoke \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --run-dir runs/m1208_corrected_profile_config_smoke \
  --seed 1208
```

## Artifacts

```text
runs/m1208_corrected_profile_config_smoke/summary.json
runs/m1208_corrected_profile_config_smoke/profile_runtime_rows.csv
```

## Smoke Result

```text
result_class: controller_profile_runtime_smoke_pass
config_count: 8
all_configs_instantiated: true
contract_ok: true
model_forward_ok: true
l0_mask_observed: true
unmasked_profiles_unchanged: true
current_tiled_profile_count: 2
current_tiled_profiles_observed: true
corrected_reset_profile_count: 1
corrected_reset_policy_routing_ok: true
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
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L3_online_gru
L3_reset_control_corrected
```

## Corrected-Control Checks

Current-tiled controls:

```text
L2_window_13_current_tiled raw_step_current_tiled: false
L2_window_13_current_tiled wrapped_step_current_tiled: true
L2_window_13_current_tiled current_tiled_observed: true
L2_window_25_current_tiled raw_step_current_tiled: false
L2_window_25_current_tiled wrapped_step_current_tiled: true
L2_window_25_current_tiled current_tiled_observed: true
```

This proves the generated configs route through the runtime history transform,
not merely through naturally identical reset frames.

Corrected reset control:

```text
L3_reset_control_corrected reset_hidden_policy: every_step_control
L3_reset_control_corrected reset_policy_routing_ok: true
```

The smoke uses `ActorPolicy` routing with a spy recurrent model to verify that
`every_step_control` resets hidden before the action call.

## Code Changes

`src/autodrift/controller_profile_runtime_smoke.py` now supports:

```text
--config-glob
current_tiled runtime-transform checks
corrected reset-policy routing checks
```

The old M1192 smoke path still works with the default `m1190_*_smoke.json`
glob.

## Verification

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_controller_profile_runtime_smoke.py \
  tests/test_controller_profile_runtime.py \
  tests/test_corrected_profile_configs.py \
  tests/test_evaluate_reset_hidden_policy.py
```

Result:

```text
26 passed
```

## Limits

M1208 only proves generated-config runtime readiness. It does not train any
profile and does not provide profile performance evidence.

Unsupported:

```text
finite-window history necessity
GRU recurrent-belief advantage
self-identification
profile superiority
promotion
private-holdout generalization
paper-level result
```

## Next Milestone

```text
experiments/manifests/m1209-paper-route-corrected-profile-pilot-run.json
```

M1209 may run the fixed corrected public pilot under the M1206/M1207 budget:

```text
8 profiles
3 training seeds per profile
8192 PPO steps per seed
64 fixed public eval episodes per checkpoint
no private holdout
no promotion
no per-profile tuning
no self-ID or paper-level claim
```
