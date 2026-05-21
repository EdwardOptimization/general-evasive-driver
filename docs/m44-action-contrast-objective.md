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

## Full Run Result

Run:

```text
runs/ppo_m44_action_contrast_seed1944
```

Final eval:

- return mean: 61.818865;
- steps mean: 62.800;
- termination rate: 0.200;
- lateral RMSE mean: 0.625636;
- beta absolute error mean: 0.180298.

Final train metrics at step 200000:

- response prediction loss mean: 0.019623;
- action contrast loss mean: 0.621962.

## Checkpoint Sweeps

M38 corpus:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.4250 | 37.376 | 0.5750 |
| M37_102 | 0.6250 | 48.034 | 0.3750 |
| M42_028 | 0.6250 | 48.051 | 0.3750 |
| M44_028 | 0.5875 | 45.951 | 0.4125 |
| M44_053 | 0.5875 | 45.941 | 0.4125 |
| M44_077 | 0.6000 | 46.605 | 0.4000 |
| M44_102 | 0.6000 | 46.467 | 0.4000 |
| M44_126 | 0.5875 | 45.763 | 0.4125 |
| M44_151 | 0.5875 | 45.752 | 0.4125 |
| M44_176 | 0.5875 | 45.777 | 0.4125 |
| M44_final | 0.5875 | 45.786 | 0.4125 |

M35 corpus:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.4625 | 40.454 | 0.5375 |
| M37_102 | 0.6500 | 50.262 | 0.3500 |
| M42_028 | 0.6500 | 50.268 | 0.3500 |
| M44_077 | 0.6250 | 48.868 | 0.3750 |
| M44_102 | 0.6250 | 48.716 | 0.3750 |
| M44_final | 0.6125 | 47.982 | 0.3875 |

M29 selected corpus:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.7250 | 61.882 | 0.2750 |
| M30_053 | 0.8750 | 70.795 | 0.1250 |
| M37_102 | 0.8750 | 68.293 | 0.1250 |
| M42_028 | 0.8750 | 68.273 | 0.1250 |
| M44_077 | 0.8750 | 68.448 | 0.1250 |
| M44_102 | 0.8750 | 68.275 | 0.1250 |
| M44_final | 0.8750 | 68.044 | 0.1250 |

Broad same-seed sweep:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.6750 | 56.594 | 0.3000 |
| M30_053 | 0.8250 | 67.732 | 0.1750 |
| M37_102 | 0.8250 | 63.699 | 0.1750 |
| M42_028 | 0.8250 | 63.683 | 0.1750 |
| M44_077 | 0.8000 | 62.684 | 0.2000 |
| M44_102 | 0.8000 | 62.558 | 0.2000 |
| M44_final | 0.7750 | 61.029 | 0.2250 |

## Action-Trajectory Gate

Perturbed accepted matches, 73 / 80:

| Checkpoint | Variant | Success | First action distance | Trajectory mean distance | Trajectory RMS distance | Trajectory max distance |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| M37_102 | hidden_swap | 0.6849 | 0.029597 | 0.005528 | 0.008859 | 0.031880 |
| M42_028 | hidden_swap | 0.6712 | 0.030208 | 0.004872 | 0.008246 | 0.031702 |
| M44_077 | hidden_swap | 0.6712 | 0.039885 | 0.006230 | 0.010728 | 0.042024 |
| M37_102 | reset | 0.6575 | 0.209906 | 0.219339 | 0.224898 | 0.280733 |
| M42_028 | reset | 0.6575 | 0.191957 | 0.200152 | 0.205404 | 0.259158 |
| M44_077 | reset | 0.6575 | 0.309719 | 0.305656 | 0.312178 | 0.382101 |
| M37_102 | zero_response | 0.6575 | 0.113424 | 0.199217 | 0.207295 | 0.268625 |
| M42_028 | zero_response | 0.6438 | 0.105304 | 0.180518 | 0.187769 | 0.243691 |
| M44_077 | zero_response | 0.6575 | 0.145748 | 0.246570 | 0.255472 | 0.325126 |

Outcome changes:

| Checkpoint | Reset | Zero-response | Hidden-swap |
| --- | ---: | ---: | ---: |
| M37_102 | 2 unfavorable / 0 favorable | 2 unfavorable / 0 favorable | 0 |
| M42_028 | 1 unfavorable / 0 favorable | 2 unfavorable / 0 favorable | 0 |
| M44_077 | 2 unfavorable / 1 favorable | 2 unfavorable / 1 favorable | 0 |

## Conclusion

M44 is a negative result. The deterministic action-mean contrast increases
reset and zero-response trajectory action distance, but it does not create
hidden-swap outcome sensitivity and only increases hidden-swap trajectory mean
distance from 0.005528 to 0.006230. It also regresses M38, M35, and broad
success versus M37_102.

The lesson is specific: contrasting against zero hidden teaches the policy to
separate normal hidden from an out-of-distribution reset state, but it does not
teach the policy to distinguish nominal hidden from perturbed hidden. The next
step should target paired nominal/perturbed hidden states directly.
