# M186 M185 Guarded PPO Repeat

M185 was a positive single-seed PPO smoke from M184. M186 repeats the same
conservative recipe on fresh PPO seeds to check whether the replay-retention
result is stable before any longer stage.

This is a positive repeat milestone. It admits a short staged PPO extension
design, not long PPO.

## Setup

All repeat runs initialize independently from M184:

```text
runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt
```

They reuse:

```text
configs/ppo_m185_guarded_from_m184_smoke.json
```

The repeats are not chained from the M185 seed-5185 checkpoint.

## PPO Repeats

Seed `5186`:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/ppo_m185_guarded_from_m184_smoke.json \
  --seed 5186 \
  --init-checkpoint runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt \
  --run-dir runs/ppo_m186_guarded_from_m184_seed5186
```

Seed `5187`:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/ppo_m185_guarded_from_m184_smoke.json \
  --seed 5187 \
  --init-checkpoint runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt \
  --run-dir runs/ppo_m186_guarded_from_m184_seed5187
```

| Seed | Checkpoint | Return mean | Termination rate | Anchor loss |
| ---: | --- | ---: | ---: | ---: |
| 5186 | `runs/ppo_m186_guarded_from_m184_seed5186/checkpoint.pt` | 78.171999 | 0.0 | 0.000005485 |
| 5187 | `runs/ppo_m186_guarded_from_m184_seed5187/checkpoint.pt` | 81.653292 | 0.0 | 0.000024509 |

Both runs load M184 strictly as the init checkpoint and as the action-anchor
checkpoint.

## Fixed M183 Objective

Run:

```text
runs/m186_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M184 |
| --- | ---: | ---: |
| m184_s20 | 0.171518 | 0.000000 |
| m185_5185 | 0.171432 | -0.000086 |
| m186_5186 | 0.171486 | -0.000032 |
| m186_5187 | 0.171519 | +0.000001 |

M186 repeats are retention-positive but not uniformly objective-improving.
M185 seed `5185` remains the lowest fixed-loss checkpoint among this family.

## Boundary Replay

All repeats must preserve both M183 replay surfaces.

| Candidate | Corpus | Rows | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| m186_5186 | M168 strict | 16 | 16 | 16 | +0.000026 | +0.000116 | true |
| m186_5186 | M170 split | 17 | 17 | 17 | -0.001333 | -0.000058 | true |
| m186_5187 | M168 strict | 16 | 16 | 16 | +0.000070 | +0.000138 | true |
| m186_5187 | M170 split | 17 | 17 | 17 | -0.001291 | -0.000037 | true |

Every repeat retains every M168 and M170 success-drop row.

## Behavior Retention

Commands use `configs/m121_human_view_zero_obstacle_relvel.json`, 80 episodes,
and compare M184 with both repeats and response-history ablations.

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.846415 |
| m186_5186 | 0.8625 | 0.1375 | 1.846375 |
| m186_5186_reset | 0.8500 | 0.1250 | 1.842012 |
| m186_5186_zero_all | 0.8000 | 0.1250 | 1.856485 |
| m186_5186_noact | 0.8625 | 0.1375 | 1.847569 |
| m186_5187 | 0.8625 | 0.1375 | 1.846307 |
| m186_5187_reset | 0.8500 | 0.1250 | 1.842009 |
| m186_5187_zero_all | 0.8000 | 0.1250 | 1.856447 |
| m186_5187_noact | 0.8625 | 0.1375 | 1.847490 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.853940 |
| m186_5186 | 0.8625 | 0.1375 | 1.853894 |
| m186_5186_reset | 0.8500 | 0.1250 | 1.850160 |
| m186_5186_zero_all | 0.8000 | 0.1250 | 1.868460 |
| m186_5186_noact | 0.8625 | 0.1375 | 1.856444 |
| m186_5187 | 0.8625 | 0.1375 | 1.853829 |
| m186_5187_reset | 0.8500 | 0.1250 | 1.850158 |
| m186_5187_zero_all | 0.8000 | 0.1250 | 1.868425 |
| m186_5187_noact | 0.8625 | 0.1375 | 1.856367 |

Behavior retention passes for both repeats. Reset and zero-all ablations still
degrade success. No-action history remains behavior-neutral.

## Protected Key

Run:

```text
runs/m186_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m184_s20 | 1 / 1 | true |
| m186_5186 | 1 / 1 | true |
| m186_5187 | 1 / 1 | true |

Protected key `9944|perturbed|28|28` passes for both repeats.

## Decision

M186 is positive.

What passed:

- both repeats initialize independently from M184;
- both repeats preserve M168 and M170 M183 boundary replay success-drop counts;
- both repeats retain behavior success on seeds `9503` and `9504`;
- both repeats preserve reset/zero-all ablation degradation;
- both repeats pass the protected key.

What remains weak:

- fixed objective improvement is not uniform; seed `5187` is effectively flat
  versus M184;
- no-action history is still behavior-neutral;
- no staged continuation has passed yet.

Decision:

```text
admit_guarded_stage2_ppo_design
```

Next step: run one short staged PPO extension from the best retained fixed-loss
checkpoint, M185 seed `5185`, with the same M183 replay, behavior, and protected
key gates.
