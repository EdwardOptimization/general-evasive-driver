# M30 Mixed Hard-Corpus Training

Last updated: 2026-05-21

## Motivation

M23 showed that hard-only seed replay can overfit and damage broad obstacle
performance. M29 produced a useful matched hard corpus, but it should not be
used as the only reset distribution. M30 adds mixed hard-seed sampling so hard
matched cases can be oversampled while ordinary randomized resets remain active.

## Infrastructure Change

`PPOConfig` now supports:

```text
training_seed_mix_probability
```

When `training_seed_csv` is set:

- `1.0` keeps the old hard-only behavior;
- `0.0` disables the seed corpus and uses ordinary deterministic vector-env
  seeds;
- values between 0 and 1 sample hard corpus seeds with that probability and
  default randomized seeds otherwise.

This keeps the actor input clean. The seed corpus only controls simulator reset
selection during training; it is not an actor observation.

## Config

```text
configs/ppo_m30_mixed_matched_response_driver.json
```

Key choices:

- init from `m26_602`;
- train with `human_view_online_gru`;
- use `runs/m29_matched_response_corpus_seed4200/scenario_corpus.csv`;
- `training_seed_mix_probability = 0.65`;
- checkpoint every 50k steps;
- low learning rate `6e-5`;
- 300k total steps.

## Smoke

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m30_mixed_matched_response_driver.json \
  --total-steps 20480 \
  --seed 1330 \
  --device cuda \
  --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --run-dir runs/ppo_m30_mixed_matched_response_smoke_seed1330
```

Result:

- strict init checkpoint load succeeded;
- training device: `cuda`;
- final smoke step: 20480;
- rollout return mean: 59.95;
- eval return mean: 69.080;
- eval steps mean: 61.900;
- eval termination rate: 0.100;
- checkpoint: `runs/ppo_m30_mixed_matched_response_smoke_seed1330/checkpoint.pt`.

Smoke conclusion: the mixed seed sampler and M30 config train end to end.

## Full Run Plan

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m30_mixed_matched_response_driver.json \
  --seed 1330 \
  --device cuda \
  --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --run-dir runs/ppo_m30_mixed_matched_response_seed1330
```

After full training, evaluate:

- M29 selected corpus success;
- M28 hidden-swap gate;
- broad same-seed human-view obstacle benchmark;
- reset, zero-response, and hidden-swap ablations.
