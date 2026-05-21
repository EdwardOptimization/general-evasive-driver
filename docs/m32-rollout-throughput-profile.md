# M32 Rollout Throughput Profile

Last updated: 2026-05-21

## Motivation

M31 proved that process-based rollout works, but the 4096-step full-training
smoke was not faster than sync mode. M32 isolates rollout throughput from PPO
updates, CUDA work, checkpointing, and eval.

## Implementation

CLI:

```text
autodrift-rollout-throughput
```

Module:

```text
src/autodrift/rollout_throughput.py
```

Artifacts:

- `throughput_rows.csv`;
- `throughput_summary.csv`;
- `manifest.json`.

## Command

```bash
conda run -n autodrift python -m autodrift.rollout_throughput \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --modes sync parallel \
  --num-envs 1,2,4,8,16 \
  --rollout-steps 2048 \
  --repeats 2 \
  --seed 5100 \
  --run-dir runs/m32_rollout_throughput_seed5100
```

## Result

| Mode | Num envs | Env steps/s | Elapsed mean |
| --- | ---: | ---: | ---: |
| sync | 1 | 9835 | 0.208 |
| parallel | 1 | 3041 | 0.673 |
| sync | 2 | 10113 | 0.405 |
| parallel | 2 | 5195 | 0.788 |
| sync | 4 | 10240 | 0.800 |
| parallel | 4 | 8195 | 1.000 |
| sync | 8 | 10237 | 1.600 |
| parallel | 8 | 11311 | 1.449 |
| sync | 16 | 10103 | 3.243 |
| parallel | 16 | 11664 | 2.809 |

Conclusion: parallel rollout becomes useful around 8-16 envs, but the speedup
is modest. At 8 envs it improves rollout-only throughput by about 10%; at 16
envs by about 15%. It is harmful at 1-4 envs because process/IPC overhead is
larger than the work per step.

## Next Step

Do not switch every training run to parallel mode by default. Use parallel mode
only when:

- `num_envs >= 8`;
- rollout collection is known to dominate runtime;
- the run is long enough that worker startup overhead is negligible.

The next useful benchmark is a short full PPO profile at 16 envs comparing sync
and parallel with the same total steps, so rollout-only gains can be weighed
against PPO update and CUDA overhead.
