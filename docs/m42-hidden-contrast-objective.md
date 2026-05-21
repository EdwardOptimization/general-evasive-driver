# M42 Hidden-Contrast Objective

Last updated: 2026-05-21

## Motivation

M40/M41 showed that lower response-prediction MSE does not imply stronger
behavior-critical hidden state. M42 adds a small intervention-aware auxiliary
loss: for positive-advantage rollout samples, the normal recurrent hidden state
should assign higher log probability to the executed action than an intervention
that resets hidden state at every step.

This target uses only deployable observations, executed actions, rewards, and
the model's recurrent state. It does not add hidden vehicle parameters or rule
labels to the actor.

## Implementation

New PPO config fields:

```text
hidden_contrast_aux_coef
hidden_contrast_margin
```

For online recurrent sequence training, M42 computes:

```text
softplus(logp_reset_hidden - logp_normal_hidden + margin)
```

weighted by positive advantages. `reset_hidden` means the sequence evaluator
zeros the recurrent state before every step, approximating the deployed
`reset_recurrent_state` ablation.

The trainer logs:

```text
hidden_contrast_loss_mean
```

when the auxiliary is enabled.

## Config

```text
configs/ppo_m42_hidden_contrast_driver.json
```

Key choices:

- init checkpoint: `M37_102`;
- response auxiliary horizon: 4;
- `hidden_contrast_aux_coef = 0.005`;
- `hidden_contrast_margin = 0.05`;
- M38 corpus mix probability: 0.60;
- total steps: 200k.

## Smoke

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m42_hidden_contrast_driver.json \
  --total-steps 4096 \
  --rollout-steps 128 \
  --seed 1842 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m42_hidden_contrast_smoke_seed1842
```

Result:

- init load mode: `strict`;
- training device: `cuda`;
- final smoke step: 4096;
- rollout return mean: 45.17;
- eval return mean: 78.432;
- eval steps mean: 74.300;
- eval termination rate: 0.000;
- final smoke response prediction loss mean: 0.024953;
- final smoke hidden contrast loss mean: 0.640056.

## Full Run Command

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m42_hidden_contrast_driver.json \
  --seed 1842 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m42_hidden_contrast_seed1842
```

## Validation

M42 must be judged against M37_102:

- M38 and M35 response-critical corpus success;
- M29 selected-corpus success;
- broad same-seed success;
- hidden-swap gate;
- reset and zero-response unfavorable outcome-change counts.

The objective only counts as progress if reset/zero-response or hidden-swap
sensitivity improves without losing M37_102 aggregate success.
