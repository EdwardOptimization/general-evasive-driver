# M188 Stage2 Repeat From M185

M187 was a positive single-seed stage2 result. M188 repeats the same stage2
recipe from M185 seed `5185` on fresh seeds before any longer or chained PPO
continuation.

This is a positive stage2 repeat milestone. It admits one short guarded stage3
design, not long PPO.

## Setup

All repeats initialize from:

```text
runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt
```

They reuse:

```text
configs/ppo_m185_guarded_from_m184_smoke.json
```

The action anchor remains M184, and actor inputs are unchanged.

## PPO Repeats

Seed `5191`:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/ppo_m185_guarded_from_m184_smoke.json \
  --seed 5191 \
  --init-checkpoint runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt \
  --run-dir runs/ppo_m188_stage2_from_m185_seed5191
```

Seed `5192`:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/ppo_m185_guarded_from_m184_smoke.json \
  --seed 5192 \
  --init-checkpoint runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt \
  --run-dir runs/ppo_m188_stage2_from_m185_seed5192
```

| Seed | Checkpoint | Return mean | Termination rate | Anchor loss |
| ---: | --- | ---: | ---: | ---: |
| 5191 | `runs/ppo_m188_stage2_from_m185_seed5191/checkpoint.pt` | 89.884395 | 0.0 | 0.000045965 |
| 5192 | `runs/ppo_m188_stage2_from_m185_seed5192/checkpoint.pt` | 87.361795 | 0.0 | 0.000033323 |

## Fixed M183 Objective

Run:

```text
runs/m188_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M187 |
| --- | ---: | ---: |
| m184_s20 | 0.171518 | +0.000167 |
| m185_5185 | 0.171432 | +0.000081 |
| m187_5190 | 0.171351 | 0.000000 |
| m188_5191 | 0.171306 | -0.000045 |
| m188_5192 | 0.171353 | +0.000002 |

Seed `5191` is the lowest fixed-loss retained checkpoint in this branch.

## Boundary Replay

| Candidate | Corpus | Rows | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| m188_5191 | M168 strict | 16 | 16 | 16 | +0.000410 | +0.000224 | true |
| m188_5191 | M170 split | 17 | 17 | 17 | -0.000952 | +0.000048 | true |
| m188_5192 | M168 strict | 16 | 16 | 16 | +0.000150 | +0.000264 | true |
| m188_5192 | M170 split | 17 | 17 | 17 | -0.001217 | +0.000087 | true |

Every repeat preserves every M168 and M170 success-drop row.

## Behavior Retention

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.846415 |
| m187_5190 | 0.8625 | 0.1375 | 1.846652 |
| m188_5191 | 0.8625 | 0.1375 | 1.846699 |
| m188_5191_reset | 0.8500 | 0.1250 | 1.842234 |
| m188_5191_zero_all | 0.8000 | 0.1250 | 1.856590 |
| m188_5191_noact | 0.8625 | 0.1375 | 1.848036 |
| m188_5192 | 0.8625 | 0.1375 | 1.846528 |
| m188_5192_reset | 0.8500 | 0.1250 | 1.842217 |
| m188_5192_zero_all | 0.8000 | 0.1250 | 1.856614 |
| m188_5192_noact | 0.8625 | 0.1375 | 1.847784 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.853940 |
| m187_5190 | 0.8625 | 0.1375 | 1.854181 |
| m188_5191 | 0.8625 | 0.1375 | 1.854231 |
| m188_5191_reset | 0.8500 | 0.1250 | 1.850393 |
| m188_5191_zero_all | 0.8000 | 0.1250 | 1.868580 |
| m188_5191_noact | 0.8625 | 0.1375 | 1.856896 |
| m188_5192 | 0.8625 | 0.1375 | 1.854049 |
| m188_5192_reset | 0.8500 | 0.1250 | 1.850375 |
| m188_5192_zero_all | 0.8000 | 0.1250 | 1.868606 |
| m188_5192_noact | 0.8625 | 0.1375 | 1.856632 |

Behavior retention passes for both repeats. Reset and zero-all ablations still
degrade success. No-action history remains behavior-neutral.

## Protected Key

Run:

```text
runs/m188_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m184_s20 | 1 / 1 | true |
| m187_5190 | 1 / 1 | true |
| m188_5191 | 1 / 1 | true |
| m188_5192 | 1 / 1 | true |

Protected key `9944|perturbed|28|28` passes for both repeats.

## Decision

M188 is positive.

What passed:

- both stage2 repeats initialize from M185 seed `5185`;
- both repeats preserve M168 and M170 M183 replay success-drop counts;
- both repeats retain behavior success on seeds `9503` and `9504`;
- both repeats preserve reset/zero-all ablation degradation;
- both repeats pass the protected key;
- fixed objective remains at or below the M187 level, with seed `5191` best.

What remains weak:

- no-action history remains behavior-neutral;
- all gates are still on the M183 boundary surfaces and two behavior seeds;
- no chained stage3 continuation has passed.

Decision:

```text
admit_guarded_stage3_design
```

Next step: run one short guarded stage3 from the lowest fixed-loss retained
stage2 checkpoint, M188 seed `5191`.
