# M189 Guarded Stage3 From M188

M188 admitted one short guarded stage3 design after stage2 repeats preserved
behavior, protected key, and both M183 replay surfaces. M189 runs one 1024-step
stage3 continuation from the best retained stage2 checkpoint, M188 seed `5191`.

This is a positive single-seed stage3 result. It admits stage3 repeats, not a
longer PPO continuation.

## Setup

Initial checkpoint:

```text
runs/ppo_m188_stage2_from_m185_seed5191/checkpoint.pt
```

The run reuses:

```text
configs/ppo_m185_guarded_from_m184_smoke.json
```

The action anchor remains M184:

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
  --seed 5193 \
  --init-checkpoint runs/ppo_m188_stage2_from_m185_seed5191/checkpoint.pt \
  --run-dir runs/ppo_m189_stage3_from_m188_seed5193
```

Training result:

```text
loaded_init_checkpoint=.../ppo_m188.../checkpoint.pt load_mode=strict
loaded_baseline_action_anchor=.../m184.../optimized_checkpoint.pt load_mode=strict
training_device=cuda num_envs=8 curriculum_stage=base
step=1024 update=1 stage=base rollout_return_mean=71.94 reward_mean=1.026 episode_count=11
saved=runs/ppo_m189_stage3_from_m188_seed5193/checkpoint.pt
```

Training metrics:

| Metric | Value |
| --- | ---: |
| response prediction loss | 0.063203 |
| outcome intervention loss | 0.171907 |
| baseline action-anchor loss | 0.000072021 |

Eval summary:

| Metric | Value |
| --- | ---: |
| return mean | 83.558409 |
| steps mean | 77.2 |
| termination rate | 0.0 |
| lateral RMSE mean | 0.907424 |
| beta abs error mean | 0.225684 |

Candidate:

```text
runs/ppo_m189_stage3_from_m188_seed5193/checkpoint.pt
```

## Fixed M183 Objective

Run:

```text
runs/m189_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M188 |
| --- | ---: | ---: |
| m184_s20 | 0.171518 | +0.000297 |
| m188_5191 | 0.171306 | 0.000000 |
| m189_stage3 | 0.171221 | -0.000085 |

M189 improves the fixed M183 objective versus M188 seed `5191`.

## Boundary Replay

| Corpus | Rows | Baseline drops | M189 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M168 strict | 16 | 16 | 16 | +0.000677 | +0.000331 | true |
| M170 split | 17 | 17 | 17 | -0.000689 | +0.000154 | true |

M189 preserves every M168 and M170 success-drop row.

## Behavior Retention

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.846415 |
| m188_5191 | 0.8625 | 0.1375 | 1.846699 |
| m189_stage3 | 0.8625 | 0.1375 | 1.846815 |
| m189_stage3_reset | 0.8500 | 0.1250 | 1.842174 |
| m189_stage3_zero_all | 0.8000 | 0.1250 | 1.856527 |
| m189_stage3_noact | 0.8625 | 0.1375 | 1.848355 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.853940 |
| m188_5191 | 0.8625 | 0.1375 | 1.854231 |
| m189_stage3 | 0.8625 | 0.1375 | 1.854353 |
| m189_stage3_reset | 0.8500 | 0.1250 | 1.850334 |
| m189_stage3_zero_all | 0.8000 | 0.1250 | 1.868511 |
| m189_stage3_noact | 0.8625 | 0.1375 | 1.857188 |

Behavior retention passes. Reset and zero-all ablations continue to degrade
success. No-action history remains behavior-neutral.

## Protected Key

Run:

```text
runs/m189_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m184_s20 | 1 / 1 | true |
| m188_5191 | 1 / 1 | true |
| m189_stage3 | 1 / 1 | true |

Protected key `9944|perturbed|28|28` passes.

## Decision

M189 is positive.

What passed:

- fixed M183 objective improves versus M188 seed `5191`;
- M168 and M170 boundary replay gates keep every success-drop row;
- behavior success matches M184/M188 on seeds `9503` and `9504`;
- reset and zero-all ablations still degrade success;
- protected key passes.

What remains weak:

- this is one stage3 seed;
- training rollout had one terminated episode, though post-stage behavior gates
  pass;
- no-action history remains behavior-neutral;
- gates are still concentrated on the M183 boundary proof surface and two
  behavior seeds.

Decision:

```text
admit_stage3_repeat
```

Next step: repeat this stage3 recipe from M188 seed `5191` on fresh seeds before
any longer continuation.
