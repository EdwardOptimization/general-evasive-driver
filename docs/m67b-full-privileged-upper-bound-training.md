# M67-B Full Privileged Upper-Bound Training

M67-A added the full-dynamics privileged observation packet and the
per-env-config upper-bound harness. M67-B trains the first full privileged
teacher from scratch and compares it against the current deployable baseline
`m62_a250` on the M65 response-critical corpus.

## Training

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m67a_privileged_upper_bound_teacher.json \
  --seed 3067 \
  --device cuda \
  --run-dir runs/ppo_m67a_privileged_upper_bound_teacher_seed3067
```

Result:

- final checkpoint:
  `runs/ppo_m67a_privileged_upper_bound_teacher_seed3067/checkpoint.pt`;
- dense checkpoints every 8192 steps under
  `runs/ppo_m67a_privileged_upper_bound_teacher_seed3067/checkpoints/`;
- final eval return mean: `71.909091`;
- final eval termination rate: `0.100000`;
- final eval lateral RMSE mean: `0.704402`;
- final eval beta absolute error mean: `0.194360`.

Training did improve substantially over the 1024-step smoke teacher, but the
training eval is not the promotion gate. The gate is the M65 response-critical
corpus comparison against M62.

## Final-Checkpoint Upper-Bound Comparison

Command:

```bash
conda run -n autodrift python -m autodrift.privileged_upper_bound \
  --baseline-env-config configs/ppo_m24_human_view_gru_driver.json \
  --candidate-env-config configs/ppo_m67a_privileged_upper_bound_teacher.json \
  --baseline-checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --candidate-checkpoint-policy m67a_teacher=runs/ppo_m67a_privileged_upper_bound_teacher_seed3067/checkpoint.pt \
  --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv \
  --seed 3600 \
  --device cpu \
  --run-dir runs/m67a_privileged_upper_bound_m65_seed3600
```

| Policy | Episodes | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: | ---: |
| `m62_a250` | 26 | 0.615385 | 0.384615 | 0.304161 |
| `m67a_teacher` | 26 | 0.461538 | 0.538462 | 0.191716 |

Final-checkpoint deltas:

- success delta: `-0.153846`;
- collision delta: `0.153846`;
- mean clearance-margin delta: `-0.112445`.

## Checkpoint Sweep

Command:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m67a_privileged_upper_bound_teacher.json \
  --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv \
  --checkpoint-policy m67a_008=... \
  ... \
  --checkpoint-policy m67a_256=... \
  --policies heuristic \
  --device cpu \
  --run-dir runs/m67a_privileged_teacher_checkpoint_sweep_m65_seed3600
```

Best checkpoints by M65 success and margin:

| Policy | Success | Mean margin | Return mean | Collision |
| --- | ---: | ---: | ---: | ---: |
| `m67a_232` | 0.500000 | 0.213538 | 45.653439 | 0.500000 |
| `m67a_184` | 0.500000 | 0.212342 | 45.279042 | 0.500000 |
| `m67a_192` | 0.500000 | 0.206659 | 45.579990 | 0.500000 |
| `m67a_200` | 0.500000 | 0.202804 | 45.691560 | 0.500000 |
| `m67a_176` | 0.500000 | 0.184678 | 45.129651 | 0.500000 |

The best sweep candidate is `m67a_232`:

```text
runs/ppo_m67a_privileged_upper_bound_teacher_seed3067/checkpoints/checkpoint_step_237568.pt
```

Best-checkpoint upper-bound command:

```bash
conda run -n autodrift python -m autodrift.privileged_upper_bound \
  --baseline-env-config configs/ppo_m24_human_view_gru_driver.json \
  --candidate-env-config configs/ppo_m67a_privileged_upper_bound_teacher.json \
  --baseline-checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --candidate-checkpoint-policy m67a_232=runs/ppo_m67a_privileged_upper_bound_teacher_seed3067/checkpoints/checkpoint_step_237568.pt \
  --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv \
  --seed 3600 \
  --device cpu \
  --run-dir runs/m67a_privileged_upper_bound_best_m65_seed3600
```

| Policy | Episodes | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: | ---: |
| `m62_a250` | 26 | 0.615385 | 0.384615 | 0.304161 |
| `m67a_232` | 26 | 0.500000 | 0.500000 | 0.213538 |

Best-checkpoint deltas:

- success delta: `-0.115385`;
- collision delta: `0.115385`;
- mean clearance-margin delta: `-0.090623`;
- margin-improved seeds: 6;
- margin-regressed seeds: 20.

## Conclusion

M67-B is a negative upper-bound attempt. A privileged `online_gru` trained from
scratch sees the full hidden dynamics packet, but still does not beat the
human-view M62 checkpoint on the M65 response-critical corpus.

This does not prove that hidden dynamics information is useless. The stronger
failure hypothesis is:

```text
The from-scratch privileged teacher must learn baseline emergency driving and
oracle usage simultaneously. It never reaches M62's retained driving behavior,
so its hidden inputs cannot become a meaningful upper bound.
```

The next experiment should build a warm-start or anchored privileged teacher:

- preserve M62's response/context structure for the first 72 deployable inputs;
- append full hidden dynamics as extra teacher-only context;
- initialize or anchor the shared behavior to M62 where possible;
- only then test whether hidden dynamics improves M65 margin or action choices.

If a warm-start privileged teacher still cannot beat M62, then the next step is
to re-mine matched action-divergent seeds before any deployable student OSI
objective.
