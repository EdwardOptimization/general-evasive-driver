# M85 Warm-Started Wheel Response Auxiliary Continuation

M84 proved that the wheel-response actor can be initialized from M62 without
destroying behavior, but `zero_wheel_response` did not hurt. M85 tests whether
making the auxiliary response-prediction target cover the full 25-value response
stream can make wheel feedback behavior-relevant while retaining the M62/M84
driver behavior.

## Config

`configs/ppo_m85_wheel_response_aux_driver.json` changes M84 in three ways:

- `response_prediction_dim = 25`;
- `response_prediction_aux_coef = 0.05`;
- `baseline_action_anchor_coef = 0.02` with the M62 checkpoint as an anchor.

The actor still starts from the M62 checkpoint through the M84 partial
initialization path. Because the response-prediction head changes from 12 to 25
predicted values, the expected load mode is:

```text
partial_wheel_response_encoder_response_prediction_head
```

## Focused Test

Added:

```text
tests/test_checkpoints.py::test_wheel_human_view_init_can_resize_response_prediction_head
```

It verifies that a 72-value human-view actor with a 12-value prediction head can
initialize an 85-value wheel actor with a 25-value prediction head while:

- preserving the copied response encoder body columns;
- zeroing the new wheel response columns;
- leaving the resized prediction head at its target initialization.

Focused validation:

```text
1 passed
```

## Smoke Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m85_wheel_response_aux_driver.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 3985 \
  --device cuda \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m85_wheel_response_aux_smoke_seed3985 \
  --eval-episodes 4
```

Load path:

```text
loaded_init_checkpoint=.../alpha_0_25.pt load_mode=partial_wheel_response_encoder_response_prediction_head
loaded_baseline_action_anchor=.../alpha_0_25.pt load_mode=partial_wheel_response_encoder_response_prediction_head
```

Built-in eval:

```text
return_mean = 59.73171597059553
steps_mean = 64.25
termination_rate = 0.25
lateral_rmse_mean = 0.9206067239581565
beta_abs_error_mean = 0.12274963305951271
```

This is weaker than M84's smoke eval (`termination_rate = 0.0`), but still
worth gating because short eval variance is high.

## Ablation Gate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m85_wheel_response_aux_driver.json \
  --episodes 20 \
  --seed 8830 \
  --policies heuristic \
  --checkpoint-policy m85=runs/ppo_m85_wheel_response_aux_smoke_seed3985/checkpoint.pt \
  --checkpoint-policy m85_zero_wheel=runs/ppo_m85_wheel_response_aux_smoke_seed3985/checkpoint.pt@zero_wheel_response \
  --checkpoint-policy m85_reset=runs/ppo_m85_wheel_response_aux_smoke_seed3985/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m85_zero_all=runs/ppo_m85_wheel_response_aux_smoke_seed3985/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m85_wheel_response_aux_gate_seed8830
```

Summary:

| policy | success | termination | return mean | clearance mean | clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | 0.40 | 0.60 | 50.407181 | 0.479831 | -0.231359 |
| m85 | 0.90 | 0.10 | 70.645276 | 2.168007 | -0.100225 |
| m85_reset | 0.90 | 0.10 | 69.043603 | 2.150428 | -0.095626 |
| m85_zero_all | 0.85 | 0.15 | 67.787839 | 2.155189 | -0.086382 |
| m85_zero_wheel | 0.90 | 0.10 | 70.620790 | 2.168196 | -0.101966 |

## Weight Audit

Response encoder column norms:

```text
m84 body_norm  = 7.811256
m84 wheel_norm = 0.065372
m85 body_norm  = 7.809560
m85 wheel_norm = 0.058681
```

The wheel columns remain tiny relative to body-response columns after the short
M85 continuation. This matches the ablation result: zeroing wheel response has
almost no behavioral effect.

## Interpretation

M85 is positive for retention but negative for wheel self-identification.

What improved:

- M85 keeps `success_rate = 0.90` on the 20-episode gate;
- return mean improves versus M84 on the same seed;
- the 25-value response head can be initialized and trained without breaking
  the checkpoint path.

What failed:

- `m85_zero_wheel` is effectively identical to normal M85;
- reset-hidden is also not meaningfully worse;
- wheel encoder columns remain very small;
- therefore the full-response auxiliary loss did not make wheel response
  behavior-critical.

## Decision

Do not simply increase wheel-response auxiliary coefficient or train longer
without a better gate. The current front/rear wheel response features may be
redundant with body response in this task, or the task may not contain enough
cases where wheel response is the only early evidence.

Next, run M86 as a wheel-response relevance audit:

```text
measure whether wheel response adds predictive information beyond body response;
compare body-only vs body+wheel probes for hidden dynamics or future response;
mine or construct cases where body response is matched but wheel response differs;
only then decide whether to add stronger wheel inputs or a wrong-wheel-history gate.
```
