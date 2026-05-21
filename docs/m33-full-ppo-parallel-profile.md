# M33 Full PPO Parallel Profile

Last updated: 2026-05-21

## Motivation

M32 showed rollout-only speedup for parallel mode at 8-16 envs. M33 checks
whether that survives a short full PPO run including model inference, recurrent
sequence PPO update, CUDA work, checkpointing, and final eval.

## Command

Parallel:

```bash
/usr/bin/time -p conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m30_mixed_matched_response_driver.json \
  --total-steps 20480 \
  --rollout-steps 256 \
  --num-envs 16 \
  --seed 1332 \
  --device cuda \
  --vector-env-mode parallel \
  --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --run-dir runs/m33_parallel_ppo_profile_seed1332
```

Sync:

```bash
/usr/bin/time -p conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m30_mixed_matched_response_driver.json \
  --total-steps 20480 \
  --rollout-steps 256 \
  --num-envs 16 \
  --seed 1332 \
  --device cuda \
  --vector-env-mode sync \
  --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --run-dir runs/m33_sync_ppo_profile_seed1332
```

## Result

| Mode | Real seconds | User seconds | Sys seconds | Eval return | Termination |
| --- | ---: | ---: | ---: | ---: | ---: |
| parallel | 50.99 | 47.31 | 11.43 | 61.042 | 0.100 |
| sync | 53.48 | 44.80 | 10.44 | 61.042 | 0.100 |

The training/eval outputs are identical for the same seed and config. Parallel
mode is about 4.7% faster on this short full PPO profile.

## Determinism Check

File-level checks:

- `train_metrics.csv`: byte-identical;
- `eval_summary.json`: byte-identical;
- model tensors in `checkpoint.pt`: maximum absolute difference `0.0` across
  all 15 tensors;
- checkpoint file hash: different.

The checkpoint hash differs only because the saved config records
`vector_env_mode` as `parallel` or `sync`. The learned model state and reported
behavior are identical. Therefore switching sync versus parallel does not create
a numerical training diff for this deterministic profile; it only changes
metadata in the artifact.

## Conclusion

Parallel rollout is usable but not a major training accelerator yet. The modest
full-training gain means rollout is only part of runtime; recurrent PPO updates,
CUDA work, and process IPC still matter. Use `vector_env_mode=parallel` only for
longer 16-env runs where a small speed gain is worth the extra process
complexity.
