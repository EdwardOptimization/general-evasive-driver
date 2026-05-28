# M1188 Paper-Route Controller Profile Scaffold Implementation

## Summary

M1188 implements controller-profile scaffolding for the paper-route L0/L1/L2/L3
comparison. The implementation is:

```text
src/autodrift/controller_profiles.py
tests/test_controller_profiles.py
```

This is infrastructure only. It does not train controllers, run PPO, run
candidate replay, promote a checkpoint, use private holdout, or change actor
inputs.

## Implemented Profiles

The scaffold defines eight profiles:

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

Profile meanings:

- `L0_current_masked`: canonical 72-value human-view frame with previous
  command fields `9,10,11` masked to zero.
- `L1_one_step`: canonical 72-value one-step command-response feedback frame.
- `L2_window_*`: finite-window temporal-GRU profiles with no online recurrent
  hidden state.
- `L3_online_gru`: online human-view GRU with episode-persistent hidden state.
- `L3_reset_control`: online-GRU architecture with hidden reset every step for
  recurrent-memory control.

The L2 step counts map to the current environment `dt = 0.02s`:

```text
13 steps  -> 0.26s, closest scaffold to 0.25s
25 steps  -> 0.50s
50 steps  -> 1.00s
100 steps -> 2.00s
```

## Contract

Every profile is marked as:

```text
P0_human_view_no_wheel_no_oracle
```

The scaffold keeps:

```text
hidden_or_oracle_actor_inputs: false
wheel_or_slip_actor_inputs: false
reference_or_ttc_inputs: false
actor_input_contract_changed: false
```

Profile environment configs force:

```text
action_history_mode: full
include_privileged_params: false
privileged_observation_mode: basic
obstacle_relative_velocity_mode: zero
wheel_observation_mode: none
road_lookahead_count: 8
obstacle_slots: 4
```

## Smoke Artifact

Command:

```text
PYTHONPATH=src python -m autodrift.controller_profiles --run-dir runs/m1188_controller_profile_scaffold_smoke
```

Artifact:

```text
runs/m1188_controller_profile_scaffold_smoke/summary.json
runs/m1188_controller_profile_scaffold_smoke/profile_rows.csv
```

Summary:

```text
result_class: controller_profile_scaffold_ready
profile_count: 8
finite_window_steps: [13, 25, 50, 100]
l0_previous_command_mask_indices: [9, 10, 11]
training_started: false
optimizer_started: false
ppo_used: false
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
```

## Verification

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_profiles.py
```

Result:

```text
7 passed
```

The focused tests verify:

- all profile names exist;
- L0 masks only previous-command fields;
- profile env configs instantiate canonical no-oracle human-view observations;
- `ActorCritic` can instantiate L0, L1, L2, L3, and L3 reset profiles without
  training;
- PPO override metadata is contract-clean;
- forbidden hidden/oracle input flags stay false;
- smoke artifact writing works.

## Decision

```text
controller_profile_scaffold_ready_route_to_config_generation_design
```

The next step should design config generation for the profile matrix before any
controller training:

```text
experiments/manifests/m1189-paper-route-controller-profile-config-generation-design.json
```

## What Is Not Claimed

M1188 does not claim:

- any L0/L1/L2/L3 controller has been trained;
- any profile performs better;
- finite-window or GRU superiority;
- self-identification evidence;
- driver-performance improvement;
- private-holdout readiness.
