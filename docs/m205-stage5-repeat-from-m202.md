# M205 Stage5 Repeat From M202

M205 repeats the M204 stage5 recipe from M202 seed `5206` on fresh seeds.

Every repeat starts from M202 seed `5206`. No repeat chains from M204 or another
M205 checkpoint.

## Setup

Initial checkpoint for every repeat:

```text
runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt
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
  --seed 5210 \
  --init-checkpoint runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt \
  --run-dir runs/ppo_m205_stage5_from_m202_seed5210

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5211 \
  --init-checkpoint runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt \
  --run-dir runs/ppo_m205_stage5_from_m202_seed5211
```

Artifacts:

- `runs/ppo_m205_stage5_from_m202_seed5210/checkpoint.pt`
- `runs/ppo_m205_stage5_from_m202_seed5211/checkpoint.pt`

| Seed | Rollout return mean | Reward mean | Episodes | Outcome aux loss | Anchor loss | Eval return | Eval termination |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5210 | 71.131832 | 1.077846 | 11 | 0.159551 | 0.000262308 | 63.684173 | 0.20 |
| 5211 | 77.168006 | 1.122464 | 10 | 0.159037 | 0.000226249 | 63.669987 | 0.20 |

Both repeats have smoke eval termination `0.20`.

## Fixed M193 Objective Eval

Artifact:

```text
runs/m205_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M202 | Delta vs M204 |
| --- | ---: | ---: | ---: |
| m202_stage4 | 0.158585 | 0.000000 | 0.000110 |
| m204_stage5 | 0.158475 | -0.000110 | 0.000000 |
| m205_5210 | 0.158520 | -0.000065 | 0.000045 |
| m205_5211 | 0.158503 | -0.000082 | 0.000028 |

Both repeats improve the fixed M193 objective versus M202, but neither repeat
beats M204. M204 remains the best fixed-loss retained stage5 checkpoint.

## Replay Gates

All replay gates use M202 as the direct-parent retention baseline.

| Candidate | Corpus | Rows | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| m205_5210 | M183 M168 | 16 | 16 | 0.000067 | 0.000109 | true |
| m205_5210 | M183 M170 | 17 | 17 | 0.000060 | 0.000109 | true |
| m205_5210 | M193 M189 | 14 | 14 | 0.000049 | 0.000184 | true |
| m205_5211 | M183 M168 | 16 | 16 | 0.000132 | 0.000103 | true |
| m205_5211 | M183 M170 | 17 | 17 | 0.000127 | 0.000103 | true |
| m205_5211 | M193 M189 | 14 | 14 | 0.000124 | 0.000178 | true |

Artifacts:

- `runs/m205_5210_m183_m168_replay_gate_seed9510`
- `runs/m205_5210_m183_m170_replay_gate_seed9510`
- `runs/m205_5210_m193_m189_replay_gate_seed9630`
- `runs/m205_5211_m183_m168_replay_gate_seed9510`
- `runs/m205_5211_m183_m170_replay_gate_seed9510`
- `runs/m205_5211_m193_m189_replay_gate_seed9630`

Both repeats preserve old M183 replay and refreshed M193 replay.

## Behavior Retention

Artifacts:

- `runs/m205_behavior_gate_seed9505`
- `runs/m205_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m202_stage4 | 0.8625 | 0.1375 | 1.836613 |
| 9505 | m204_stage5 | 0.8625 | 0.1375 | 1.836804 |
| 9505 | m205_5210 | 0.8625 | 0.1375 | 1.836559 |
| 9505 | m205_5210_reset | 0.8500 | 0.1250 | 1.834620 |
| 9505 | m205_5210_zero_all | 0.8000 | 0.1250 | 1.852009 |
| 9505 | m205_5211 | 0.8625 | 0.1375 | 1.836665 |
| 9505 | m205_5211_reset | 0.8500 | 0.1250 | 1.834728 |
| 9505 | m205_5211_zero_all | 0.8000 | 0.1250 | 1.852112 |
| 9506 | m202_stage4 | 0.8625 | 0.1375 | 1.854222 |
| 9506 | m204_stage5 | 0.8625 | 0.1375 | 1.854415 |
| 9506 | m205_5210 | 0.8625 | 0.1375 | 1.854159 |
| 9506 | m205_5210_reset | 0.8500 | 0.1250 | 1.850907 |
| 9506 | m205_5210_zero_all | 0.8000 | 0.1250 | 1.869978 |
| 9506 | m205_5211 | 0.8625 | 0.1375 | 1.854271 |
| 9506 | m205_5211_reset | 0.8500 | 0.1250 | 1.851018 |
| 9506 | m205_5211_zero_all | 0.8000 | 0.1250 | 1.870089 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success. Zero-action-history remains behavior-neutral.

## Protected Key

Artifact:

```text
runs/m205_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m199_5201 | 1 / 1 | true | 0.119416 | 0.068219 | 0.051197 |
| m204_stage5 | 1 / 1 | true | 0.189607 | 0.094102 | 0.095505 |
| m205_5210 | 1 / 1 | true | 0.189370 | 0.093572 | 0.095797 |
| m205_5211 | 1 / 1 | true | 0.189096 | 0.093477 | 0.095619 |

Protected key `9944|perturbed|28|28` is retained for both repeats.

## Decision

M205 is positive repeat evidence, but not a new best checkpoint:

- both repeats restart from M202 seed `5206`, not M204;
- both improve fixed M193 objective versus M202;
- neither repeat beats M204 on fixed M193 objective;
- both repeats have smoke eval termination `0.20`;
- both preserve behavior seeds `9505` and `9506`;
- both preserve old M183 replay drops `16/16` and `17/17`;
- both preserve refreshed M193 replay drops `14/14`;
- protected key passes for both repeats.

M204 remains the best fixed-loss retained stage5 checkpoint.

Decision:

```text
admit_guarded_stage6_from_m204
```

Next step:

```text
m206-guarded-stage6-ppo-from-m204
```

Run only one short guarded stage6 from M204 before any repeat or longer
continuation.
