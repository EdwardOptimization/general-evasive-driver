# M44 Action-Contrast Objective

Last updated: 2026-05-21

## Motivation

M43 showed that hidden-swap produces only a tiny sustained action difference:
about 0.005 mean action-trajectory distance on perturbed accepted matches,
while reset and zero-response produce about 0.18 to 0.22. M42's log-probability
contrast was trainable but did not change this deterministic closed-loop
behavior.

M44 therefore targets deterministic action means directly. The objective is not
proof of self-identification; it is a test of whether a small action-mean
contrast can make recurrent hidden state harder to ignore than log-probability
contrast did.

## Implementation

New PPO config fields:

```text
action_contrast_aux_coef
action_contrast_margin
```

For online recurrent sequence training, M44 computes the squashed deterministic
action mean for:

- the normal recurrent hidden sequence;
- a reset-hidden intervention that zeros hidden state before every step.

For positive-advantage rollout samples, it adds:

```text
softplus(action_contrast_margin - ||a_normal - a_reset||_2)
```

The trainer logs:

```text
action_contrast_loss_mean
```

when the auxiliary is enabled.

## Config

```text
configs/ppo_m44_action_contrast_driver.json
```

Key choices:

- init checkpoint: `M37_102`;
- response auxiliary horizon: 4;
- `action_contrast_aux_coef = 0.003`;
- `action_contrast_margin = 0.18`;
- M38 corpus mix probability: 0.60;
- total steps: 200k.

## Smoke

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m44_action_contrast_driver.json \
  --total-steps 4096 \
  --rollout-steps 128 \
  --seed 1944 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m44_action_contrast_smoke_seed1944
```

Result:

- init load mode: `strict`;
- training device: `cuda`;
- final smoke step: 4096;
- rollout return mean: 40.875;
- eval return mean: 61.995;
- eval steps mean: 62.800;
- eval termination rate: 0.200;
- final smoke response prediction loss mean: 0.023666;
- final smoke action contrast loss mean: 0.680256.

The smoke only proves that the objective is trainable and logged. It is not a
positive policy result because the short smoke eval is weaker than the M37/M42
smoke evals.

## Full Run Command

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m44_action_contrast_driver.json \
  --seed 1944 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m44_action_contrast_seed1944
```

## Validation

M44 must be judged against M37_102 and M42_028:

- M38 and M35 response-critical corpus success;
- M29 selected-corpus success;
- broad same-seed success;
- M43 action-trajectory hidden-swap gate;
- reset and zero-response unfavorable outcome-change counts.

The objective only counts as progress if hidden-swap trajectory action distance
or outcome sensitivity improves without losing M37_102 aggregate success.
