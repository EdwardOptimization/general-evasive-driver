# M34 Response-Aux Mixed Training

Last updated: 2026-05-21

## Motivation

M30 improved aggregate success but still failed recurrent self-identification:
hidden-swap remained outcome-neutral. M34 adds a deployable auxiliary loss that
requires the recurrent state to predict the next response stream.

The auxiliary target is not an oracle. It uses only the next observed
human-view response features:

```text
vx, vy, yaw_rate, ax, ay, steering state, steering rate,
throttle state, brake state, previous steering/throttle/brake command
```

This is the canonical first 12 values of the 72-value human-view observation.

## Implementation

Config:

```text
configs/ppo_m34_response_aux_mixed_driver.json
```

Key fields:

- init checkpoint: `m30_053`;
- `response_prediction_aux_coef = 0.05`;
- `response_prediction_dim = 12`;
- M29 hard seed mix probability: 0.65;
- `vector_env_mode = parallel`;
- total steps: 300k.

The init checkpoint loader now allows exactly one partial-init case: adding a
new response-prediction head to an otherwise compatible actor. Other missing,
unexpected, or shape-mismatched weights still fail.

## Smoke

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m34_response_aux_mixed_driver.json \
  --total-steps 4096 \
  --rollout-steps 128 \
  --seed 1434 \
  --device cuda \
  --init-checkpoint runs/ppo_m30_mixed_matched_response_seed1330/checkpoints/checkpoint_step_53248.pt \
  --run-dir runs/ppo_m34_response_aux_smoke_seed1434
```

Result:

- load mode: `partial_response_prediction_head`;
- training device: `cuda`;
- final smoke step: 4096;
- rollout return mean: 76.98;
- eval return mean: 70.377;
- eval steps mean: 65.400;
- eval termination rate: 0.200.

Conclusion: M34 trains end to end and can initialize from M30_053 while adding
the response-prediction auxiliary head.

## Full Run Plan

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m34_response_aux_mixed_driver.json \
  --seed 1434 \
  --device cuda \
  --init-checkpoint runs/ppo_m30_mixed_matched_response_seed1330/checkpoints/checkpoint_step_53248.pt \
  --run-dir runs/ppo_m34_response_aux_mixed_seed1434
```

Post-run gates:

- M29 selected-corpus checkpoint sweep;
- broad same-seed benchmark;
- M28/M30 hidden-swap gate;
- reset and zero-response ablations.
