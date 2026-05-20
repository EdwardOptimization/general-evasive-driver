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

## Exit Criteria

M4 should not be considered complete until:

- a trained policy survives full figure-eight episodes on fixed benchmark seeds;
- metrics are reported by curvature-sign or segment type;
- selected rollouts show left/right drift transitions and recovery;
- the circular M2/M3 tasks still pass their existing smoke and benchmark paths.
