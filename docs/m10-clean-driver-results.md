# M10 Clean Driver Results

Last updated: 2026-05-21

## Purpose

M10 retrains the temporal-GRU obstacle driver under the clean 60-dimensional
actor observation contract. It is the first full training run after removing
oracle-like and non-driver inputs from the actor:

- `aeb_stop_distance`;
- explicit sideslip `beta`;
- `speed_ref`;
- `beta_target`.

The historical M8 checkpoint is not compatible with this contract and was not
used for initialization.

## Training

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m8_temporal_gru_driver.json \
  --seed 327 \
  --device cuda \
  --run-dir runs/ppo_m10_clean_temporal_gru_driver_seed327
```

Research harness run:

- task: `m10-clean-observation-retrain`;
- command log:
  `runs/research/m10-clean-observation-retrain_20260520T191136Z/command.log`;
- checkpoint:
  `runs/ppo_m10_clean_temporal_gru_driver_seed327/checkpoint.pt`.

Training completed successfully.

Built-in deterministic eval:

| metric | value |
| --- | ---: |
| return mean | 10.787 |
| steps mean | 31.400 |
| termination rate | 0.800 |
| lateral RMSE mean | 0.355 |
| beta abs error mean | 0.144 |

The built-in eval is weak: high termination rate means the checkpoint should not
be treated as a driver-v1 candidate without gate results.

## Observation-Degradation Gate

Command:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/m8_history_critical_obstacle_holdout_eval.json \
  --episodes 40 \
  --seed 1600 \
  --policies envelope_aes \
  --checkpoint-policy m10=runs/ppo_m10_clean_temporal_gru_driver_seed327/checkpoint.pt \
  --checkpoint-policy m10_zero_current=runs/ppo_m10_clean_temporal_gru_driver_seed327/checkpoint.pt@zero_current_response \
  --checkpoint-policy m10_zero_all=runs/ppo_m10_clean_temporal_gru_driver_seed327/checkpoint.pt@zero_all_response \
  --checkpoint-policy m10_single=runs/ppo_m10_clean_temporal_gru_driver_seed327/checkpoint.pt@single_frame_history \
  --checkpoint-policy m10_shuffle=runs/ppo_m10_clean_temporal_gru_driver_seed327/checkpoint.pt@shuffled_history \
  --device cpu \
  --run-dir runs/m10_clean_observation_degradation_gate_seed1600
```

Aggregate result:

| policy | success | collision | return | high sideslip |
| --- | ---: | ---: | ---: | ---: |
| envelope AES | 0.225 | 0.775 | 6.662 | 0.000 |
| M10 | 0.275 | 0.725 | 11.335 | 0.024 |
| M10 zero current response | 0.275 | 0.725 | 11.342 | 0.026 |
| M10 zero all response | 0.275 | 0.725 | 11.214 | 0.054 |
| M10 single-frame history | 0.275 | 0.725 | 11.296 | 0.025 |
| M10 shuffled history | 0.275 | 0.725 | 11.343 | 0.024 |

Label-bucket result:

| policy | label | episodes | success | collision | return |
| --- | --- | ---: | ---: | ---: | ---: |
| envelope AES | drift_required | 9 | 0.778 | 0.222 | 63.426 |
| envelope AES | unavoidable | 31 | 0.065 | 0.935 | -9.817 |
| M10 | drift_required | 9 | 1.000 | 0.000 | 80.087 |
| M10 | unavoidable | 31 | 0.065 | 0.935 | -8.625 |
| M10 zero all response | drift_required | 9 | 1.000 | 0.000 | 79.163 |
| M10 zero all response | unavoidable | 31 | 0.065 | 0.935 | -8.513 |

M10 improves the static benchmark slightly over envelope AES by solving every
sampled `drift_required` case. It does not improve `unavoidable` mitigation in a
meaningful way.

The ablation result is negative. Success is unchanged after zeroing current
response, zeroing all response history, forcing single-frame history, or
shuffling history. This means M10 still does not prove closed-loop
self-identification.

## Latent Probe

Command:

```bash
conda run -n autodrift python -m autodrift.latent_probe \
  --checkpoint runs/ppo_m10_clean_temporal_gru_driver_seed327/checkpoint.pt \
  --env-config configs/m8_history_critical_obstacle_holdout_eval.json \
  --episodes 80 \
  --seed 1700 \
  --epochs 120 \
  --device cpu \
  --run-dir runs/m10_clean_latent_probe_seed1700
```

Selected probe results:

| target | latent lift | single-frame lift | shuffled-history latent lift |
| --- | ---: | ---: | ---: |
| mu bucket | 0.076 | 0.037 | 0.086 |
| brake bucket | 0.116 | 0.084 | 0.124 |
| CG bucket | 0.065 | 0.117 | 0.055 |
| tire bucket | -0.094 | -0.048 | -0.107 |
| steering tau bucket | -0.204 | -0.197 | -0.199 |

The latent has some friction and brake signal, but shuffled-history latent is
not weaker than ordered-history latent. The probe therefore does not support the
claim that the current GRU behavior depends on ordered closed-loop response
history.

## Conclusion

M10 is a valid clean-contract checkpoint and should be kept as the current clean
temporal baseline. It is not a professional-driver result.

The important negative result is stronger than "needs more training": the clean
policy still passes and fails the same scenarios under all history/response
ablations. The next work should change the validation and architecture toward
online recurrent hidden state and hidden-state reset tests, with paired
scenarios where static geometry is identical but vehicle response changes after
the first control actions.
