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
