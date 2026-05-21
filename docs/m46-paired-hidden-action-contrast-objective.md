# M46 Paired-Hidden Action Contrast Objective

Last updated: 2026-05-21

## Motivation

M44 proved that reset-hidden action contrast is the wrong target: it increases
reset and zero-response action distances, but it does not transfer to
hidden-swap. M45 exported matched nominal/perturbed observations and recurrent
hidden states from M37_102, giving a direct data source for the actual hidden
states that the gate swaps.

M46 is a conservative same-checkpoint fine-tuning objective. It starts from
M37_102 and uses the M45 snapshot NPZ, so the saved hidden vectors are still in
the checkpoint's original latent space at initialization.

## Implementation

New PPO config fields:

```text
paired_hidden_action_contrast_aux_coef
paired_hidden_action_contrast_margin
paired_hidden_snapshot_npz
paired_hidden_snapshot_batch_size
```

For each sampled snapshot pair, M46 evaluates deterministic squashed action
means under:

- nominal observation with nominal hidden;
- nominal observation with perturbed hidden;
- perturbed observation with perturbed hidden;
- perturbed observation with nominal hidden.

It then adds:

```text
softplus(margin - ||a_own_hidden - a_paired_hidden||_2)
```

for both source conditions. The trainer logs:

```text
paired_hidden_action_contrast_loss_mean
```

## Config

```text
configs/ppo_m46_paired_hidden_action_contrast_driver.json
```

Key choices:

- init checkpoint: `M37_102`;
- snapshot NPZ:
  `runs/m45_m37_102_paired_hidden_snapshots_seed4300/snapshots.npz`;
- response auxiliary horizon: 4;
- `paired_hidden_action_contrast_aux_coef = 0.0015`;
- `paired_hidden_action_contrast_margin = 0.08`;
- snapshot batch size: 128;
- M38 corpus mix probability: 0.60;
- total steps: 200k.

## Smoke

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m46_paired_hidden_action_contrast_driver.json \
  --total-steps 4096 \
  --rollout-steps 128 \
  --seed 2046 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m46_paired_hidden_action_contrast_smoke_seed2046
```

Result:

- init load mode: `strict`;
- training device: `cuda`;
- final smoke step: 4096;
- rollout return mean: 37.319;
- eval return mean: 82.897;
- eval steps mean: 77.200;
- eval termination rate: 0.000;
- final smoke response prediction loss mean: 0.025627;
- final smoke paired-hidden action contrast loss mean: 0.718800.

The smoke proves trainability and metric logging only. It does not prove
self-identification or aggregate robustness.

## Full Run Command

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m46_paired_hidden_action_contrast_driver.json \
  --seed 2046 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m46_paired_hidden_action_contrast_seed2046
```

## Validation

M46 must be judged against M37_102 and M42_028:

- M38 and M35 response-critical corpus success;
- M29 selected-corpus success;
- broad same-seed success;
- M43 action-trajectory hidden-swap gate;
- reset and zero-response unfavorable outcome-change counts.

The objective only counts as progress if hidden-swap trajectory action distance
or outcome sensitivity improves without losing M37_102 aggregate success.

## Full Run Result

Run directory:

```text
runs/ppo_m46_paired_hidden_action_contrast_seed2046
```

Final eval:

- return mean: 83.167580;
- steps mean: 77.700;
- termination rate: 0.000;
- lateral RMSE mean: 0.979150;
- beta absolute error mean: 0.113100.

Final train metrics at step 200000:

- response prediction loss mean: 0.022801;
- paired-hidden action contrast loss mean: 0.709751.

## Checkpoint Sweeps

M38 response-critical corpus:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.4250 | 37.376 | 0.5750 |
| M37_102 | 0.6250 | 48.034 | 0.3750 |
| M42_028 | 0.6250 | 48.051 | 0.3750 |
| M46_028 | 0.6000 | 46.693 | 0.4000 |
| M46_053 | 0.6250 | 48.170 | 0.3750 |
| M46_077 | 0.6375 | 48.844 | 0.3625 |
| M46_102 | 0.6125 | 47.460 | 0.3875 |
| M46_126 | 0.6250 | 48.110 | 0.3750 |
| M46_151 | 0.6125 | 47.496 | 0.3875 |
| M46_176 | 0.6250 | 48.065 | 0.3750 |
| M46_200 | 0.6375 | 48.724 | 0.3625 |
| M46_final | 0.6375 | 48.724 | 0.3625 |

M35 response-change corpus:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.4625 | 40.454 | 0.5375 |
| M37_102 | 0.6500 | 50.262 | 0.3500 |
| M42_028 | 0.6500 | 50.268 | 0.3500 |
| M46_077 | 0.6500 | 50.337 | 0.3500 |
| M46_200 | 0.6500 | 50.216 | 0.3500 |

M29 selected corpus:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.7250 | 61.882 | 0.2750 |
| M30_053 | 0.8750 | 70.795 | 0.1250 |
| M37_102 | 0.8750 | 68.293 | 0.1250 |
| M42_028 | 0.8750 | 68.273 | 0.1250 |
| M46_077 | 0.8750 | 68.352 | 0.1250 |
| M46_200 | 0.8750 | 68.272 | 0.1250 |

Broad same-seed sweep:

| Policy | Success | Return | Collision |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.6750 | 56.594 | 0.3000 |
| M30_053 | 0.8250 | 67.732 | 0.1750 |
| M37_102 | 0.8250 | 63.699 | 0.1750 |
| M42_028 | 0.8250 | 63.683 | 0.1750 |
| M46_077 | 0.8000 | 63.039 | 0.2000 |
| M46_200 | 0.8000 | 62.585 | 0.2000 |

M46 lightly improves the M38 mined corpus but fails the broad aggregate gate.
Therefore it cannot replace M37_102.

## Action-Trajectory Gate

Accepted perturbed matches:

| Checkpoint | Accepted | Variant | Success | First action distance | Trajectory mean distance | Trajectory RMS distance | Trajectory max distance |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| M37_102 | 73 | hidden_swap | 0.6849 | 0.029597 | 0.005528 | 0.008859 | 0.031880 |
| M42_028 | 73 | hidden_swap | 0.6712 | 0.030208 | 0.004872 | 0.008246 | 0.031702 |
| M44_077 | 73 | hidden_swap | 0.6712 | 0.039885 | 0.006230 | 0.010728 | 0.042024 |
| M46_077 | 73 | hidden_swap | 0.6712 | 0.033754 | 0.006379 | 0.010098 | 0.036450 |
| M46_200 | 72 | hidden_swap | 0.6806 | 0.036984 | 0.007083 | 0.010772 | 0.037673 |
| M46_077 | 73 | reset | 0.6575 | 0.223550 | 0.230402 | 0.236469 | 0.299842 |
| M46_200 | 72 | reset | 0.6528 | 0.266067 | 0.249862 | 0.255192 | 0.310395 |
| M46_077 | 73 | zero_response | 0.6438 | 0.119659 | 0.199611 | 0.207800 | 0.270195 |
| M46_200 | 72 | zero_response | 0.6528 | 0.106308 | 0.169107 | 0.174300 | 0.220236 |

Outcome changes on accepted pairs:

| Checkpoint | Reset | Zero-response | Hidden-swap |
| --- | ---: | ---: | ---: |
| M37_102 | 2 unfavorable / 0 favorable | 2 unfavorable / 0 favorable | 0 |
| M42_028 | 1 unfavorable / 0 favorable | 2 unfavorable / 0 favorable | 0 |
| M44_077 | 2 unfavorable / 1 favorable | 2 unfavorable / 1 favorable | 0 |
| M46_077 | 1 unfavorable / 0 favorable | 2 unfavorable / 0 favorable | 0 |
| M46_200 | 2 unfavorable / 0 favorable | 2 unfavorable / 0 favorable | 0 |

M46 increases hidden-swap trajectory distance slightly, but hidden-swap outcome
changes remain 0 and the broad benchmark regresses. The static M45 hidden
snapshots are therefore not enough as a standalone objective. The next
objective should use on-policy or continuation-level evidence rather than only
forcing action-mean separation on fixed offline hidden vectors.

## Conclusion

M46 is a negative result. It is trainable and gives a small M38 corpus gain, but
it fails the aggregate broad gate and does not create hidden-swap outcome
sensitivity. Current best remains M37_102.
