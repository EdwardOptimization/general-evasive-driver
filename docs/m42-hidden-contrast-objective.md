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

## Full Run Result

Run:

```text
runs/ppo_m42_hidden_contrast_seed1842
```

Final eval:

- return mean: 78.523250;
- steps mean: 75.500;
- termination rate: 0.000;
- lateral RMSE mean: 1.019109;
- beta absolute error mean: 0.163743.

Final train metrics at step 200000:

- response prediction loss mean: 0.016727;
- hidden contrast loss mean: 0.530701.

M42 trained cleanly, but the loss decrease did not translate into a stronger
behavior-critical recurrent state.

## Checkpoint Sweeps

M38 corpus:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.4250 | 37.376 | 0.5750 |
| M37_102 | 0.6250 | 48.034 | 0.3750 |
| M39_053 | 0.6375 | 48.934 | 0.3625 |
| M42_028 | 0.6250 | 48.051 | 0.3750 |
| M42_053 | 0.6000 | 46.610 | 0.4000 |
| M42_077 | 0.5875 | 45.865 | 0.4125 |
| M42_102 | 0.6000 | 46.534 | 0.4000 |
| M42_126 | 0.5875 | 45.821 | 0.4125 |
| M42_151 | 0.5875 | 45.762 | 0.4125 |
| M42_176 | 0.5875 | 45.787 | 0.4125 |
| M42_final | 0.6125 | 47.209 | 0.3875 |

M35 corpus:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.4625 | 40.454 | 0.5375 |
| M37_102 | 0.6500 | 50.262 | 0.3500 |
| M42_028 | 0.6500 | 50.268 | 0.3500 |
| M42_final | 0.6375 | 49.400 | 0.3625 |

M29 selected corpus:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.7250 | 61.882 | 0.2750 |
| M30_053 | 0.8750 | 70.795 | 0.1250 |
| M37_102 | 0.8750 | 68.293 | 0.1250 |
| M42_028 | 0.8750 | 68.273 | 0.1250 |
| M42_final | 0.8750 | 68.226 | 0.1250 |

Broad same-seed sweep:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.6750 | 56.594 | 0.3000 |
| M30_053 | 0.8250 | 67.732 | 0.1750 |
| M37_102 | 0.8250 | 63.699 | 0.1750 |
| M42_028 | 0.8250 | 63.683 | 0.1750 |
| M42_final | 0.8000 | 62.030 | 0.2000 |

M42_028 is the best M42 checkpoint. It preserves M37_102 on M35, M29, and
broad sweeps, but it does not improve M38 and later checkpoints regress.

## Hidden-Swap Gate

Same seed range, 80 episodes, 73 accepted visible matches:

| Checkpoint | Perturbed normal success | Reset changes | Zero-response changes | Hidden-swap changes |
| --- | ---: | ---: | ---: | ---: |
| M37_102 | 0.6849 | 2 unfavorable / 0 favorable | 2 unfavorable / 0 favorable | 0 |
| M42_028 | 0.6712 | 1 unfavorable / 0 favorable | 2 unfavorable / 0 favorable | 0 |

Accepted perturbed first-action distance:

| Checkpoint | Reset | Zero-response | Hidden-swap |
| --- | ---: | ---: | ---: |
| M37_102 | 0.209906 | 0.113424 | 0.029597 |
| M42_028 | 0.191957 | 0.105304 | 0.030208 |

The hidden-contrast objective does not create hidden-swap outcome sensitivity.
It also weakens reset action distance and reset outcome changes versus M37_102.

## Conclusion

M42 is a negative result. The infrastructure is valid and the auxiliary loss is
trainable, but stochastic log-probability contrast against reset hidden does
not make the deployed deterministic policy more recurrent-state critical.
M37_102 remains the current best checkpoint.

The next step should not be a blind continuation of M42. M43 should first
measure deterministic action-trajectory divergence under reset, zero-response,
and hidden-swap interventions, then use that evidence to choose a stronger
behavior-sensitive training objective.
