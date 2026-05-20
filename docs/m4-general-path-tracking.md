# M4 General Path Tracking

Last updated: 2026-05-20

## Goal

M4 moves beyond steady circular drift and adds variable-curvature path tracking.
This is the bridge from steady drift control to emergency steering and obstacle
avoidance, because AES-style maneuvers need curvature changes, drift initiation,
and drift recovery rather than only steady-state circular motion.

## Implemented Path Task

The environment now supports:

```text
track_kind = "circle"
track_kind = "figure_eight"
```

The `figure_eight` track is a closed sampled Lissajous-style path. It provides
the same path-frame contract as the circular task:

- nearest path frame;
- signed lateral error;
- heading error;
- signed curvature;
- progress;
- tangent vector and tangent heading;
- reset poses near the path.

The friction-limited speed sampler now uses the active track's reference radius,
so the figure-eight task automatically lowers speed when the tightest curvature
is smaller than the circular path radius.

## Configs

Evaluation config:

```text
configs/m4_figure_eight_eval.json
```

Training template:

```text
configs/ppo_m4_figure_eight_history.json
```

The training template uses `history_length=4`, so it can initialize strictly
from the current M3 history checkpoint:

```text
runs/ppo_m3_staged_history_seed47_init_m2/checkpoint.pt
```

The evaluation config also uses `history_length=4`. This is required when
evaluating the M4 history checkpoint; using a single-frame eval config causes an
observation/model shape mismatch.

## Smoke Results

Heuristic figure-eight benchmark smoke:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 5 \
  --policies heuristic \
  --env-config configs/m4_figure_eight_eval.json \
  --run-dir runs/benchmark_m4_figure_eight_heuristic_smoke
```

Result:

| policy | episodes | success_rate | return_mean | lateral_rmse_mean |
| --- | ---: | ---: | ---: | ---: |
| heuristic | 5 | 1.000 | 812.80 | 1.350 |

PPO training-loop smoke:

```bash
PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m4_figure_eight_history.json \
  --init-checkpoint runs/ppo_m3_staged_history_seed47_init_m2/checkpoint.pt \
  --total-steps 512 \
  --eval-episodes 1 \
  --run-dir runs/ppo_m4_figure_eight_history_seed61_smoke
```

Result:

```text
loaded_init_checkpoint=... load_mode=strict
training_device=cuda num_envs=16 curriculum_stage=wide_low_speed
```

The 512-step smoke is not expected to learn the task. Its purpose is only to
verify strict M3-to-M4 checkpoint initialization, figure-eight environment
construction, and the PPO training loop.

## First M4 Training Attempt

Command:

```bash
PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m4_figure_eight_history.json \
  --init-checkpoint runs/ppo_m3_staged_history_seed47_init_m2/checkpoint.pt \
  --run-dir runs/ppo_m4_figure_eight_history_seed61
```

Benchmark command:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 100 \
  --policies heuristic checkpoint \
  --checkpoint runs/ppo_m4_figure_eight_history_seed61/checkpoint.pt \
  --env-config configs/m4_figure_eight_eval.json \
  --run-dir runs/benchmark_ppo_m4_figure_eight_history_seed61_100eval
```

Overall result:

| policy | episodes | success_rate | return_mean | lateral_rmse_mean | beta_abs_error_mean | speed_mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| checkpoint | 100 | 0.820 | 848.21 | 1.467 | 0.320 | 6.052 |
| heuristic | 100 | 1.000 | 805.79 | 1.519 | 0.314 | 4.890 |

Friction bucket result:

| policy | mu bucket | episodes | success_rate | return_mean | lateral_rmse_mean | speed_mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| checkpoint | low | 26 | 0.462 | 443.78 | 2.178 | 4.519 |
| checkpoint | medium | 34 | 0.882 | 922.35 | 1.475 | 6.262 |
| checkpoint | high | 40 | 1.000 | 1048.07 | 0.998 | 6.871 |
| heuristic | low | 26 | 1.000 | 823.76 | 1.427 | 3.889 |
| heuristic | medium | 34 | 1.000 | 809.15 | 1.527 | 4.941 |
| heuristic | high | 40 | 1.000 | 791.25 | 1.571 | 5.497 |

Selected rollout plots:

```text
runs/rollouts_ppo_m4_figure_eight_history_seed61
```

Selected seeds:

| seed | mu | steps | terminated | return | purpose |
| ---: | ---: | ---: | --- | ---: | --- |
| 7 | 0.989 | 800 | false | 1016.53 | high-mu success |
| 13 | 0.252 | 343 | true | 95.18 | low-mu failure |
| 21 | 0.351 | 526 | true | -34.11 | low-mu failure |
| 44 | 0.554 | 312 | true | 325.93 | medium-mu failure |

Interpretation:

- The first trained figure-eight policy is useful evidence but not an M4 pass.
  It gets higher return than the heuristic by driving faster, but lower success
  because it terminates in 18% of episodes.
- Failures are concentrated in low friction. The low `mu` bucket is only
  `0.462` success, while high `mu` is already `1.000`.
- The next M4 iteration should use a low-friction figure-eight recovery
  curriculum or lower-speed low-mu stage before tightening the benchmark.
- `info` and rollout traces now include `curvature` and `progress`, which are
  the fields needed for the next segment-level analysis.

## Low-Mu Recovery Negative Result

Config:

```text
configs/ppo_m4_figure_eight_low_mu_recovery.json
```

Command:

```bash
PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m4_figure_eight_low_mu_recovery.json \
  --init-checkpoint runs/ppo_m4_figure_eight_history_seed61/checkpoint.pt \
  --run-dir runs/ppo_m4_figure_eight_low_mu_seed67
```

Benchmark:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 100 \
  --policies heuristic checkpoint \
  --checkpoint runs/ppo_m4_figure_eight_low_mu_seed67/checkpoint.pt \
  --env-config configs/m4_figure_eight_eval.json \
  --run-dir runs/benchmark_ppo_m4_figure_eight_low_mu_seed67_100eval
```

Result:

| run | success_rate | return_mean | lateral_rmse_mean | low-mu success |
| --- | ---: | ---: | ---: | ---: |
| `runs/benchmark_ppo_m4_figure_eight_history_seed61_100eval` | 0.820 | 848.21 | 1.467 | 0.462 |
| `runs/benchmark_ppo_m4_figure_eight_low_mu_seed67_100eval` | 0.710 | 615.75 | 2.173 | 0.308 |

Interpretation:

- Naive low-mu oversampling made the policy worse and should not be treated as
  the M4 path forward.
- The likely issue is distribution shift/forgetting: the policy overfits the
  wide, slow low-mu recovery stages and loses medium-friction tracking quality.
- The next attempt should use a mixed replay curriculum or train/evaluate a
  more conservative survival-first objective instead of replacing most samples
  with low-mu stages.

## Survival-Penalty Recovery Result

Config:

```text
configs/ppo_m4_figure_eight_survival_recovery.json
```

This config adds `termination_penalty=8.0` and keeps a mixed friction
distribution instead of replacing most samples with low-mu episodes.

Command:

```bash
PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m4_figure_eight_survival_recovery.json \
  --init-checkpoint runs/ppo_m4_figure_eight_history_seed61/checkpoint.pt \
  --run-dir runs/ppo_m4_figure_eight_survival_seed71
```

Benchmark:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 100 \
  --policies heuristic checkpoint \
  --checkpoint runs/ppo_m4_figure_eight_survival_seed71/checkpoint.pt \
  --env-config configs/m4_figure_eight_eval.json \
  --run-dir runs/benchmark_ppo_m4_figure_eight_survival_seed71_100eval
```

Result:

| run | success_rate | return_mean | lateral_rmse_mean | low-mu success | medium-mu success | high-mu success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `runs/benchmark_ppo_m4_figure_eight_history_seed61_100eval` | 0.820 | 848.21 | 1.467 | 0.462 | 0.882 | 1.000 |
| `runs/benchmark_ppo_m4_figure_eight_low_mu_seed67_100eval` | 0.710 | 615.75 | 2.173 | 0.308 | 0.676 | 1.000 |
| `runs/benchmark_ppo_m4_figure_eight_survival_seed71_100eval` | 0.830 | 901.31 | 1.382 | 0.423 | 0.941 | 1.000 |

Interpretation:

- The survival penalty is the best M4 checkpoint so far by overall success,
  return, and lateral RMSE.
- It still does not solve low-friction figure-eight tracking: low-mu success is
  `0.423`, below the first M4 checkpoint's `0.462`.
- M4 remains open. The next high-leverage work is not another blind fine-tune;
  it should add segment-level diagnostics and/or a policy objective that
  explicitly separates low-mu survival from high-speed progress.

## Segment Diagnostics

Benchmark now writes two additional artifacts:

```text
segment_summary.csv
segment_mu_bucket_summary.csv
```

Each episode row also includes per-segment metrics for:

- `left_curve`;
- `right_curve`;
- `near_zero`.

The segment classifier uses the sign of path curvature, so it applies to both
figure-eight tracking and later avoidance paths.

Reference command:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 100 \
  --policies heuristic checkpoint \
  --checkpoint runs/ppo_m4_figure_eight_survival_seed71/checkpoint.pt \
  --env-config configs/m4_figure_eight_eval.json \
  --run-dir runs/benchmark_ppo_m4_figure_eight_survival_seed71_segment_100eval
```

Overall segment summary:

| policy | segment | episodes | success_rate | lateral_rmse_mean | speed_mean |
| --- | --- | ---: | ---: | ---: | ---: |
| checkpoint | left_curve | 99 | 0.838 | 1.354 | 6.313 |
| checkpoint | right_curve | 98 | 0.837 | 1.213 | 6.180 |
| heuristic | left_curve | 100 | 1.000 | 1.379 | 4.870 |
| heuristic | right_curve | 100 | 1.000 | 1.358 | 4.866 |

Segment by friction bucket:

| policy | mu bucket | segment | episodes | success_rate | lateral_rmse_mean | speed_mean |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| checkpoint | low | left_curve | 25 | 0.440 | 1.512 | 4.457 |
| checkpoint | low | right_curve | 24 | 0.417 | 1.702 | 4.754 |
| checkpoint | medium | left_curve | 34 | 0.941 | 1.753 | 6.647 |
| checkpoint | medium | right_curve | 34 | 0.941 | 1.259 | 6.055 |
| checkpoint | high | left_curve | 40 | 1.000 | 0.916 | 7.190 |
| checkpoint | high | right_curve | 40 | 1.000 | 0.880 | 7.143 |

Interpretation:

- The M4 blocker is primarily low friction, not only left/right transition. Low
  `mu` fails in both left and right curve segments.
- Right-curve low-mu tracking is slightly worse than left-curve low-mu tracking
  (`1.702` vs `1.512` lateral RMSE), so transition direction may matter, but it
  is secondary to friction.
- High-friction figure-eight is solved by the RL policy on this benchmark.
- The next M4 policy iteration should explicitly reduce low-mu speed/progress
  pressure or add recovery/survival structure in low-friction segments, rather
  than only oversampling low-mu episodes.

## Exit Criteria

M4 should not be considered complete until:

- a trained policy survives full figure-eight episodes on fixed benchmark seeds;
- metrics are reported by curvature-sign or segment type;
- selected rollouts show left/right drift transitions and recovery;
- the circular M2/M3 tasks still pass their existing smoke and benchmark paths.
