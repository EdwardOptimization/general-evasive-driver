# M1207 Paper-Route Corrected Profile Config Generation

## Summary

M1207 materializes the corrected public pilot configs designed in M1206.

Decision:

```text
corrected_profile_configs_generated_route_to_config_smoke
```

No controller training, PPO, candidate replay, promotion, private holdout, or
profile tuning occurs in M1207.

## Generated Configs

Config directory:

```text
configs/paper_route_corrected_profiles
```

Generated profiles:

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

Run artifact:

```text
runs/m1207_corrected_profile_config_generation/summary.json
runs/m1207_corrected_profile_config_generation/config_rows.csv
```

The summary records:

```text
generated_config_count: 8
current_tiled_profiles: L2_window_13_current_tiled, L2_window_25_current_tiled
corrected_reset_profiles: L3_reset_control_corrected
training_started: false
optimizer_started: false
ppo_used: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
```

## Corrected Semantics

Current-tiled L2 controls:

```text
history_transform: current_tiled
current_tiled_history_control: true
actor_encoder: temporal_gru
actor_history_length: preserved from source L2 profile
env_history_length: preserved from source L2 profile
hidden_size: preserved from source L2 profile
reward/env distribution: preserved from source L2 profile
```

Corrected L3 reset control:

```text
profile: L3_reset_control_corrected
source_profile_name: L3_reset_control
reset_hidden_policy: every_step_control
eval_reset_hidden_policy_enforced: true
actor_encoder: human_view_online_gru
recurrent_sequence_training: false
```

## Budget Metadata

M1207 writes the M1206 corrected pilot protocol into every config:

```text
training_seed_base: 110600
training_seed_offsets: [0, 1, 2]
total_steps: 8192
rollout_steps: 128
num_envs: 4
update_epochs: 2
minibatch_size: 256
device: cpu
vector_env_mode: sync
eval_seed_base: 120600
eval_episodes_per_checkpoint: 64
```

`train_ppo` built-in eval remains `eval_episodes: 1`; the corrected public
pilot runner should produce the fixed 64-episode public evaluation separately.

## Code Changes

New config generator:

```text
src/autodrift/corrected_profile_configs.py
```

Runtime contract update:

```text
src/autodrift/controller_profile_runtime.py
```

`assert_profile_mask_matches_scaffold` now allows generated current-tiled
profile names that intentionally do not exist in the static scaffold, because
their runtime contract is config-declared rather than scaffold-declared.

## Verification

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_corrected_profile_configs.py \
  tests/test_controller_profile_runtime.py \
  tests/test_controller_profile_configs.py \
  tests/test_controller_profile_train_entrypoint_mask.py \
  tests/test_evaluate_reset_hidden_policy.py
```

Result:

```text
28 passed, 1 warning
```

The tests cover:

```text
expected corrected profile set
current-tiled capacity contract preservation
corrected reset-control metadata
no hidden/oracle/wheel/slip/reference/TTC actor inputs
generated JSON summary and config rows
existing runtime mask and evaluation reset-policy behavior
```

## Limits

M1207 is config generation only. It does not produce performance evidence or
history-necessity evidence.

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
experiments/manifests/m1208-paper-route-corrected-profile-config-smoke-run.json
```

M1208 should run a no-training smoke over the generated configs:

```text
1. load all eight generated corrected configs;
2. instantiate AutoDriftEnv and ActorCritic for each config;
3. verify generated current-tiled L2 controls transform reset/step observations;
4. verify generated corrected L3 reset-control routes to every-step-control evaluation semantics;
5. select the corrected public pilot run only if these checks pass.
```
