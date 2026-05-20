# M17 Response-Prediction Auxiliary Loss

Last updated: 2026-05-21

## Motivation

M16 fixed detached hidden-state PPO updates and improved perturbed success, but
hidden reset still beat normal recurrent inference on nominal cases. The next
hypothesis is that reward alone is too weak to force hidden state to represent
vehicle response history.

M17 adds a deployable auxiliary target: predict the next response frame from the
current recurrent feature and executed action.

## Change

`PPOConfig.response_prediction_aux_coef` enables an auxiliary loss for online
GRU sequence training. With `response_prediction_dim=5`, the prediction target
is the next observation's first five deployable response features:

```text
[vx, vy, yaw_rate, steering_actuator_state, drive_brake_actuator_state]
```

The target is masked across done transitions. It does not use true friction,
vehicle parameters, obstacle labels, controller modes, or feasibility oracles.

## Training Config

Config:

```text
configs/ppo_m17_response_aux_recurrent_driver.json
```

Queued command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m17_response_aux_recurrent_driver.json \
  --seed 733 \
  --device cuda \
  --run-dir runs/ppo_m17_response_aux_recurrent_seed733
```

Smoke result:

- seed 809 smoke was rejected as a poor random-initialization comparison:
  termination rate was 1.000 after one update;
- using seed 733 matches M16's initialization for a cleaner auxiliary-loss
  comparison;
- run dir: `runs/ppo_m17_response_aux_smoke_seed733`;
- eval return mean: 83.418;
- eval steps mean: 67.500;
- eval termination rate: 0.000;
- eval lateral RMSE mean: 0.258.

Full training result:

- run dir: `runs/ppo_m17_response_aux_recurrent_seed733`;
- checkpoint: `runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt`;
- research run dir: `runs/research/m17-response-prediction-aux_20260520T211106Z`;
- final eval return mean: 79.977;
- final eval steps mean: 62.800;
- final eval termination rate: 0.000;
- final eval lateral RMSE mean: 0.813;
- final eval beta absolute error mean: 0.132.

## Validation

Use the same M13 paired gate:

```bash
conda run -n autodrift python -m autodrift.paired_perturbation_gate \
  --env-config configs/m11_online_recurrent_history_critical_eval.json \
  --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv \
  --checkpoint runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt \
  --checkpoint-policy m17=runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt \
  --checkpoint-policy m17_reset=runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m17_zero_current=runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt@zero_current_response \
  --checkpoint-policy m17_zero_all=runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m17_response_aux_paired_gate_seed3000
```

Pass direction:

- normal M17 should beat hidden reset, especially on perturbed success;
- response masking should remain worse than normal inference;
- normal M17 should not regress below M16 aggregate gate performance.

Gate result:

| policy | nominal success | perturbed success | success drop | return delta |
| --- | ---: | ---: | ---: | ---: |
| `m17` | 0.825 | 0.400 | 0.425 | -20.595 |
| `m17_reset` | 0.900 | 0.400 | 0.500 | -23.024 |
| `m17_zero_current` | 0.825 | 0.400 | 0.425 | -20.468 |
| `m17_zero_all` | 0.825 | 0.400 | 0.425 | -20.468 |

Interpretation:

- The auxiliary loss slightly improves normal perturbed success versus M16
  (`0.400` vs `0.375`) and matches hidden-reset perturbed success.
- Hidden reset still wins nominal success (`0.900` vs `0.825`), so normal
  recurrent inference still does not dominate.
- Current-response and all-response masking are behaviorally indistinguishable
  from normal M17 on this gate. The actor can still solve the sampled cases
  mostly from geometry and learned timing rather than response-dependent
  self-identification.

Conclusion: M17 is not the driver mechanism we want. Predicting next response
as an auxiliary task may shape hidden state, but the policy head is still free
to ignore that response-sensitive part of the latent. The next experiment should
make response dependence behavior-critical rather than merely predictable.
