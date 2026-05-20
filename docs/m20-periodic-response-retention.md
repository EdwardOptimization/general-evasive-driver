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
