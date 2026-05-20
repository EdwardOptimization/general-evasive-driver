# M18 Actuator-Response-Critical Training

Last updated: 2026-05-21

## Motivation

M17 improved the M13 perturbed success rate from `0.375` to `0.400`, but
response masking was indistinguishable from normal recurrent inference. The
failure mode is clear: predicting the next response can shape hidden state, but
the policy head can still ignore the response-sensitive part of the latent.

M18 moves the pressure into the control problem. The same obstacle geometry and
same friction-step timing can now be evaluated under different hidden actuator
response conditions. A driver-like policy should use observed vehicle and
actuator response to adapt, while response-masked inference should lose
performance.

## Gate Change

`paired_perturbation_gate` now supports condition-specific randomization
overrides:

```text
--nominal-randomization KEY=LOW,HIGH
--perturbed-randomization KEY=LOW,HIGH
```

The overrides apply only to hidden simulator randomization ranges. They do not
add actor inputs. With identical friction ranges and identical seed corpus, the
gate keeps the same obstacle geometry and road perturbation while changing
actuator response.

M17 actuator-response baseline command:

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
  --nominal-friction-mu-range 0.30,0.45 \
  --perturbed-friction-mu-range 0.30,0.45 \
  --nominal-randomization actuator_tau_scale_range=0.60,0.90 \
  --nominal-randomization brake_scale_range=1.20,1.40 \
  --nominal-randomization drive_scale_range=1.10,1.35 \
  --perturbed-randomization actuator_tau_scale_range=2.40,3.20 \
  --perturbed-randomization brake_scale_range=0.45,0.65 \
  --perturbed-randomization drive_scale_range=0.55,0.75 \
  --run-dir runs/m18_actuator_response_gate_m17_smoke_seed3000
```

M17 baseline result:

| policy | nominal success | perturbed success | success drop | return delta |
| --- | ---: | ---: | ---: | ---: |
| `m17` | 0.450 | 0.425 | 0.025 | -3.326 |
| `m17_reset` | 0.475 | 0.450 | 0.025 | -4.415 |
| `m17_zero_current` | 0.450 | 0.425 | 0.025 | -3.087 |
| `m17_zero_all` | 0.450 | 0.425 | 0.025 | -3.087 |

Interpretation: this gate already exposes weak actuator-response robustness,
but M17 still behaves the same under response masking. M18 training must improve
success while making response masking measurably worse than normal recurrent
inference.

## Training Config

Config:

```text
configs/ppo_m18_actuator_response_recurrent_driver.json
```

The actor contract is unchanged:

- online GRU actor;
- deployable single-frame observation with action history and actuator state;
- no hidden friction, vehicle parameters, labels, controller modes, or oracle
  feasibility inputs;
- no response-prediction auxiliary head.

The training distribution widens actuator and vehicle-response variation:

- `actuator_tau_scale_range`: `[0.55, 3.20]`;
- `brake_scale_range`: `[0.45, 1.40]`;
- `drive_scale_range`: `[0.55, 1.35]`;
- `tire_stiffness_scale_range`: `[0.55, 1.45]`;
- `mass_scale_range`: `[0.80, 1.28]`.

Queued training command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m18_actuator_response_recurrent_driver.json \
  --seed 911 \
  --device cuda \
  --run-dir runs/ppo_m18_actuator_response_recurrent_seed911
```

Smoke results:

| run | seed | steps | return mean | termination rate | lateral RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| `runs/ppo_m18_actuator_response_smoke_seed811` | 811 | 512 | 36.902 | 0.600 | 0.361 |
| `runs/ppo_m18_actuator_response_smoke_seed733` | 733 | 512 | 52.169 | 0.500 | 0.484 |
| `runs/ppo_m18_actuator_response_smoke_seed911` | 911 | 512 | 65.386 | 0.400 | 0.640 |
| `runs/ppo_m18_actuator_response_warmup_smoke_seed911` | 911 | 20480 | 82.054 | 0.100 | 0.624 |

Seed `911` is selected for the full run because it has the best short-smoke
signal and improves after five PPO updates on the harder M18 warmup
distribution.

## Pass Direction

M18 should satisfy all of the following before it can be considered a better
self-identifying driver candidate:

- improve actuator-response gate success above the M17 baseline;
- normal recurrent inference should beat `reset_recurrent_state`;
- `zero_current_response` and `zero_all_response` should be worse than normal;
- M13 friction perturbation gate should not regress below M17's `0.400`
  perturbed success;
- stable AES behavior should not become drift-seeking.

## Full Result

Training result:

- run dir: `runs/ppo_m18_actuator_response_recurrent_seed911`;
- checkpoint: `runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt`;
- research run dir:
  `runs/research/m18-actuator-response-critical-training_20260520T221756Z`;
- final eval return mean: 80.380;
- final eval steps mean: 68.600;
- final eval termination rate: 0.100;
- final eval lateral RMSE mean: 0.700;
- final eval beta absolute error mean: 0.136.

Actuator-response paired gate:

| policy | nominal success | perturbed success | success drop | return delta |
| --- | ---: | ---: | ---: | ---: |
| `m18` | 0.450 | 0.375 | 0.075 | -7.482 |
| `m18_reset` | 0.175 | 0.225 | -0.050 | 0.173 |
| `m18_zero_current` | 0.450 | 0.300 | 0.150 | -11.280 |
| `m18_zero_all` | 0.450 | 0.300 | 0.150 | -11.280 |

M13 friction paired gate:

| policy | nominal success | perturbed success | success drop | return delta |
| --- | ---: | ---: | ---: | ---: |
| `m18` | 0.775 | 0.375 | 0.400 | -18.785 |
| `m18_reset` | 0.575 | 0.150 | 0.425 | -21.305 |
| `m18_zero_current` | 0.750 | 0.325 | 0.425 | -20.944 |
| `m18_zero_all` | 0.750 | 0.325 | 0.425 | -20.944 |

Same-corpus obstacle benchmark:

| policy | success | termination | high sideslip |
| --- | ---: | ---: | ---: |
| `envelope_aes` | 0.250 | 0.750 | 0.000 |
| `m18` | 0.450 | 0.550 | 0.004 |
| `m18_reset` | 0.225 | 0.775 | 0.010 |
| `m18_zero_current` | 0.425 | 0.575 | 0.000 |

Conclusion: M18 is the first run in this sequence where response masking and
hidden-state reset clearly hurt paired-gate performance. That is real progress
toward closed-loop self-identification. It is not yet the ideal driver:
actuator-response aggregate success is still low, and M13 perturbed success
falls short of M17 (`0.375` vs `0.400`). The next experiment should preserve the
M18 response-dependence signal while recovering M17-level aggregate success.
