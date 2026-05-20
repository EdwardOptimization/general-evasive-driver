# M7 First-Stage Results

Last updated: 2026-05-21

## Scope

This note records the first M7 implementation and validation pass. It is a
real training and benchmark result for the new M7 infrastructure, but it is not
a completed M7 success claim.

Implemented pieces:

- `action_history_mode="full"` for deployable actor inputs that include both
  previous drive/brake and previous steering commands while preserving the
  legacy observation prefix for old checkpoint expansion;
- hidden vehicle-road diagnostics in `info`, including mass, CG, brake, tire,
  and actuator-delay scales;
- M7-A history actor path through stacked observations and full action history;
- M7-B receding-horizon sequence actor path with
  `action_sequence_horizon > 1`, executing only the first action;
- sequence auxiliary target construction from future executed actions inside
  the rollout buffer;
- checkpoint compatibility so older M5 checkpoints can be expanded to the M7
  observation shape and M7-B can add a new sequence head;
- benchmark support for multiple named checkpoint policies through
  `--checkpoint-policy name=path`;
- checkpoint observation ablations through
  `--checkpoint-policy name=path@zero_action_history` and
  `--checkpoint-policy name=path@single_frame_history`;
- latent self-identification probe tooling through
  `python -m autodrift.latent_probe`;
- vehicle-road bucket summaries for held-out analysis.

## Configs

New configuration files:

- `configs/ppo_m7a_history_obstacle.json`;
- `configs/ppo_m7b_sequence_obstacle.json`;
- `configs/m7_obstacle_holdout_eval.json`;
- `configs/m7_obstacle_aes_weighted_holdout_eval.json`.

All use:

- `history_length=4`;
- `action_history_mode="full"`;
- AEB-infeasible obstacle sampling;
- `aes_feasible`, `drift_required`, and `unavoidable` labels;
- broader vehicle-road randomization than M5.

The AES-weighted holdout config narrows speed and obstacle ranges so the
benchmark contains more avoidable cases while still keeping AEB-only
infeasible. For seeds `0..99`, its labels were:

| label | count |
| --- | ---: |
| `aes_feasible` | 18 |
| `drift_required` | 42 |
| `unavoidable` | 40 |

## Training Runs

M7-A 1M-step training:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m7a_history_obstacle.json \
  --init-checkpoint runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --run-dir runs/ppo_m7a_history_seed127
```

Result:

- load mode: `partial_input_expand`;
- device: CUDA;
- eval return mean: `10.256`;
- eval termination rate: `0.700`;
- lateral RMSE mean: `0.411`;
- beta absolute error mean: `0.241`.

M7-B 1M-step training:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m7b_sequence_obstacle.json \
  --init-checkpoint runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --run-dir runs/ppo_m7b_sequence_seed131
```

Result:

- load mode: `new_sequence_head+partial_input_expand`;
- device: CUDA;
- eval return mean: `1.390`;
- eval termination rate: `0.800`;
- lateral RMSE mean: `0.225`;
- beta absolute error mean: `0.230`.

Interpretation: both 1M-step runs completed and produced usable checkpoints,
but the built-in training eval is weak. The useful evidence comes from the
shared-seed obstacle benchmarks below.

## Holdout Benchmark

Command:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --episodes 100 \
  --seed 700 \
  --policies aeb aes_heuristic envelope_aes \
  --checkpoint-policy m5=runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --checkpoint-policy m7a=runs/ppo_m7a_history_seed127/checkpoint.pt \
  --checkpoint-policy m7b=runs/ppo_m7b_sequence_seed131/checkpoint.pt \
  --env-config configs/m7_obstacle_holdout_eval.json \
  --device cpu \
  --run-dir runs/benchmark_m7_operator_holdout_100eval
```

Policy summary:

| policy | success_rate | collision_rate | high_sideslip_fraction | plan_horizon_mean |
| --- | ---: | ---: | ---: | ---: |
| `aeb` | 0.070 | 0.920 | 0.033 | 1 |
| `aes_heuristic` | 0.150 | 0.850 | 0.277 | 1 |
| `envelope_aes` | 0.330 | 0.670 | 0.000 | 1 |
| `m5` | 0.330 | 0.670 | 0.055 | 1 |
| `m7a` | 0.360 | 0.640 | 0.113 | 1 |
| `m7b` | 0.330 | 0.670 | 0.074 | 6 |

Label-level summary:

| label | episodes | envelope_aes | m5 | m7a | m7b |
| --- | ---: | ---: | ---: | ---: | ---: |
| `aes_feasible` | 4 | 1.000 | 1.000 | 1.000 | 1.000 |
| `drift_required` | 29 | 0.897 | 0.897 | 0.931 | 0.862 |
| `unavoidable` | 67 | 0.000 | 0.045 | 0.075 | 0.060 |

Interpretation:

- M7-A is slightly better than M5 overall and on `drift_required` cases.
- M7-B records a valid six-step plan but does not beat M5 in this benchmark.
- The main holdout is dominated by `unavoidable` cases, so it is not balanced
  enough to judge drift-capable AES behavior by itself.

## AES-Weighted Holdout Benchmark

Command:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --episodes 100 \
  --seed 900 \
  --policies aeb aes_heuristic envelope_aes \
  --checkpoint-policy m5=runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --checkpoint-policy m7a=runs/ppo_m7a_history_seed127/checkpoint.pt \
  --checkpoint-policy m7b=runs/ppo_m7b_sequence_seed131/checkpoint.pt \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --device cpu \
  --run-dir runs/benchmark_m7_operator_aes_weighted_100eval
```

Policy summary:

| policy | success_rate | collision_rate | high_sideslip_fraction | plan_horizon_mean |
| --- | ---: | ---: | ---: | ---: |
| `aeb` | 0.130 | 0.860 | 0.061 | 1 |
| `aes_heuristic` | 0.290 | 0.710 | 0.270 | 1 |
| `envelope_aes` | 0.570 | 0.430 | 0.004 | 1 |
| `m5` | 0.580 | 0.420 | 0.046 | 1 |
| `m7a` | 0.600 | 0.400 | 0.115 | 1 |
| `m7b` | 0.600 | 0.400 | 0.071 | 6 |

Label-level success:

| label | episodes | envelope_aes | m5 | m7a | m7b |
| --- | ---: | ---: | ---: | ---: | ---: |
| `aes_feasible` | 15 | 1.000 | 1.000 | 1.000 | 1.000 |
| `drift_required` | 40 | 0.950 | 0.950 | 0.950 | 0.975 |
| `unavoidable` | 45 | 0.089 | 0.111 | 0.156 | 0.133 |

Label-level high-sideslip fraction:

| label | envelope_aes | m5 | m7a | m7b |
| --- | ---: | ---: | ---: | ---: |
| `aes_feasible` | 0.026 | 0.113 | 0.346 | 0.204 |
| `drift_required` | 0.000 | 0.061 | 0.155 | 0.111 |
| `unavoidable` | 0.000 | 0.000 | 0.003 | 0.000 |

Interpretation:

- M7-A and M7-B improve aggregate success from M5's `0.580` to `0.600`.
- M7-B improves `drift_required` success from `0.950` to `0.975`.
- M7-A improves the binary pass rate on `unavoidable` cases from `0.111` to
  `0.156`.
- Neither checkpoint satisfies the "drift-capable, not drift-seeking" behavior
  requirement yet. Both use more high-sideslip behavior than M5 and
  `envelope_aes` on `aes_feasible` cases.

## Observation Ablation Benchmark

Command:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --episodes 100 \
  --seed 900 \
  --policies envelope_aes \
  --checkpoint-policy m5=runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --checkpoint-policy m7a=runs/ppo_m7a_history_seed127/checkpoint.pt \
  --checkpoint-policy m7a_noact=runs/ppo_m7a_history_seed127/checkpoint.pt@zero_action_history \
  --checkpoint-policy m7a_single=runs/ppo_m7a_history_seed127/checkpoint.pt@single_frame_history \
  --checkpoint-policy m7b=runs/ppo_m7b_sequence_seed131/checkpoint.pt \
  --checkpoint-policy m7b_noact=runs/ppo_m7b_sequence_seed131/checkpoint.pt@zero_action_history \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --device cpu \
  --run-dir runs/benchmark_m7_operator_ablation_100eval
```

Policy summary:

| policy | ablation | success_rate | collision_rate | high_sideslip_fraction | plan_horizon_mean |
| --- | --- | ---: | ---: | ---: | ---: |
| `envelope_aes` | none | 0.570 | 0.430 | 0.004 | 1 |
| `m5` | none | 0.580 | 0.420 | 0.046 | 1 |
| `m7a` | none | 0.600 | 0.400 | 0.115 | 1 |
| `m7a_noact` | zero action history | 0.600 | 0.400 | 0.115 | 1 |
| `m7a_single` | single frame tiled | 0.590 | 0.410 | 0.125 | 1 |
| `m7b` | none | 0.600 | 0.400 | 0.071 | 6 |
| `m7b_noact` | zero action history | 0.620 | 0.380 | 0.067 | 6 |

Key label-level result:

| policy | `aes_feasible` | `drift_required` | `unavoidable` |
| --- | ---: | ---: | ---: |
| `m7a` | 1.000 | 0.950 | 0.156 |
| `m7a_noact` | 1.000 | 0.950 | 0.156 |
| `m7a_single` | 1.000 | 0.950 | 0.133 |
| `m7b` | 1.000 | 0.975 | 0.133 |
| `m7b_noact` | 1.000 | 0.975 | 0.178 |

Interpretation:

- The current M7 checkpoints do not prove action-history-based
  self-identification. Zeroing action history does not hurt M7-A and slightly
  improves M7-B on this seed set.
- Single-frame tiling barely hurts M7-A, which suggests the current actor may
  still behave mostly like a feed-forward geometry and state controller.
- The ablation tool is now in place, but the algorithm has not passed the M7
  adaptation gate.

## Latent Self-Identification Probe

Probe commands:

```bash
conda run -n autodrift python -m autodrift.latent_probe \
  --checkpoint runs/ppo_m7a_history_seed127/checkpoint.pt \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --episodes 100 \
  --seed 1200 \
  --device cpu \
  --epochs 160 \
  --run-dir runs/latent_probe_m7a_history_100eval

conda run -n autodrift python -m autodrift.latent_probe \
  --checkpoint runs/ppo_m7b_sequence_seed131/checkpoint.pt \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --episodes 100 \
  --seed 1200 \
  --device cpu \
  --epochs 160 \
  --run-dir runs/latent_probe_m7b_sequence_100eval
```

The probe trains linear classifiers on frozen rollout samples. It compares
three feature sets:

- actor `latent`: the output of the actor's shared hidden layers;
- `single_frame`: the current deployable observation frame only;
- `shuffled_history_latent`: actor latent after randomly permuting history
  frame order.

M7-A selected probe results:

| target | latent_acc | single_frame_acc | shuffled_latent_acc | majority_acc |
| --- | ---: | ---: | ---: | ---: |
| `mu_bucket` | 0.957 | 0.976 | 0.956 | 0.798 |
| `mass_bucket` | 0.321 | 0.475 | 0.327 | 0.392 |
| `cg_bucket` | 0.417 | 0.499 | 0.398 | 0.467 |
| `brake_bucket` | 0.338 | 0.296 | 0.326 | 0.395 |
| `tire_bucket` | 0.366 | 0.218 | 0.368 | 0.235 |
| `steering_tau_bucket` | 0.552 | 0.517 | 0.540 | 0.642 |

M7-B selected probe results:

| target | latent_acc | single_frame_acc | shuffled_latent_acc | majority_acc |
| --- | ---: | ---: | ---: | ---: |
| `mu_bucket` | 0.959 | 0.974 | 0.967 | 0.799 |
| `mass_bucket` | 0.366 | 0.441 | 0.378 | 0.397 |
| `cg_bucket` | 0.349 | 0.478 | 0.355 | 0.471 |
| `brake_bucket` | 0.307 | 0.301 | 0.298 | 0.397 |
| `tire_bucket` | 0.357 | 0.143 | 0.384 | 0.234 |
| `steering_tau_bucket` | 0.444 | 0.514 | 0.461 | 0.643 |

Interpretation:

- Both policies encode useful friction-bucket information, but single-frame
  features are even stronger on `mu_bucket`.
- Tire-bucket information is present in latent features, but
  shuffled-history latent is not worse, so this does not prove temporal
  self-identification.
- Mass, CG, brake authority, and steering delay probes are weak or worse than
  the majority baseline.
- These probe results reinforce the ablation result: the current M7 policies
  do not yet show convincing action-history or temporal-order dependence.

## Negative Results And Gaps

- M7-A and M7-B completed 1M-step training, but the training eval termination
  rates remain high.
- The AES-weighted benchmark shows small aggregate gains, but not a robust
  behavioral win.
- Both M7 checkpoints overuse high sideslip in `aes_feasible` scenarios.
- Action-history ablation does not currently reduce performance, so the core
  closed-loop self-identification claim is not validated.
- No recurrent actor has been trained yet.
- No privileged critic or teacher-student asymmetric training result exists
  yet.
- Latent probes are implemented, but the first results do not show convincing
  temporal/action-history self-identification.
- M7-B sequence smoothness is recorded, but no safety-preview decision rule has
  been validated.

## Current Conclusion

M7 infrastructure is ready for iteration, but the current checkpoints should be
treated as first-pass baselines rather than successful universal closed-loop
operators.

The strongest positive signal is that M7-A and M7-B can slightly improve
aggregate success over M5 on the AES-weighted held-out benchmark, and M7-B can
run the MPC-like "predict sequence, execute first action" interface.

The strongest negative signal is that removing action history does not hurt,
and latent probes do not degrade when history order is shuffled. The next
algorithm work should therefore target architectures and objectives that make
feedback identification necessary and measurable.

## Next Steps

1. Add a recurrent actor or explicit latent-state actor and rerun the same
   ablations.
2. Add stable-AES penalties or reward terms so `aes_feasible` success is not
   achieved through unnecessary sideslip.
3. Improve latent probe evidence by adding recurrent/latent actor states and
   probing them against the current feed-forward latent baseline.
4. Add label-balanced benchmark generation instead of relying only on random
   filtered sampling.
5. Add `shuffled_history` and `privileged_leak` ablations.
6. Use the M7-B sequence output as a diagnostic and safety-preview signal, but
   do not treat it as validated fallback logic yet.
