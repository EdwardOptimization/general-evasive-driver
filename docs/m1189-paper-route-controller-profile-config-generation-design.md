# M1189 Paper-Route Controller Profile Config Generation Design

## Summary

M1189 designs generated config support for the M1188 controller profiles. It is
design-only. It does not generate final train/eval configs, train controllers,
run PPO, run replay, use private holdout, promote, or change actor inputs.

Decision:

```text
controller_profile_config_generation_design_admit_implementation
```

Next manifest:

```text
experiments/manifests/m1190-paper-route-controller-profile-config-generation-implementation.json
```

## Design Goal

The config generator must make L0/L1/L2/L3 comparisons reproducible and
contract-clean before training starts. It should eliminate manual per-profile
JSON editing and produce profile-specific smoke configs with explicit metadata.

## Required Generated Artifacts

The implementation milestone should generate:

```text
configs/paper_route_profiles/m1190_l0_current_masked_smoke.json
configs/paper_route_profiles/m1190_l1_one_step_smoke.json
configs/paper_route_profiles/m1190_l2_window_13_smoke.json
configs/paper_route_profiles/m1190_l2_window_25_smoke.json
configs/paper_route_profiles/m1190_l2_window_50_smoke.json
configs/paper_route_profiles/m1190_l2_window_100_smoke.json
configs/paper_route_profiles/m1190_l3_online_gru_smoke.json
configs/paper_route_profiles/m1190_l3_reset_control_smoke.json
runs/m1190_controller_profile_config_generation/summary.json
runs/m1190_controller_profile_config_generation/config_rows.csv
```

The smoke configs are not training results. They are runnable contract
templates for later smoke runs.

## Base Environment

Use `configs/m121_human_view_zero_obstacle_relvel.json` as the first base
distribution because it already encodes the canonical human-view no-wheel
profile:

```text
history_length: profile-specific
action_history_mode: full
obstacle_relative_velocity_mode: zero
road_lookahead_count: 8
obstacle_slots: 4
wheel_observation_mode: none
include_privileged_params: false
```

The generator must override `history_length` per profile and preserve the rest
of the task distribution unless the manifest explicitly registers a difference.

## PPO Smoke Template

Initial generated PPO smoke configs should use a small, CPU-friendly template:

```text
total_steps: 1024
rollout_steps: 64
num_envs: 2
update_epochs: 1
minibatch_size: 128
hidden_size: 64
learning_rate: 0.0001
clip_coef: 0.10
max_grad_norm: 0.25
eval_episodes: 5
checkpoint_interval_steps: 0
device: cpu
```

The generator must fill:

```text
actor_encoder
actor_history_length
history_baseline_level
recurrent_sequence_training
```

from `src/autodrift/controller_profiles.py`.

No generated config should run during M1190. Running the smoke configs is a
later milestone.

## L0 Runtime Mask Handling

L0 is not equivalent to the existing historical `L0_current_observation`
metadata because the older metadata still allowed previous physical command
fields in the canonical frame. M1187 and M1188 define L0 as:

```text
canonical 72-value frame with fields 9,10,11 masked to zero
```

M1190 should therefore generate explicit metadata:

```json
"controller_profile": {
  "name": "L0_current_masked",
  "observation_mask": "zero_previous_command_fields",
  "previous_command_mask_indices": [9, 10, 11]
}
```

M1190 does not need to modify `train_ppo.py` to apply the mask during training.
It should instead expose the contract clearly and route any runtime-mask
integration to the next implementation milestone if missing.

Acceptance for M1190:

- generated config contains the L0 mask metadata;
- focused tests verify the metadata is present;
- generated env config still instantiates canonical no-oracle human-view obs;
- generated PPO profile fields match `controller_profiles.py`;
- no actual training starts.

## L3 Reset Control Handling

`L3_reset_control` uses the L3 architecture but is not a training profile in
the first implementation. Its config should be generated as metadata-only or
marked:

```json
"training_enabled": false
```

This prevents accidentally training a reset-control policy before the reset
runtime is implemented.

## Contract Checks

M1190 should add tests that verify every generated config:

- has no privileged actor input;
- uses `wheel_observation_mode: none`;
- uses `obstacle_relative_velocity_mode: zero`;
- has `action_history_mode: full`;
- preserves profile-specific `history_length`;
- uses the expected `actor_encoder` and `actor_history_length`;
- carries profile metadata with `uses_hidden_oracle_actor_inputs: false`;
- records `private_holdout_used: false`;
- records `training_started: false` in the generation summary.

## Gate Policy

M1190 remains under Stack A process/infrastructure gates:

```text
make research-validate
focused profile config tests
no training
no private holdout
no actor-input change
```

Stack B becomes active only after generated configs are used for driver
checkpoint training, evaluation, or mechanism claims.

## Follow-Up

If M1190 succeeds, the next milestone should be one of:

```text
M1191 profile config smoke instantiation run
M1191 L0 runtime mask wrapper implementation
```

The correct choice depends on whether M1190 can represent L0 runtime masking
with existing evaluation/training entrypoints. If not, implement the runtime
mask wrapper before training.

## What Is Not Claimed

M1189 does not claim:

- configs are generated;
- any profile is trained;
- L0 mask is applied at runtime;
- finite-window or GRU is better;
- self-identification evidence;
- driver-performance progress.
