# M187 Guarded Stage2 PPO From M185

M186 admitted one short stage2 PPO design after independent M185-recipe repeats
preserved behavior, protected key, and both M183 replay surfaces. M187 runs one
1024-step staged PPO extension from the best retained fixed-loss checkpoint,
M185 seed `5185`.

This is a positive single-seed stage2 result. It admits stage2 repeats, not a
longer PPO continuation.

## Setup

Initial checkpoint:

```text
runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt
```

The run reuses:

```text
configs/ppo_m185_guarded_from_m184_smoke.json
```

That config still anchors actions to M184:

```text
runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt
```

Actor inputs are unchanged.

## PPO Stage

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/ppo_m185_guarded_from_m184_smoke.json \
  --seed 5190 \
  --init-checkpoint runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt \
  --run-dir runs/ppo_m187_stage2_from_m185_seed5190
```

Training result:

```text
loaded_init_checkpoint=.../ppo_m185.../checkpoint.pt load_mode=strict
loaded_baseline_action_anchor=.../m184.../optimized_checkpoint.pt load_mode=strict
training_device=cuda num_envs=8 curriculum_stage=base
step=1024 update=1 stage=base rollout_return_mean=76.22 reward_mean=1.100 episode_count=10
saved=runs/ppo_m187_stage2_from_m185_seed5190/checkpoint.pt
```

Training metrics:

| Metric | Value |
| --- | ---: |
| response prediction loss | 0.049864 |
| outcome intervention loss | 0.170688 |
| baseline action-anchor loss | 0.000053014 |

Eval summary:

| Metric | Value |
| --- | ---: |
| return mean | 90.439008 |
| steps mean | 84.0 |
| termination rate | 0.0 |
| lateral RMSE mean | 0.959462 |
| beta abs error mean | 0.178178 |

Candidate:

```text
runs/ppo_m187_stage2_from_m185_seed5190/checkpoint.pt
```

## Fixed M183 Objective

Run:

```text
runs/m187_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M184 | Delta vs M185 |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.171518 | 0.000000 | +0.000086 |
| m185_5185 | 0.171432 | -0.000086 | 0.000000 |
| m187_stage2 | 0.171351 | -0.000167 | -0.000081 |

M187 improves the fixed M183 objective versus both M184 and M185.

## Boundary Replay

| Corpus | Rows | Baseline drops | M187 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M168 strict | 16 | 16 | 16 | +0.000339 | +0.000231 | true |
| M170 split | 17 | 17 | 17 | -0.001024 | +0.000055 | true |

M187 preserves every M168 and M170 success-drop row.

## Behavior Retention

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.846415 |
| m185_5185 | 0.8625 | 0.1375 | 1.846491 |
| m187_stage2 | 0.8625 | 0.1375 | 1.846652 |
| m187_stage2_reset | 0.8500 | 0.1250 | 1.842231 |
| m187_stage2_zero_all | 0.8000 | 0.1250 | 1.856595 |
| m187_stage2_noact | 0.8625 | 0.1375 | 1.847963 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.853940 |
| m185_5185 | 0.8625 | 0.1375 | 1.854015 |
| m187_stage2 | 0.8625 | 0.1375 | 1.854181 |
| m187_stage2_reset | 0.8500 | 0.1250 | 1.850391 |
| m187_stage2_zero_all | 0.8000 | 0.1250 | 1.868588 |
| m187_stage2_noact | 0.8625 | 0.1375 | 1.856819 |

Behavior retention passes. Reset and zero-all ablations continue to degrade
success. No-action history remains behavior-neutral.

## Protected Key

Run:

```text
runs/m187_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m184_s20 | 1 / 1 | true |
| m185_5185 | 1 / 1 | true |
| m187_stage2 | 1 / 1 | true |

Protected key `9944|perturbed|28|28` passes.

## Decision

M187 is positive.

What passed:

- fixed M183 objective improves versus M184 and M185;
- M168 and M170 boundary replay gates keep every success-drop row;
- behavior success matches M184/M185 on seeds `9503` and `9504`;
- reset and zero-all ablations still degrade success;
- protected key passes.

What remains weak:

- this is one stage2 seed;
- M187 training rollout had one terminated episode, though post-stage behavior
  gates pass;
- no-action history remains behavior-neutral;
- no longer PPO continuation has passed.

Decision:

```text
admit_stage2_repeat
```

Next step: repeat this stage2 recipe from M185 seed `5185` on fresh seeds before
any longer continuation.
