# M97 Lateral-Floor Hidden-Envelope Objective

M97 tests whether the M96 near-pass can be fixed with a small lateral emphasis.

M96 used equal per-target contrast and was the best objective so far, but one
seed still had negative lateral `response_hidden - reset_response_hidden` R2
lift. M97 keeps the same per-target contrast and applies a mild lateral floor
through target weights:

```text
contrast_mode = per_target
target_loss_weights = 1.0 1.0 1.25
normalized weights = 0.9230769 0.9230769 1.1538461
```

This remains objective-only training. It does not change actor inputs and does
not run PPO.

## Commands

All formal runs use the same settings. Seeds are independent repeats, not tuned
variants.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_optimize \
  --checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9470 \
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
  --target-loss-weights 1.0 1.0 1.25 \
  --grad-clip-norm 1.0 \
  --device cpu \
  --run-dir runs/m97_lateral_floor_hidden_envelope_seed9470
```

Repeat with `--seed 9471 --run-dir
runs/m97_lateral_floor_hidden_envelope_seed9471` and `--seed 9472 --run-dir
runs/m97_lateral_floor_hidden_envelope_seed9472`.

## Results

The table reports held-out `response_hidden - reset_response_hidden` R2 lift.

| seed | samples | target | before | after | delta |
| ---: | ---: | --- | ---: | ---: | ---: |
| 9470 | 714 | braking | 0.165547 | -0.015814 | -0.181362 |
| 9470 | 714 | lateral accel | -0.004405 | 0.070606 | 0.075011 |
| 9470 | 714 | yaw | 0.296675 | 0.008445 | -0.288230 |
| 9471 | 722 | braking | -0.046239 | 0.042498 | 0.088738 |
| 9471 | 722 | lateral accel | 0.019971 | 0.067743 | 0.047772 |
| 9471 | 722 | yaw | 0.038529 | 0.114699 | 0.076169 |
| 9472 | 715 | braking | 0.035232 | 0.290312 | 0.255079 |
| 9472 | 715 | lateral accel | -0.697397 | -0.683934 | 0.013464 |
| 9472 | 715 | yaw | -3.211453 | -2.387921 | 0.823532 |

After optimization:

```text
braking lift is positive in 2 / 3 seeds;
lateral lift is positive in 2 / 3 seeds;
yaw lift is positive in 2 / 3 seeds;
seed 9472 lateral and yaw remain strongly negative.
```

MAE deltas are mostly positive, but they do not rescue the R2 gate:

| seed | target | before MAE lift | after MAE lift | delta |
| ---: | --- | ---: | ---: | ---: |
| 9470 | braking | 0.031201 | 0.054404 | 0.023204 |
| 9470 | lateral accel | -0.006767 | 0.050733 | 0.057500 |
| 9470 | yaw | 0.022959 | 0.025900 | 0.002941 |
| 9471 | braking | -0.036812 | 0.022445 | 0.059257 |
| 9471 | lateral accel | -0.009693 | 0.019790 | 0.029483 |
| 9471 | yaw | 0.017456 | 0.039667 | 0.022211 |
| 9472 | braking | 0.022334 | 0.120054 | 0.097720 |
| 9472 | lateral accel | -0.208595 | -0.180060 | 0.028535 |
| 9472 | yaw | -0.197362 | -0.165739 | 0.031623 |

## Interpretation

M97 is negative.

The mild lateral overweight does improve lateral in some cases, but it does not
produce a stable all-target objective:

- seed `9470` fixes lateral but turns braking negative and sharply reduces yaw;
- seed `9472` leaves both lateral and yaw strongly negative;
- only seed `9471` passes all three after-lift checks.

The main lesson is that target reweighting is not the right next lever. M96's
equal per-target contrast remains the best current recipe.

## Decision

Do not proceed to PPO continuation.

Do not keep tuning target weights seed-by-seed. The next step should repeat the
M96 equal per-target recipe with a larger batch and more held-out samples before
changing the objective again. That will distinguish:

```text
M96 was a real near-pass but sample-limited;
vs
M96 still lacks enough objective structure for stable all-target belief.
```
