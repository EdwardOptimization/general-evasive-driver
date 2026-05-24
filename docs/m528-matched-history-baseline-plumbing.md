# M528 Matched History Baseline Plumbing

## Purpose

M528 implements the smallest matched-history baseline plumbing required after
M527. The goal is to make baseline level explicit in configs and artifacts
before any L0/L2/L3 comparison is treated as evidence.

This is an infrastructure milestone. It does not train a useful driver, does
not promote a checkpoint, and does not change the actor observation contract.

## Implementation

Added `autodrift.history_baselines` with explicit levels:

```text
unspecified
L0_current_observation
L1_one_step_feedback
L2_finite_window
L3_online_gru
```

Explicit levels validate the P0 contract:

```text
include_privileged_params = false
wheel_observation_mode = none
action_history_mode = full
road_lookahead_count = 8
obstacle_slots = 4
```

The train path now records:

```text
PPOConfig.history_baseline_level
run config history_baseline block
checkpoint config history_baseline_level
checkpoint metadata history_baseline block
```

The M528 smoke uses L0:

```text
level: L0_current_observation
actor_encoder: mlp
env history_length: 1
```

Important limitation: this L0 is a feedforward current-frame baseline. The
current P0 frame still includes deployable previous physical command fields,
because those are part of the canonical human-view frame.

## Smoke Command

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo \
  --config configs/ppo_m528_l0_current_observation_smoke.json \
  --device cpu \
  --run-dir runs/m528_l0_current_observation_smoke
```

## Smoke Result

```text
training_device=cpu
num_envs=2
total_steps=64
rollout_steps=16
updates=2
saved=runs/m528_l0_current_observation_smoke/checkpoint.pt
```

Eval summary:

```text
return_mean = 17.82356972950608
steps_mean = 63.0
termination_rate = 1.0
lateral_rmse_mean = 3.4695077520672566
beta_abs_error_mean = 0.20616396393323957
```

These numbers are smoke-only. They verify the route and artifact plumbing; they
are not a baseline performance claim.

## Artifact Checks

`runs/m528_l0_current_observation_smoke/config.json` contains:

```text
history_baseline.level = L0_current_observation
history_baseline.input_contract = P0_human_view_no_wheel_no_oracle
history_baseline.uses_recurrent_hidden = false
history_baseline.uses_finite_window = false
```

`runs/m528_l0_current_observation_smoke/checkpoint.pt` contains:

```text
config.history_baseline_level = L0_current_observation
metadata.history_baseline.level = L0_current_observation
metadata.history_baseline.input_contract = P0_human_view_no_wheel_no_oracle
```

## Validation

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests/test_history_baselines.py
```

Result:

```text
7 passed
```

## Decision

```text
matched_history_baseline_plumbing_smoke_pass_admit_m529_eval_ladder
```

Next blocker:

```text
m529-matched-history-baseline-eval-ladder-design
```
