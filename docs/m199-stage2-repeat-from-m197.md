# M199 Stage2 Repeat From M197

M199 repeats the M198 stage2 recipe from M197 seed `5197` on fresh seeds.

Every repeat starts from M197 seed `5197`. No repeat chains from M198 or another
M199 checkpoint.

## Setup

Initial checkpoint for every repeat:

```text
runs/ppo_m197_guarded_from_m194_seed5197/checkpoint.pt
```

Training config:

```text
configs/ppo_m196_guarded_from_m194_smoke.json
```

The config still anchors actions to M194.

## Training Repeats

Commands:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5201 \
  --init-checkpoint runs/ppo_m197_guarded_from_m194_seed5197/checkpoint.pt \
  --run-dir runs/ppo_m199_stage2_from_m197_seed5201

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5202 \
  --init-checkpoint runs/ppo_m197_guarded_from_m194_seed5197/checkpoint.pt \
  --run-dir runs/ppo_m199_stage2_from_m197_seed5202
```

Artifacts:

- `runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt`
- `runs/ppo_m199_stage2_from_m197_seed5202/checkpoint.pt`

| Seed | Rollout return mean | Reward mean | Episodes | Outcome aux loss | Anchor loss | Eval return | Eval termination |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5201 | 75.622042 | 1.056102 | 10 | 0.157412 | 0.000037700 | 60.909080 | 0.20 |
| 5202 | 72.093531 | 1.080684 | 11 | 0.161160 | 0.000015640 | 63.882565 | 0.20 |

## Fixed M193 Objective Eval

Artifact:

```text
runs/m199_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M197_5197 | Delta vs M198 |
| --- | ---: | ---: | ---: |
| m197_5197 | 0.158919 | 0.000000 | 0.000027 |
| m198_stage2 | 0.158892 | -0.000026 | 0.000000 |
| m199_5201 | 0.158850 | -0.000068 | -0.000042 |
| m199_5202 | 0.158857 | -0.000062 | -0.000036 |

Both repeats improve the fixed M193 objective versus M198. Seed `5201` is the
best fixed-loss retained stage2 checkpoint.

## Replay Gates

All replay gates use M197 seed `5197` as the retention baseline.

| Candidate | Corpus | Rows | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| m199_5201 | M183 M168 | 16 | 16 | 0.000084 | 0.000128 | true |
| m199_5201 | M183 M170 | 17 | 17 | 0.000076 | 0.000127 | true |
| m199_5201 | M193 M189 | 14 | 14 | 0.000049 | 0.000179 | true |
| m199_5202 | M183 M168 | 16 | 16 | 0.000255 | 0.000093 | true |
| m199_5202 | M183 M170 | 17 | 17 | 0.000251 | 0.000092 | true |
| m199_5202 | M193 M189 | 14 | 14 | 0.000241 | 0.000144 | true |

Artifacts:

- `runs/m199_5201_m183_m168_replay_gate_seed9510`
- `runs/m199_5201_m183_m170_replay_gate_seed9510`
- `runs/m199_5201_m193_m189_replay_gate_seed9630`
- `runs/m199_5202_m183_m168_replay_gate_seed9510`
- `runs/m199_5202_m183_m170_replay_gate_seed9510`
- `runs/m199_5202_m193_m189_replay_gate_seed9630`

Both repeats preserve old M183 replay and refreshed M193 replay.

## Behavior Retention

Artifacts:

- `runs/m199_behavior_gate_seed9505`
- `runs/m199_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m197_5197 | 0.8625 | 0.1375 | 1.836155 |
| 9505 | m198_stage2 | 0.8625 | 0.1375 | 1.836316 |
| 9505 | m199_5201 | 0.8625 | 0.1375 | 1.836142 |
| 9505 | m199_5201_reset | 0.8500 | 0.1250 | 1.834655 |
| 9505 | m199_5201_zero_all | 0.8000 | 0.1250 | 1.852139 |
| 9505 | m199_5202 | 0.8625 | 0.1375 | 1.836312 |
| 9505 | m199_5202_reset | 0.8500 | 0.1250 | 1.834661 |
| 9505 | m199_5202_zero_all | 0.8000 | 0.1250 | 1.852156 |
| 9506 | m197_5197 | 0.8625 | 0.1375 | 1.853776 |
| 9506 | m198_stage2 | 0.8625 | 0.1375 | 1.853935 |
| 9506 | m199_5201 | 0.8625 | 0.1375 | 1.853758 |
| 9506 | m199_5201_reset | 0.8500 | 0.1250 | 1.850939 |
| 9506 | m199_5201_zero_all | 0.8000 | 0.1250 | 1.870119 |
| 9506 | m199_5202 | 0.8625 | 0.1375 | 1.853927 |
| 9506 | m199_5202_reset | 0.8500 | 0.1250 | 1.850945 |
| 9506 | m199_5202_zero_all | 0.8000 | 0.1250 | 1.870134 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success. Zero-action-history remains behavior-neutral.

## Protected Key

Artifact:

```text
runs/m199_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m197_5197 | 1 / 1 | true | 0.100966 | 0.067359 | 0.033607 |
| m198_stage2 | 1 / 1 | true | 0.119167 | 0.068359 | 0.050808 |
| m199_5201 | 1 / 1 | true | 0.119416 | 0.068219 | 0.051197 |
| m199_5202 | 1 / 1 | true | 0.118540 | 0.068288 | 0.050252 |

Protected key `9944|perturbed|28|28` is retained.

## Decision

M199 is positive repeat evidence:

- both repeats start from M197 seed `5197`, not M198;
- both improve fixed M193 objective versus M198;
- both preserve behavior seeds `9505` and `9506`;
- both preserve old M183 replay drops `16/16` and `17/17`;
- both preserve refreshed M193 replay drops `14/14`;
- protected key passes for both repeats.

Decision:

```text
admit_guarded_stage3_from_m199
```

Next step:

```text
m200-guarded-stage3-ppo-from-m199
```

M200 should start from the best fixed-loss retained repeat:

```text
runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt
```

Run only one short guarded stage3 before any repeat or longer continuation.
