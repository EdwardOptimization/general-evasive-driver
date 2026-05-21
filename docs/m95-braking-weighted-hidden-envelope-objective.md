# M95 Braking-Weighted Hidden-Envelope Objective

M95 is the direct follow-up to M94.

M94 showed that the fixed-batch no-wheel hidden-envelope objective can move
response hidden, but braking was unstable across repeated seeds. M95 changes
only the objective weighting and contrast shape before any PPO continuation.

This is still not a promoted driver. It is an objective-only diagnostic.

## Objective Change

M94 used one scalar contrast over the mean error across all targets:

```text
relu(margin + mean(normal_error) - mean(reset_error))
```

That can allow yaw or lateral improvements to hide braking regression. M95 adds
two controls to `autodrift.hidden_envelope_optimize`:

```text
--contrast-mode mean | per_target
--target-loss-weights BRAKING YAW LATERAL
```

The formal M95 recipe is:

```text
contrast_mode = per_target
target_loss_weights = 3.0 1.0 1.0
normalized weights = 1.8 0.6 0.6
```

The actor input contract is unchanged. The optimizer still freezes:

```text
actor head
critic
context encoder
log_std
```

and trains only:

```text
response_encoder
online_gru_cell
temporary envelope head
```

## Commands

All formal runs use the same settings. Seeds are independent repeats, not tuned
variants.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_optimize \
  --checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9450 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --train-fraction 0.70 \
  --ridge 0.1 \
  --steps 200 \
  --batch-size 256 \
  --learning-rate 0.0003 \
  --contrast-coef 0.5 \
  --contrast-margin 0.02 \
  --contrast-mode per_target \
  --target-loss-weights 3.0 1.0 1.0 \
  --grad-clip-norm 1.0 \
  --device cpu \
  --run-dir runs/m95_braking_weighted_hidden_envelope_seed9450
```

Repeat with `--seed 9451 --run-dir
runs/m95_braking_weighted_hidden_envelope_seed9451` and `--seed 9452
--run-dir runs/m95_braking_weighted_hidden_envelope_seed9452`.

Artifacts per seed:

```text
samples.csv
train_metrics.csv
head_metrics.csv
probe_summary.csv
hidden_gain_summary.csv
optimized_checkpoint.pt
summary.json
manifest.json
```

## Results

The table reports held-out `response_hidden - reset_response_hidden` R2 lift.
Positive means carried response history is more predictive than same-frame reset
hidden.

| seed | samples | target | before | after | delta |
| ---: | ---: | --- | ---: | ---: | ---: |
| 9450 | 751 | braking | -0.043913 | 0.093007 | 0.136921 |
| 9450 | 751 | lateral accel | 0.010328 | -0.230815 | -0.241143 |
| 9450 | 751 | yaw | 0.004378 | -0.004631 | -0.009009 |
| 9451 | 763 | braking | -0.031724 | 0.059400 | 0.091123 |
| 9451 | 763 | lateral accel | 0.019025 | 0.045079 | 0.026054 |
| 9451 | 763 | yaw | -0.040891 | 0.059469 | 0.100360 |
| 9452 | 761 | braking | -0.641132 | 0.644474 | 1.285606 |
| 9452 | 761 | lateral accel | -0.821348 | -0.207891 | 0.613457 |
| 9452 | 761 | yaw | 0.429459 | 0.494708 | 0.065250 |

After optimization:

```text
braking lift is positive in 3 / 3 seeds;
yaw lift is positive in 2 / 3 seeds, with seed 9450 near zero but negative;
lateral lift is positive in 1 / 3 seeds and negative in 2 / 3 seeds.
```

MAE deltas tell the same tradeoff:

| seed | target | before MAE lift | after MAE lift | delta |
| ---: | --- | ---: | ---: | ---: |
| 9450 | braking | -0.011526 | 0.112834 | 0.124361 |
| 9450 | lateral accel | -0.013616 | -0.032557 | -0.018941 |
| 9450 | yaw | -0.001885 | 0.010719 | 0.012605 |
| 9451 | braking | -0.017208 | 0.053016 | 0.070224 |
| 9451 | lateral accel | -0.018119 | -0.003499 | 0.014621 |
| 9451 | yaw | -0.008128 | 0.015627 | 0.023755 |
| 9452 | braking | -0.197983 | 0.167968 | 0.365951 |
| 9452 | lateral accel | -0.338968 | -0.143932 | 0.195036 |
| 9452 | yaw | 0.057858 | 0.075189 | 0.017331 |

## Interpretation

M95 is useful but still not PPO-admissible.

What improved:

- Braking was the M94 failure mode, and M95 makes braking normal-vs-reset lift
  positive in all three formal seeds.
- Per-target contrast prevents braking from being silently masked by the other
  two targets.
- The optimizer remains no-wheel and objective-only, so the actor observation
  contract stays clean.

What failed:

- Lateral belief is sacrificed in two of three seeds.
- Yaw is not uniformly stronger: seed `9450` moves slightly negative.
- The objective is still fighting among targets through one shared hidden state
  and one temporary linear head.

## Decision

Do not proceed to PPO continuation from M95.

M95 establishes that the braking instability is controllable, but the current
weighted scalar recipe trades away lateral/yaw stability. The next objective
iteration should decouple targets before behavior training, for example:

```text
separate per-target heads;
target-balanced or alternating minibatches;
gate on minimum after-lift across braking/yaw/lateral;
only admit PPO if all three targets are stable across repeated seeds.
```

M95 checkpoints are diagnostics, not driver candidates.
