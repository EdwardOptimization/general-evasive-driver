# M88 Wheel-Masked Friction Auxiliary

M87 added a training-time friction bucket auxiliary objective, but the
post-training relevance audit showed that the objective was solved through body
response instead of wheel response. M88 tests a stricter variant:

```text
For the friction auxiliary branch only:
  zero body response features;
  keep wheel response features;
  classify friction bucket from response GRU hidden state.
```

The deployable actor observation remains unchanged. The mask is only used for
the auxiliary loss.

## Code Change

Added two config fields:

```text
friction_bucket_aux_observation_mask = "none" | "wheel_only"
friction_bucket_aux_feature_source = "policy_features" | "response_hidden"
```

M87 uses the default:

```text
none + policy_features
```

M88 uses:

```text
wheel_only + response_hidden
```

The `wheel_only` mask:

- zeros observation indices `0:12`;
- keeps wheel response indices `12:25`;
- keeps scene/context indices `25:85`.

The `response_hidden` feature source trains from the recurrent response hidden
state instead of the fused policy feature, reducing context shortcuts.

## Tests

Added:

```text
tests/test_checkpoints.py::test_wheel_only_friction_aux_mask_zeros_body_response_only
tests/test_checkpoints.py::test_train_logs_wheel_masked_friction_bucket_auxiliary_loss
```

Focused validation:

```text
2 passed
```

## Config

Added:

```text
configs/ppo_m88_wheel_masked_friction_aux_driver.json
```

It starts from M62 partial wheel initialization and uses:

```text
friction_bucket_aux_coef = 0.05
friction_bucket_aux_observation_mask = "wheel_only"
friction_bucket_aux_feature_source = "response_hidden"
baseline_action_anchor_coef = 0.02
```

## Training Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m88_wheel_masked_friction_aux_driver.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 4188 \
  --device cuda \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m88_wheel_masked_friction_aux_smoke_seed4188 \
  --eval-episodes 4
```

Built-in eval:

```text
return_mean = 63.07621677339177
steps_mean = 63.25
termination_rate = 0.25
lateral_rmse_mean = 0.8077934906888538
beta_abs_error_mean = 0.13097580600168007
```

Final friction auxiliary metrics:

```text
friction_bucket_aux_loss_mean = 1.121625
friction_bucket_aux_accuracy_mean = 0.285156
```

The masked auxiliary is not strong, but it is more stable than the final M87
update, which ended at `0.0` accuracy.

## Ablation Gate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m88_wheel_masked_friction_aux_driver.json \
  --episodes 20 \
  --seed 8830 \
  --policies heuristic \
  --checkpoint-policy m88=runs/ppo_m88_wheel_masked_friction_aux_smoke_seed4188/checkpoint.pt \
  --checkpoint-policy m88_zero_wheel=runs/ppo_m88_wheel_masked_friction_aux_smoke_seed4188/checkpoint.pt@zero_wheel_response \
  --checkpoint-policy m88_reset=runs/ppo_m88_wheel_masked_friction_aux_smoke_seed4188/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m88_zero_all=runs/ppo_m88_wheel_masked_friction_aux_smoke_seed4188/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m88_wheel_masked_friction_aux_gate_seed8830
```

Summary:

| policy | success | termination | return mean | clearance mean | clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | 0.40 | 0.60 | 50.407181 | 0.479831 | -0.231359 |
| m88 | 0.85 | 0.15 | 68.861229 | 2.074297 | -0.117997 |
| m88_reset | 0.80 | 0.20 | 66.271420 | 2.040547 | -0.113620 |
| m88_zero_all | 0.85 | 0.15 | 68.270256 | 2.053676 | -0.113666 |
| m88_zero_wheel | 0.85 | 0.15 | 68.797596 | 2.075091 | -0.118709 |

M88 still does not pass a wheel-dependence gate.

## Relevance Audit

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.wheel_response_relevance_audit \
  --checkpoint runs/ppo_m88_wheel_masked_friction_aux_smoke_seed4188/checkpoint.pt \
  --env-config configs/ppo_m88_wheel_masked_friction_aux_driver.json \
  --episodes 30 \
  --seed 9100 \
  --device cpu \
  --max-samples 1500 \
  --epochs 120 \
  --run-dir runs/m88_wheel_masked_friction_relevance_audit_seed9100
```

Key row:

| target | body | wheel | body+wheel | body+wheel gain |
| --- | ---: | ---: | ---: | ---: |
| mu_bucket | 0.819302 | 0.636550 | 0.825462 | 0.006160 |

Response encoder norms:

```text
m87 body_norm  = 7.812276
m87 wheel_norm = 0.071743
m88 body_norm  = 7.807649
m88 wheel_norm = 0.073712
```

The wheel columns grow slightly, but not enough to change behavior.

## Interpretation

M88 is a negative result for wheel self-identification.

What improved:

- the masked auxiliary path works and is covered by tests;
- M88 preserves most aggregate behavior (`success_rate = 0.85`);
- wheel-only probe accuracy for `mu_bucket` improves versus M87
  (`0.636550` vs `0.584980`).

What failed:

- `zero_wheel_response` remains behavior-neutral;
- body+wheel gain for `mu_bucket` is only `+0.006160`;
- wheel encoder weights remain tiny;
- PPO coupling still does not make wheel evidence behavior-critical.

## Decision

Do not claim wheel-response self-ID from M88.

The next step should isolate the objective before further PPO continuation:

```text
M89: objective-only wheel-masked friction sanity

load M62 through the wheel partial initialization path;
freeze or ignore PPO reward;
optimize only the wheel-masked friction objective on a rollout batch;
measure whether wheel encoder columns and wheel-only mu prediction improve;
then run behavior and zero-wheel gates only if the objective moves in isolation.
```

This mirrors the M80 lesson: prove the auxiliary objective can move in
isolation before expecting PPO to use it.
