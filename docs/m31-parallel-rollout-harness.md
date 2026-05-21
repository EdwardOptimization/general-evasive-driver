# M31 Parallel Rollout Harness

Last updated: 2026-05-21

## Motivation

M30 training effectively used about one CPU core during rollout collection even
though the machine has 32 logical cores. `SyncAutoDriftVectorEnv` steps all envs
sequentially in one Python process, so increasing `num_envs` does not make
rollouts CPU-parallel.

M31 adds a process-based vector env path so future long training runs can try
8-core rollout collection without changing actor inputs.

## Implementation

New class:

```text
autodrift.vector_env.ParallelAutoDriftVectorEnv
```

New PPO config fields:

```text
vector_env_mode: "sync" | "parallel"
vector_env_start_method: "fork"
```

New CLI overrides:

```bash
--num-envs 8
--vector-env-mode parallel
--vector-env-start-method fork
```

The parent process still owns seed scheduling, including
`training_seed_mix_probability`. Workers only run `AutoDriftEnv.reset(seed=...)`
and `AutoDriftEnv.step(action)`. This preserves the hard-seed mix semantics.

## Smoke

Parallel command:

```bash
/usr/bin/time -p conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m30_mixed_matched_response_driver.json \
  --total-steps 4096 \
  --rollout-steps 128 \
  --num-envs 8 \
  --seed 1331 \
  --device cuda \
  --vector-env-mode parallel \
  --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --run-dir runs/ppo_m31_parallel_rollout_smoke_seed1331
```

Sync comparison:

```bash
/usr/bin/time -p conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m30_mixed_matched_response_driver.json \
  --total-steps 4096 \
  --rollout-steps 128 \
  --num-envs 8 \
  --seed 1331 \
  --device cuda \
  --vector-env-mode sync \
  --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --run-dir runs/ppo_m31_sync_rollout_smoke_seed1331
```

Result:

| Mode | Real seconds | Eval return | Termination |
| --- | ---: | ---: | ---: |
| parallel | 9.37 | 67.979 | 0.100 |
| sync | 9.19 | 67.979 | 0.100 |

Conclusion: M31 is functional but not yet a proven speedup. On this small
4096-step smoke, process startup and IPC overhead erase parallel rollout gains.
The next performance step should benchmark longer rollout-only sections and
tune `num_envs`, rollout length, and worker count before using parallel mode for
large training by default.
