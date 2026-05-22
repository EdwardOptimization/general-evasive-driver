# M203 Stage4 Repeat From M201

M203 repeats the M202 stage4 recipe from M201 seed `5204` on fresh seeds.

Every repeat starts from M201 seed `5204`. No repeat chains from M202 or another
M203 checkpoint.

## Setup

Initial checkpoint for every repeat:

```text
runs/ppo_m201_stage3_from_m199_seed5204/checkpoint.pt
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
  --seed 5207 \
  --init-checkpoint runs/ppo_m201_stage3_from_m199_seed5204/checkpoint.pt \
  --run-dir runs/ppo_m203_stage4_from_m201_seed5207

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5208 \
  --init-checkpoint runs/ppo_m201_stage3_from_m199_seed5204/checkpoint.pt \
  --run-dir runs/ppo_m203_stage4_from_m201_seed5208
```

Artifacts:

- `runs/ppo_m203_stage4_from_m201_seed5207/checkpoint.pt`
- `runs/ppo_m203_stage4_from_m201_seed5208/checkpoint.pt`

| Seed | Rollout return mean | Reward mean | Episodes | Outcome aux loss | Anchor loss | Eval return | Eval termination |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5207 | 82.221936 | 1.136162 | 10 | 0.158538 | 0.000139376 | 53.012668 | 0.40 |
| 5208 | 77.502275 | 1.109427 | 10 | 0.166553 | 0.000189028 | 67.797005 | 0.20 |

Seed `5207` has elevated smoke eval termination. This is not a formal gate by
itself, but it limits the decision to a cautious single short continuation.

## Fixed M193 Objective Eval

Artifact:

```text
runs/m203_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M201_5204 | Delta vs M202 |
| --- | ---: | ---: | ---: |
| m201_5204 | 0.158730 | 0.000000 | 0.000145 |
| m201_5205 | 0.158755 | 0.000025 | 0.000171 |
| m202_stage4 | 0.158585 | -0.000145 | 0.000000 |
| m203_5207 | 0.158642 | -0.000089 | 0.000057 |
| m203_5208 | 0.158616 | -0.000114 | 0.000031 |

Both repeats improve the fixed M193 objective versus M201 seed `5204`, but
neither repeat beats M202. M202 remains the best fixed-loss retained stage4
checkpoint.

## Replay Gates

All replay gates use M201 seed `5204` as the direct-parent retention baseline.

| Candidate | Corpus | Rows | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| m203_5207 | M183 M168 | 16 | 16 | 0.000041 | 0.000098 | true |
| m203_5207 | M183 M170 | 17 | 17 | 0.000036 | 0.000097 | true |
| m203_5207 | M193 M189 | 14 | 14 | 0.000043 | 0.000161 | true |
| m203_5208 | M183 M168 | 16 | 16 | 0.000315 | 0.000113 | true |
| m203_5208 | M183 M170 | 17 | 17 | 0.000309 | 0.000112 | true |
| m203_5208 | M193 M189 | 14 | 14 | 0.000278 | 0.000181 | true |

Artifacts:

- `runs/m203_5207_m183_m168_replay_gate_seed9510`
- `runs/m203_5207_m183_m170_replay_gate_seed9510`
- `runs/m203_5207_m193_m189_replay_gate_seed9630`
- `runs/m203_5208_m183_m168_replay_gate_seed9510`
- `runs/m203_5208_m183_m170_replay_gate_seed9510`
- `runs/m203_5208_m193_m189_replay_gate_seed9630`

Both repeats preserve old M183 replay and refreshed M193 replay.

## Behavior Retention

Artifacts:

- `runs/m203_behavior_gate_seed9505`
- `runs/m203_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m201_5204 | 0.8625 | 0.1375 | 1.836406 |
| 9505 | m202_stage4 | 0.8625 | 0.1375 | 1.836613 |
| 9505 | m203_5207 | 0.8625 | 0.1375 | 1.836393 |
| 9505 | m203_5207_reset | 0.8500 | 0.1250 | 1.834541 |
| 9505 | m203_5207_zero_all | 0.8000 | 0.1250 | 1.851981 |
| 9505 | m203_5208 | 0.8625 | 0.1375 | 1.836582 |
| 9505 | m203_5208_reset | 0.8500 | 0.1250 | 1.834717 |
| 9505 | m203_5208_zero_all | 0.8000 | 0.1250 | 1.852114 |
| 9506 | m201_5204 | 0.8625 | 0.1375 | 1.854015 |
| 9506 | m202_stage4 | 0.8625 | 0.1375 | 1.854222 |
| 9506 | m203_5207 | 0.8625 | 0.1375 | 1.853991 |
| 9506 | m203_5207_reset | 0.8500 | 0.1250 | 1.850823 |
| 9506 | m203_5207_zero_all | 0.8000 | 0.1250 | 1.869948 |
| 9506 | m203_5208 | 0.8625 | 0.1375 | 1.854193 |
| 9506 | m203_5208_reset | 0.8500 | 0.1250 | 1.851006 |
| 9506 | m203_5208_zero_all | 0.8000 | 0.1250 | 1.870090 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success. Zero-action-history remains behavior-neutral.

## Protected Key

Artifact:

```text
runs/m203_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m199_5201 | 1 / 1 | true | 0.119416 | 0.068219 | 0.051197 |
| m202_stage4 | 1 / 1 | true | 0.166318 | 0.080886 | 0.085432 |
| m203_5207 | 1 / 1 | true | 0.165669 | 0.080173 | 0.085497 |
| m203_5208 | 1 / 1 | true | 0.166738 | 0.081000 | 0.085738 |

Protected key `9944|perturbed|28|28` is retained for both repeats.

## Decision

M203 is positive repeat evidence, but not a new best checkpoint:

- both repeats restart from M201 seed `5204`, not M202;
- both improve fixed M193 objective versus M201 seed `5204`;
- neither repeat beats M202 on fixed M193 objective;
- seed `5207` has elevated smoke eval termination `0.40`;
- both preserve behavior seeds `9505` and `9506`;
- both preserve old M183 replay drops `16/16` and `17/17`;
- both preserve refreshed M193 replay drops `14/14`;
- protected key passes for both repeats.

M202 remains the best fixed-loss retained stage4 checkpoint.

Decision:

```text
admit_guarded_stage5_from_m202
```

Next step:

```text
m204-guarded-stage5-ppo-from-m202
```

Run only one short guarded stage5 from M202 before any repeat or longer
continuation.
