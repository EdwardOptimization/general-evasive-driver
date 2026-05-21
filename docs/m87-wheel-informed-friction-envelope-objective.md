# M87 Wheel-Informed Friction Bucket Objective

M86 found one narrow wheel-response signal: adding wheel features to body
response improved `mu_bucket` prediction by about `+0.102`, while other hidden
targets did not improve meaningfully. M87 turns that finding into a training
objective:

```text
Use current friction bucket as a training-time auxiliary label.
Do not expose mu or bucket labels to the deployable actor input.
```

The intent is to push the recurrent response stream toward friction/envelope
identification without adding oracle actor inputs.

## Code Change

Added trainer support for:

```text
friction_bucket_aux_coef
```

The labels use the same boundaries as the M86 audit:

```text
low    mu < 0.45
medium 0.45 <= mu < 0.80
high   mu >= 0.80
```

Implementation details:

- rollout stores a per-step friction bucket label from env `info["mu"]`;
- a local training-only linear classifier predicts the bucket from recurrent
  policy features;
- classifier parameters are optimized jointly so gradients flow back into the
  actor feature stack;
- the auxiliary head is not saved in the deployable checkpoint;
- no hidden dynamics value is added to actor observations.

Also added:

```text
friction_bucket_labels_from_mu(...)
recurrent_feature_sequence(...)
```

`infos` are now advanced after each vector-env step, using `reset_info` for
done environments so current observations and current hidden labels stay
aligned.

## Tests

Added focused coverage:

```text
tests/test_checkpoints.py::test_friction_bucket_labels_use_m86_boundaries
tests/test_checkpoints.py::test_train_logs_friction_bucket_auxiliary_loss
```

Focused validation:

```text
2 passed
```

## Config

Added:

```text
configs/ppo_m87_wheel_friction_bucket_aux_driver.json
```

It starts from the M62-to-wheel partial initialization path and uses:

```text
friction_bucket_aux_coef = 0.05
baseline_action_anchor_coef = 0.02
response_prediction_aux_coef = 0.0
response_prediction_dim = 12
```

The response-prediction head remains shape-compatible with M62, but the generic
full 25-value response auxiliary objective from M85 is removed so M87 isolates
the friction-bucket signal.

## Training Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m87_wheel_friction_bucket_aux_driver.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 4087 \
  --device cuda \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m87_wheel_friction_bucket_aux_smoke_seed4087 \
  --eval-episodes 4
```

Load path:

```text
loaded_init_checkpoint=.../alpha_0_25.pt load_mode=partial_wheel_response_encoder
loaded_baseline_action_anchor=.../alpha_0_25.pt load_mode=partial_wheel_response_encoder
```

Built-in eval:

```text
return_mean = 73.76946882258109
steps_mean = 76.0
termination_rate = 0.0
lateral_rmse_mean = 1.3738727378720634
beta_abs_error_mean = 0.1472568903854174
```

Training metric warning:

```text
final friction_bucket_aux_loss_mean = 1.487777
final friction_bucket_aux_accuracy_mean = 0.0
```

The auxiliary classifier is not stable at this smoke scale.

## Ablation Gate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m87_wheel_friction_bucket_aux_driver.json \
  --episodes 20 \
  --seed 8830 \
  --policies heuristic \
  --checkpoint-policy m87=runs/ppo_m87_wheel_friction_bucket_aux_smoke_seed4087/checkpoint.pt \
  --checkpoint-policy m87_zero_wheel=runs/ppo_m87_wheel_friction_bucket_aux_smoke_seed4087/checkpoint.pt@zero_wheel_response \
  --checkpoint-policy m87_reset=runs/ppo_m87_wheel_friction_bucket_aux_smoke_seed4087/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m87_zero_all=runs/ppo_m87_wheel_friction_bucket_aux_smoke_seed4087/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m87_wheel_friction_bucket_aux_gate_seed8830
```

Summary:

| policy | success | termination | return mean | clearance mean | clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | 0.40 | 0.60 | 50.407181 | 0.479831 | -0.231359 |
| m87 | 0.90 | 0.10 | 66.935112 | 2.151812 | -0.082789 |
| m87_reset | 0.85 | 0.15 | 65.955201 | 2.164856 | -0.077695 |
| m87_zero_all | 0.90 | 0.10 | 67.049961 | 2.152575 | -0.068225 |
| m87_zero_wheel | 0.90 | 0.10 | 66.925595 | 2.153372 | -0.083704 |

M87 preserves aggregate behavior, but still does not create wheel dependence.

## Relevance Audit

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.wheel_response_relevance_audit \
  --checkpoint runs/ppo_m87_wheel_friction_bucket_aux_smoke_seed4087/checkpoint.pt \
  --env-config configs/ppo_m87_wheel_friction_bucket_aux_driver.json \
  --episodes 30 \
  --seed 9100 \
  --device cpu \
  --max-samples 1500 \
  --epochs 120 \
  --run-dir runs/m87_wheel_friction_relevance_audit_seed9100
```

Key result:

| target | body | wheel | body+wheel | body+wheel gain |
| --- | ---: | ---: | ---: | ---: |
| mu_bucket | 0.802372 | 0.584980 | 0.802372 | 0.000000 |

Compared with M86, body-only `mu_bucket` prediction improved, but the
body+wheel gain disappeared. The friction objective was apparently satisfied by
body response features rather than by wheel response features.

Response encoder norms:

```text
m85 body_norm  = 7.809560
m85 wheel_norm = 0.058681
m87 body_norm  = 7.812276
m87 wheel_norm = 0.071743
```

Wheel columns increased only slightly and remain tiny.

## Interpretation

M87 is retention-positive but self-ID-negative.

What worked:

- training-time friction labels can be added without actor oracle leakage;
- the checkpoint path remains compatible with M62 partial wheel initialization;
- aggregate obstacle behavior remains strong at `0.90` success.

What failed:

- the friction bucket auxiliary classifier is unstable at this scale;
- zeroing wheel response still does not affect behavior;
- offline probe gain shows the model relies on body response, not wheel response,
  for the friction bucket.

## Decision

The next step should force the auxiliary objective to use wheel evidence rather
than letting body response solve it:

```text
M88: wheel-masked friction auxiliary

compute the friction auxiliary on recurrent features generated from observations
where body response is masked and wheel response is retained;
or use paired body-ambiguous cases where body response cannot solve mu;
then gate normal vs zero-wheel/wrong-wheel history again.
```

Do not claim wheel self-identification from M87.
