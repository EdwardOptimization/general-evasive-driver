# M201 Stage3 Repeat From M199

M201 repeats the M200 stage3 recipe from M199 seed `5201` on fresh seeds.

Every repeat starts from M199 seed `5201`. No repeat chains from M200 or another
M201 checkpoint.

## Setup

Initial checkpoint for every repeat:

```text
runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt
```

Training config:

```text
configs/ppo_m196_guarded_from_m194_smoke.json
```

The config still anchors actions to M194. Actor inputs are unchanged.

## Training Repeats

Commands:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5204 \
  --init-checkpoint runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt \
  --run-dir runs/ppo_m201_stage3_from_m199_seed5204

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5205 \
  --init-checkpoint runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt \
  --run-dir runs/ppo_m201_stage3_from_m199_seed5205
```

Artifacts:

- `runs/ppo_m201_stage3_from_m199_seed5204/checkpoint.pt`
- `runs/ppo_m201_stage3_from_m199_seed5205/checkpoint.pt`

| Seed | Rollout return mean | Reward mean | Episodes | Outcome aux loss | Anchor loss | Eval return | Eval termination |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5204 | 73.314315 | 1.111301 | 12 | 0.150796 | 0.000055632 | 68.211056 | 0.20 |
| 5205 | 69.668094 | 1.052557 | 11 | 0.158737 | 0.000111500 | 68.979830 | 0.20 |

M200's elevated smoke eval termination rate (`0.40`) did not repeat; both M201
repeats have smoke eval termination `0.20`.

## Fixed M193 Objective Eval

Artifact:

```text
runs/m201_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M199_5201 | Delta vs M200 |
| --- | ---: | ---: | ---: |
| m199_5201 | 0.158850 | 0.000000 | 0.000094 |
| m200_stage3 | 0.158756 | -0.000094 | 0.000000 |
| m201_5204 | 0.158730 | -0.000120 | -0.000026 |
| m201_5205 | 0.158755 | -0.000095 | -0.000000 |

Both repeats improve the fixed M193 objective versus M199. Seed `5204` is the
best fixed-loss retained stage3 checkpoint.

## Replay Gates

All replay gates use M199 seed `5201` as the retention baseline.

| Candidate | Corpus | Rows | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| m201_5204 | M183 M168 | 16 | 16 | 0.000570 | 0.000090 | true |
| m201_5204 | M183 M170 | 17 | 17 | 0.000567 | 0.000090 | true |
| m201_5204 | M193 M189 | 14 | 14 | 0.000526 | 0.000151 | true |
| m201_5205 | M183 M168 | 16 | 16 | 0.000388 | 0.000133 | true |
| m201_5205 | M183 M170 | 17 | 17 | 0.000380 | 0.000132 | true |
| m201_5205 | M193 M189 | 14 | 14 | 0.000309 | 0.000198 | true |

Artifacts:

- `runs/m201_5204_m183_m168_replay_gate_seed9510`
- `runs/m201_5204_m183_m170_replay_gate_seed9510`
- `runs/m201_5204_m193_m189_replay_gate_seed9630`
- `runs/m201_5205_m183_m168_replay_gate_seed9510`
- `runs/m201_5205_m183_m170_replay_gate_seed9510`
- `runs/m201_5205_m193_m189_replay_gate_seed9630`

Both repeats preserve old M183 replay and refreshed M193 replay.

## Behavior Retention

Artifacts:

- `runs/m201_behavior_gate_seed9505`
- `runs/m201_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m199_5201 | 0.8625 | 0.1375 | 1.836142 |
| 9505 | m200_stage3 | 0.8625 | 0.1375 | 1.836232 |
| 9505 | m201_5204 | 0.8625 | 0.1375 | 1.836406 |
| 9505 | m201_5204_reset | 0.8500 | 0.1250 | 1.834628 |
| 9505 | m201_5204_zero_all | 0.8000 | 0.1250 | 1.852068 |
| 9505 | m201_5205 | 0.8625 | 0.1375 | 1.836264 |
| 9505 | m201_5205_reset | 0.8500 | 0.1250 | 1.834644 |
| 9505 | m201_5205_zero_all | 0.8000 | 0.1250 | 1.852107 |
| 9506 | m199_5201 | 0.8625 | 0.1375 | 1.853758 |
| 9506 | m200_stage3 | 0.8625 | 0.1375 | 1.853846 |
| 9506 | m201_5204 | 0.8625 | 0.1375 | 1.854015 |
| 9506 | m201_5204_reset | 0.8500 | 0.1250 | 1.850912 |
| 9506 | m201_5204_zero_all | 0.8000 | 0.1250 | 1.870041 |
| 9506 | m201_5205 | 0.8625 | 0.1375 | 1.853879 |
| 9506 | m201_5205_reset | 0.8500 | 0.1250 | 1.850930 |
| 9506 | m201_5205_zero_all | 0.8000 | 0.1250 | 1.870084 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success. Zero-action-history remains behavior-neutral.

## Protected Key

Artifact:

```text
runs/m201_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m199_5201 | 1 / 1 | true | 0.119416 | 0.068219 | 0.051197 |
| m200_stage3 | 1 / 1 | true | 0.142441 | 0.071530 | 0.070911 |
| m201_5204 | 1 / 1 | true | 0.141907 | 0.071739 | 0.070168 |
| m201_5205 | 1 / 1 | true | 0.143114 | 0.071820 | 0.071294 |

Protected key `9944|perturbed|28|28` is retained.

## Decision

M201 is positive repeat evidence:

- both repeats start from M199 seed `5201`, not M200;
- both improve fixed M193 objective versus M199;
- M200's elevated smoke eval termination does not repeat;
- both preserve behavior seeds `9505` and `9506`;
- both preserve old M183 replay drops `16/16` and `17/17`;
- both preserve refreshed M193 replay drops `14/14`;
- protected key passes for both repeats.

Decision:

```text
admit_guarded_stage4_from_m201
```

Next step:

```text
m202-guarded-stage4-ppo-from-m201
```

M202 should start from the best fixed-loss retained repeat:

```text
runs/ppo_m201_stage3_from_m199_seed5204/checkpoint.pt
```

Run only one short guarded stage4 before any repeat or longer continuation.
