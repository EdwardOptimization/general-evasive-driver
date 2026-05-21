# M20 Periodic Response-Retention Sweep

Last updated: 2026-05-21

## Motivation

M19 fine-tuning is a negative result: it starts from the useful M18 checkpoint
but loses the response-dependence signal by the final checkpoint. The failure
mode is partly procedural. The current trainer only saved the final model, so
there was no way to inspect whether an intermediate fine-tune checkpoint had a
better success/self-identification tradeoff.

M20 adds periodic checkpointing and reruns a shorter response-retention
fine-tune from M18. The goal is to select a checkpoint by paired gates rather
than by endpoint training completion.

## Infrastructure Change

`PPOConfig.checkpoint_interval_steps` saves periodic checkpoints under:

```text
<run-dir>/checkpoints/checkpoint_step_<global_step>.pt
```

The checkpoint format is the same strict model-contract format as the final
checkpoint.

## Training Config

Config:

```text
configs/ppo_m20_periodic_response_retention_driver.json
```

Queued command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m20_periodic_response_retention_driver.json \
  --seed 929 \
  --device cuda \
  --init-checkpoint runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt \
  --run-dir runs/ppo_m20_periodic_response_retention_seed929
```

Differences from M19:

- saves a checkpoint every `100000` environment steps;
- stops at `700000` steps, before entering the final base stage that erased the
  M18 response-dependence signal;
- keeps the same deployable online-GRU actor contract;
- uses M18 as the strict same-contract init checkpoint.

## Selection Plan

After training, evaluate the periodic checkpoints on:

- actuator-response paired gate;
- M13 friction paired gate;
- same-corpus obstacle benchmark.

A useful M20 checkpoint must beat M18 or M19 on aggregate success while keeping
normal recurrent inference above response-masked inference. If no checkpoint
does that, the next architecture step should make response-sensitive latent
features feed the actor more directly instead of relying on distribution
pressure alone.

## Result

Training completed at:

```text
runs/ppo_m20_periodic_response_retention_seed929/checkpoint.pt
```

Periodic checkpoints were saved at steps 102400, 200704, 303104, 401408,
503808, 602112, and 700000.

Built-in final evaluation:

- return mean: 78.390;
- steps mean: 65.300;
- termination rate: 0.100;
- lateral RMSE mean: 0.464;
- beta absolute error mean: 0.149.

Actuator-response checkpoint sweep:

| policy | nominal success | perturbed success | drop |
| --- | ---: | ---: | ---: |
| m18 | 0.450 | 0.375 | 0.075 |
| m20_102 | 0.450 | 0.400 | 0.050 |
| m20_200 | 0.450 | 0.375 | 0.075 |
| m20_303 | 0.425 | 0.350 | 0.075 |
| m20_401 | 0.450 | 0.375 | 0.075 |
| m20_503 | 0.425 | 0.375 | 0.050 |
| m20_602 | 0.375 | 0.400 | -0.025 |
| m20_700 | 0.475 | 0.400 | 0.075 |

Top-candidate actuator-response gate:

| policy | nominal success | perturbed success | drop |
| --- | ---: | ---: | ---: |
| m20_102 | 0.450 | 0.400 | 0.050 |
| m20_102_reset | 0.150 | 0.325 | -0.175 |
| m20_102_zero_current | 0.450 | 0.375 | 0.075 |
| m20_102_zero_all | 0.450 | 0.375 | 0.075 |
| m20_700 | 0.475 | 0.400 | 0.075 |
| m20_700_reset | 0.375 | 0.375 | 0.000 |
| m20_700_zero_current | 0.475 | 0.400 | 0.075 |
| m20_700_zero_all | 0.475 | 0.400 | 0.075 |

Top-candidate M13 friction gate:

| policy | nominal success | perturbed success | drop |
| --- | ---: | ---: | ---: |
| m20_102 | 0.825 | 0.400 | 0.425 |
| m20_102_reset | 0.575 | 0.175 | 0.400 |
| m20_102_zero_current | 0.775 | 0.400 | 0.375 |
| m20_102_zero_all | 0.775 | 0.400 | 0.375 |
| m20_700 | 0.875 | 0.425 | 0.450 |
| m20_700_reset | 0.725 | 0.350 | 0.375 |
| m20_700_zero_current | 0.850 | 0.425 | 0.425 |
| m20_700_zero_all | 0.850 | 0.425 | 0.425 |

Same-corpus obstacle benchmark:

| policy | success | termination | high sideslip |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.250 | 0.750 | 0.000 |
| m20_102 | 0.450 | 0.550 | 0.010 |
| m20_700 | 0.475 | 0.525 | 0.000 |
| m20_700_reset | 0.400 | 0.600 | 0.001 |
| m20_700_zero_current | 0.475 | 0.525 | 0.000 |
| m20_700_zero_all | 0.475 | 0.525 | 0.000 |

Conclusion: M20 improves the aggregate checkpoint selection story but does not
pass the self-identification gate. `m20_700` is the best current same-contract
checkpoint on the near-threshold corpus, with success `0.475` versus
`envelope_aes` at `0.250`, and it improves M13 friction perturbed success to
`0.425`. However, response masking does not reduce `m20_700` success. The
policy still appears able to solve too much through geometry and recurrent
state without depending on the deployable response channels. The next
experiment should change the actor architecture or loss so response-conditioned
latent state is directly control-critical.
