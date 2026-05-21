# M98 Larger-Batch Per-Target Objective

M98 repeats the M96 equal per-target hidden-envelope objective with more rollout
samples.

M96 was the best objective recipe but missed the strict gate because one seed
had slightly negative lateral after-lift. M97 showed that target-weight tuning
is not robust. M98 therefore returns to the M96 recipe and changes only the
amount of objective data:

```text
contrast_mode = per_target
target_loss_weights = 1.0 1.0 1.0
episodes = 60
max_samples = 1600
steps = 200
```

This is still objective-only. It does not run PPO and does not prove driver
behavior retention.

## Commands

All formal runs use the same settings. Seeds are independent repeats, not tuned
variants.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_optimize \
  --checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 60 \
  --seed 9480 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1600 \
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
  --run-dir runs/m98_larger_batch_per_target_seed9480
```

Repeat with `--seed 9481 --run-dir runs/m98_larger_batch_per_target_seed9481`
and `--seed 9482 --run-dir runs/m98_larger_batch_per_target_seed9482`.

## Results

The table reports held-out `response_hidden - reset_response_hidden` R2 lift.

| seed | samples | target | before | after | delta |
| ---: | ---: | --- | ---: | ---: | ---: |
| 9480 | 1427 | braking | 0.052356 | 0.285544 | 0.233188 |
| 9480 | 1427 | lateral accel | 0.042906 | 0.068964 | 0.026059 |
| 9480 | 1427 | yaw | -0.122657 | 0.005246 | 0.127903 |
| 9481 | 1411 | braking | -0.050519 | 0.087432 | 0.137951 |
| 9481 | 1411 | lateral accel | 0.068294 | 0.066624 | -0.001670 |
| 9481 | 1411 | yaw | 0.003565 | 0.059191 | 0.055626 |
| 9482 | 1411 | braking | -0.032162 | 0.082257 | 0.114419 |
| 9482 | 1411 | lateral accel | 0.083484 | 0.083511 | 0.000027 |
| 9482 | 1411 | yaw | 0.003138 | 0.064771 | 0.061633 |

After optimization:

```text
braking lift is positive in 3 / 3 seeds;
lateral lift is positive in 3 / 3 seeds;
yaw lift is positive in 3 / 3 seeds.
```

MAE deltas:

| seed | target | before MAE lift | after MAE lift | delta |
| ---: | --- | ---: | ---: | ---: |
| 9480 | braking | -0.024154 | 0.103027 | 0.127182 |
| 9480 | lateral accel | 0.073532 | 0.036142 | -0.037390 |
| 9480 | yaw | -0.002607 | 0.012584 | 0.015191 |
| 9481 | braking | -0.020502 | 0.055501 | 0.076003 |
| 9481 | lateral accel | 0.025827 | 0.035489 | 0.009662 |
| 9481 | yaw | 0.000996 | 0.016931 | 0.015935 |
| 9482 | braking | -0.031380 | 0.040832 | 0.072212 |
| 9482 | lateral accel | 0.029623 | 0.022168 | -0.007455 |
| 9482 | yaw | 0.000666 | 0.013345 | 0.012679 |

## Interpretation

M98 is the first strict objective-only hidden-envelope pass.

What this proves:

- The M96 equal per-target contrast recipe can make no-wheel carried response
  hidden beat same-frame reset hidden on braking, lateral, and yaw future
  envelope targets across repeated seeds.
- The M96 lateral negative seed was likely sample-limited or split-sensitive,
  not a reason to abandon equal per-target contrast.
- More objective data is a better lever than M97-style target-weight tuning.

What this does not prove:

- It does not prove behavior retention. The actor head is frozen, but the
  response encoder and GRU changed, so the actor feature distribution changed.
- It does not prove closed-loop self-identification behavior. It only proves a
  supervised hidden-belief diagnostic.
- It does not justify PPO continuation without a retention and intervention
  gate.

## Decision

M98 passes the objective-only admission criterion for hidden-envelope belief.

Next step is not PPO yet. First run a behavior gate on the M98 checkpoints:

```text
M62 baseline vs M98 optimized checkpoints;
normal / reset / zero-current / zero-all / zero-action ablations;
success, termination, clearance margin, and intervention gaps;
reject if aggregate driving behavior regresses before PPO.
```

Only if behavior retention is acceptable should the project attempt a guarded
PPO continuation from the M98 objective checkpoint.
