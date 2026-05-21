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

## Full Run Result

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m34_response_aux_mixed_driver.json \
  --seed 1434 \
  --device cuda \
  --init-checkpoint runs/ppo_m30_mixed_matched_response_seed1330/checkpoints/checkpoint_step_53248.pt \
  --run-dir runs/ppo_m34_response_aux_mixed_seed1434
```

Run artifacts:

- final checkpoint: `runs/ppo_m34_response_aux_mixed_seed1434/checkpoint.pt`;
- periodic checkpoints: steps 53248, 102400, 151552, 200704, 253952, and
  300000;
- command log: `runs/research/m34-response-aux-mixed-training_20260521T035144Z/command.log`.

Final eval:

- return mean: 70.148;
- steps mean: 65.900;
- termination rate: 0.200;
- lateral RMSE mean: 0.656;
- beta absolute error mean: 0.166.

M29 selected-corpus checkpoint sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.725 | 61.882 | 0.275 |
| M26_602 | 0.775 | 66.875 | 0.225 |
| M30_053 | 0.875 | 70.795 | 0.125 |
| M34_053 | 0.875 | 70.368 | 0.125 |
| M34_102 | 0.875 | 69.758 | 0.125 |
| M34_151 | 0.875 | 69.411 | 0.125 |
| M34_200 | 0.850 | 68.202 | 0.150 |
| M34_253 | 0.850 | 68.479 | 0.150 |
| M34_final | 0.850 | 68.993 | 0.150 |

Broad 40-seed checkpoint sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.675 | 56.594 | 0.300 |
| M26_602 | 0.800 | 67.765 | 0.200 |
| M30_053 | 0.825 | 67.732 | 0.175 |
| M34_053 | 0.825 | 66.798 | 0.175 |
| M34_102 | 0.800 | 64.655 | 0.200 |
| M34_151 | 0.825 | 65.783 | 0.175 |
| M34_final | 0.775 | 63.909 | 0.225 |

Hidden-swap gates for M34_053, M34_102, and M34_151:

- accepted visible matches: 73 / 80 for all three checkpoints;
- hidden-swap success outcome changes: 0 for all three checkpoints;
- perturbed reset outcome changes: 1, 2, and 3 respectively;
- perturbed zero-response outcome changes: 2, 3, and 3 respectively.

## Conclusion

M34 is a mixed negative result. It preserves M30_053-level aggregate success at
early checkpoints but does not improve it. More importantly, it still fails the
self-identification gate: hidden-swap remains outcome-neutral.

The useful signal is that response-prediction auxiliary training creates a
small number of current-response ablation outcome changes. M35 therefore
expands M34_151 hidden-swap mining and builds a response-change corpus instead
of treating M34 as a pass.
