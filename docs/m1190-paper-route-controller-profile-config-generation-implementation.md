# M1190 Paper-Route Controller Profile Config Generation Implementation

## Summary

M1190 implements generated smoke configs for the paper-route controller
profiles. The implementation is:

```text
src/autodrift/controller_profile_configs.py
tests/test_controller_profile_configs.py
```

Generated configs:

```text
configs/paper_route_profiles/m1190_l0_current_masked_smoke.json
configs/paper_route_profiles/m1190_l1_one_step_smoke.json
configs/paper_route_profiles/m1190_l2_window_13_smoke.json
configs/paper_route_profiles/m1190_l2_window_25_smoke.json
configs/paper_route_profiles/m1190_l2_window_50_smoke.json
configs/paper_route_profiles/m1190_l2_window_100_smoke.json
configs/paper_route_profiles/m1190_l3_online_gru_smoke.json
configs/paper_route_profiles/m1190_l3_reset_control_smoke.json
```

This milestone did not run the generated configs. It did not train
controllers, run PPO, run candidate replay, use private holdout, promote, or
change actor inputs.

## Command

```text
PYTHONPATH=src python -m autodrift.controller_profile_configs --output-dir configs/paper_route_profiles --run-dir runs/m1190_controller_profile_config_generation
```

Run artifacts:

```text
runs/m1190_controller_profile_config_generation/summary.json
runs/m1190_controller_profile_config_generation/config_rows.csv
```

Summary:

```text
result_class: controller_profile_configs_generated
generated_config_count: 8
l2_window_steps: [13, 25, 50, 100]
l0_observation_mask: zero_previous_command_fields
l0_previous_command_mask_indices: [9, 10, 11]
training_started: false
optimizer_started: false
ppo_used: false
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
```

## Config Contract

Each generated config has:

```text
controller_profile
ppo
env
```

The `controller_profile` block records:

- profile name and level;
- observation mask metadata;
- previous-command mask indices for L0;
- allowed and forbidden inputs;
- hidden/oracle input flags;
- `training_enabled`;
- private-holdout status.

The `ppo` block records smoke-scale settings and profile-specific fields:

```text
actor_encoder
actor_history_length
history_baseline_level
recurrent_sequence_training
hidden_size
```

The `env` block is derived from `configs/m121_human_view_zero_obstacle_relvel.json`
with profile-specific history length and contract-clean settings.

## L0 Runtime Caveat

The generated L0 config correctly records:

```text
observation_mask: zero_previous_command_fields
previous_command_mask_indices: [9, 10, 11]
```

However, M1190 does not modify `train_ppo.py`, `evaluate.py`, or policy
wrappers to apply this mask at runtime. Therefore the next step must implement
runtime mask application before any L0 training or evaluation run.

## Verification

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_profile_configs.py tests/test_controller_profiles.py
```

Result:

```text
13 passed
```

The focused tests verify:

- all eight profile configs can be generated;
- L0 includes runtime mask metadata;
- L2 covers 13, 25, 50, and 100 step windows;
- L3 reset control has `training_enabled=false`;
- env configs instantiate canonical no-oracle human-view observation spaces;
- summary flags report no training, PPO, or private holdout.

## Decision

```text
controller_profile_configs_generated_route_to_runtime_mask_wrapper
```

Next milestone:

```text
experiments/manifests/m1191-paper-route-observation-mask-runtime-wrapper-implementation.json
```

M1191 should implement a runtime observation-mask wrapper or policy adapter for
profile-aware evaluation/training entrypoints. No L0 training should start
until the mask is actually applied.

## What Is Not Claimed

M1190 does not claim:

- generated configs were trained;
- L0 mask is applied at runtime;
- any controller performance;
- finite-window or GRU superiority;
- self-identification evidence;
- private-holdout readiness.
