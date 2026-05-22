# M190 Stage3 Repeat From M188

M189 was a positive single-seed stage3 result. M190 repeats the same stage3
recipe from M188 seed `5191` on fresh seeds before any longer or chained PPO
continuation.

This is a positive retention repeat, but not a reason to continue immediately to
stage4. The fixed M183 objective plateaus near M189, so the next step should be
a broader evaluation of the current best checkpoint.

## Setup

All repeats initialize from:

```text
runs/ppo_m188_stage2_from_m185_seed5191/checkpoint.pt
```

They reuse:

```text
configs/ppo_m185_guarded_from_m184_smoke.json
```

The action anchor remains M184, and actor inputs are unchanged.

## PPO Repeats

Seed `5194`:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/ppo_m185_guarded_from_m184_smoke.json \
  --seed 5194 \
  --init-checkpoint runs/ppo_m188_stage2_from_m185_seed5191/checkpoint.pt \
  --run-dir runs/ppo_m190_stage3_from_m188_seed5194
```

Seed `5195`:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/ppo_m185_guarded_from_m184_smoke.json \
  --seed 5195 \
  --init-checkpoint runs/ppo_m188_stage2_from_m185_seed5191/checkpoint.pt \
  --run-dir runs/ppo_m190_stage3_from_m188_seed5195
```

| Seed | Checkpoint | Return mean | Termination rate | Anchor loss |
| ---: | --- | ---: | ---: | ---: |
| 5194 | `runs/ppo_m190_stage3_from_m188_seed5194/checkpoint.pt` | 65.602787 | 0.2 | 0.000059935 |
| 5195 | `runs/ppo_m190_stage3_from_m188_seed5195/checkpoint.pt` | 67.340653 | 0.2 | 0.000075017 |

The short training eval is weaker than M189, so the formal behavior gates are
especially important.

## Fixed M183 Objective

Run:

```text
runs/m190_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M189 |
| --- | ---: | ---: |
| m184_s20 | 0.171518 | +0.000297 |
| m188_5191 | 0.171306 | +0.000085 |
| m189_5193 | 0.171221 | 0.000000 |
| m190_5194 | 0.171232 | +0.000011 |
| m190_5195 | 0.171232 | +0.000011 |

M190 repeats are close to M189 but do not improve the fixed M183 objective.
M189 remains the current fixed-loss best checkpoint.

## Boundary Replay

| Candidate | Corpus | Rows | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| m190_5194 | M168 strict | 16 | 16 | 16 | +0.000687 | +0.000356 | true |
| m190_5194 | M170 split | 17 | 17 | 17 | -0.000682 | +0.000179 | true |
| m190_5195 | M168 strict | 16 | 16 | 16 | +0.000912 | +0.000329 | true |
| m190_5195 | M170 split | 17 | 17 | 17 | -0.000453 | +0.000152 | true |

Every repeat preserves every M168 and M170 success-drop row.

## Behavior Retention

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.846415 |
| m189_5193 | 0.8625 | 0.1375 | 1.846815 |
| m190_5194 | 0.8625 | 0.1375 | 1.846805 |
| m190_5194_reset | 0.8500 | 0.1250 | 1.842226 |
| m190_5194_zero_all | 0.8000 | 0.1250 | 1.856565 |
| m190_5194_noact | 0.8625 | 0.1375 | 1.848287 |
| m190_5195 | 0.8625 | 0.1375 | 1.846961 |
| m190_5195_reset | 0.8500 | 0.1250 | 1.842276 |
| m190_5195_zero_all | 0.8000 | 0.1250 | 1.856573 |
| m190_5195_noact | 0.8625 | 0.1375 | 1.848513 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.853940 |
| m189_5193 | 0.8625 | 0.1375 | 1.854353 |
| m190_5194 | 0.8625 | 0.1375 | 1.854344 |
| m190_5194_reset | 0.8500 | 0.1250 | 1.850390 |
| m190_5194_zero_all | 0.8000 | 0.1250 | 1.868556 |
| m190_5194_noact | 0.8625 | 0.1375 | 1.857120 |
| m190_5195 | 0.8625 | 0.1375 | 1.854508 |
| m190_5195_reset | 0.8500 | 0.1250 | 1.850443 |
| m190_5195_zero_all | 0.8000 | 0.1250 | 1.868568 |
| m190_5195_noact | 0.8625 | 0.1375 | 1.857355 |

Behavior retention passes for both repeats. Reset and zero-all ablations still
degrade success. No-action history remains behavior-neutral.

## Protected Key

Run:

```text
runs/m190_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m184_s20 | 1 / 1 | true |
| m189_5193 | 1 / 1 | true |
| m190_5194 | 1 / 1 | true |
| m190_5195 | 1 / 1 | true |

Protected key `9944|perturbed|28|28` passes for both repeats.

## Decision

M190 is positive as a retention repeat.

What passed:

- both repeats initialize from M188 seed `5191`;
- both repeats preserve M168 and M170 M183 replay success-drop counts;
- both repeats retain behavior success on seeds `9503` and `9504`;
- both repeats preserve reset/zero-all ablation degradation;
- both repeats pass the protected key.

What remains weak:

- fixed M183 objective does not improve beyond M189;
- the short training eval has termination rate `0.2` for both repeats;
- no-action history remains behavior-neutral;
- repeated PPO work is still mostly measured on the same M183 boundary surfaces
  and two behavior seeds.

Decision:

```text
pause_stage4_for_broader_eval
```

Next step: run a broader current-best evaluation before any stage4 or longer
PPO continuation.
