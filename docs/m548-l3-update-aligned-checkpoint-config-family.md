# M548 L3 Update-Aligned Checkpoint Config Family

## Purpose

M548 implements update-aligned checkpoint configs after M547 showed that all
three L3 repair variants peaked at step `1792`, while the 512-step checkpoint
cadence did not save that update.

This milestone is infrastructure-only. It does not train or promote a
checkpoint.

## Added Configs

```text
configs/ppo_m548_l3_repair_fast_select_ckpt256_4096.json
configs/ppo_m548_l3_repair_lr1e4_ckpt256_4096.json
configs/ppo_m548_l3_repair_lr5e5_ckpt256_4096.json
```

Each config is identical to its M546 parent except:

```text
checkpoint_interval_steps = 256
```

This matches the PPO update cadence in the 4096-step route-pilot setup:

```text
rollout_steps = 64
num_envs = 4
global_step increment = 256
```

Therefore any update step reported in `train_metrics.csv` can be saved and
evaluated by the M545 route-only checkpoint-selection rule.

## Tests

`tests/test_history_baseline_configs.py` now verifies:

- all M548 configs preserve the `L3_online_gru` P0 actor contract;
- all M548 configs preserve the M546 parent environment exactly;
- each M548 config differs from its M546 parent only by
  `checkpoint_interval_steps`;
- `checkpoint_interval_steps` changes from `512` to `256`.

Focused validation:

```text
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests/test_history_baseline_configs.py
```

## Next Route Pilot

M549 should run the three M548 configs on seed `3540`, then evaluate all saved
interval checkpoints. The key question is narrow:

```text
Does the actual best training update pass deterministic route health when it is
saved and evaluated?
```

If yes, admit public diagnostics for the route-selected checkpoint. If no, the
blocker is not checkpoint cadence; it is deterministic route/eval mismatch or
the recurrent training objective itself.

## Decision

```text
update_aligned_checkpoint_config_pass_admit_m549_route_pilot
```
