# M96 Per-Target Hidden-Envelope Objective

M96 tests the smallest correction after M95.

M95 stabilized braking by using per-target contrast plus a higher braking
weight, but it sacrificed lateral response. M96 keeps the useful per-target
contrast and removes the braking overweight:

```text
contrast_mode = per_target
target_loss_weights = 1.0 1.0 1.0
normalized weights = 1.0 1.0 1.0
```

The actor observation contract is unchanged. This is still objective-only
hidden-envelope training, not PPO.

## Commands

All formal runs use the same settings. Seeds are independent repeats, not tuned
variants.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_optimize \
  --checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9460 \
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
  --target-loss-weights 1.0 1.0 1.0 \
  --grad-clip-norm 1.0 \
  --device cpu \
  --run-dir runs/m96_per_target_balanced_hidden_envelope_seed9460
```

Repeat with `--seed 9461 --run-dir
runs/m96_per_target_balanced_hidden_envelope_seed9461` and `--seed 9462
--run-dir runs/m96_per_target_balanced_hidden_envelope_seed9462`.

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
| 9460 | 729 | braking | -0.058331 | 0.086932 | 0.145263 |
| 9460 | 729 | lateral accel | -0.095185 | -0.040365 | 0.054821 |
| 9460 | 729 | yaw | -0.007534 | 0.016726 | 0.024260 |
| 9461 | 730 | braking | -0.131870 | 0.066797 | 0.198667 |
| 9461 | 730 | lateral accel | 0.012886 | 0.004757 | -0.008130 |
| 9461 | 730 | yaw | 0.033236 | 0.075936 | 0.042699 |
| 9462 | 729 | braking | -0.145999 | 0.079167 | 0.225166 |
| 9462 | 729 | lateral accel | 0.009430 | 0.010814 | 0.001384 |
| 9462 | 729 | yaw | -0.001484 | 0.151876 | 0.153360 |

After optimization:

```text
braking lift is positive in 3 / 3 seeds;
yaw lift is positive in 3 / 3 seeds;
lateral lift is positive in 2 / 3 seeds;
seed 9460 lateral remains negative, but improves from -0.095185 to -0.040365.
```

MAE deltas:

| seed | target | before MAE lift | after MAE lift | delta |
| ---: | --- | ---: | ---: | ---: |
| 9460 | braking | -0.025775 | 0.077501 | 0.103277 |
| 9460 | lateral accel | -0.053670 | -0.023687 | 0.029982 |
| 9460 | yaw | 0.004921 | 0.018796 | 0.013875 |
| 9461 | braking | -0.070631 | 0.033661 | 0.104293 |
| 9461 | lateral accel | 0.006899 | -0.026375 | -0.033274 |
| 9461 | yaw | 0.003521 | 0.023606 | 0.020085 |
| 9462 | braking | -0.067524 | 0.068106 | 0.135630 |
| 9462 | lateral accel | 0.007482 | 0.021671 | 0.014188 |
| 9462 | yaw | 0.000803 | 0.036032 | 0.035229 |

## Interpretation

M96 is the best no-wheel hidden-envelope objective so far, but it still misses
the strict PPO-admission rule.

What improved:

- Braking and yaw both become positive after optimization in all three seeds.
- Lateral no longer collapses like M95; two seeds are positive and the remaining
  negative seed improves substantially.
- Removing braking overweight fixed most of the M95 lateral tradeoff while
  preserving the M95 braking gain.

Remaining blocker:

- The strict objective-only gate requires all three future-envelope targets to
  beat reset hidden across repeated seeds. Seed `9460` lateral remains negative
  (`-0.040365`), and seed `9461` lateral MAE lift regresses.

## Decision

Do not proceed to PPO continuation yet.

M96 is a near-pass objective recipe. The next iteration should target the
remaining lateral weakness without reintroducing braking instability:

```text
use equal per-target contrast as the base;
add a small lateral floor or minimum-lift penalty;
or alternate target-balanced minibatches with a gate on minimum after-lift;
rerun repeated seeds before PPO.
```

M96 checkpoints are diagnostics, not driver candidates.
