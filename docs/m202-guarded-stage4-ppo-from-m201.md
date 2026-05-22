# M202 Guarded Stage4 PPO From M201

M202 runs one short guarded stage4 from the best fixed-loss retained M201
repeat.

This milestone tests one additional 1024-step continuation only. It does not
run stage4 repeats or a longer PPO continuation.

## Setup

Initial checkpoint:

```text
runs/ppo_m201_stage3_from_m199_seed5204/checkpoint.pt
```

Training config:

```text
configs/ppo_m196_guarded_from_m194_smoke.json
```

The config still anchors actions to M194. Actor inputs are unchanged.

## Training

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5206 \
  --init-checkpoint runs/ppo_m201_stage3_from_m199_seed5204/checkpoint.pt \
  --run-dir runs/ppo_m202_stage4_from_m201_seed5206
```

Artifact:

```text
runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt
```

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Outcome aux loss | Anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 76.136655 | 1.081332 | 11 | 0.155683 | 0.000187238 |

Smoke eval summary:

| Return mean | Steps mean | Termination rate | Lateral RMSE | Beta abs error |
| ---: | ---: | ---: | ---: | ---: |
| 66.732638 | 77.0 | 0.20 | 1.359798 | 0.131685 |

The smoke eval termination rate stays at `0.20`.

## Fixed M193 Objective Eval

Artifact:

```text
runs/m202_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M201_5204 |
| --- | ---: | ---: |
| m199_5201 | 0.158850 | 0.000120 |
| m200_stage3 | 0.158756 | 0.000026 |
| m201_5204 | 0.158730 | 0.000000 |
| m201_5205 | 0.158755 | 0.000025 |
| m202_stage4 | 0.158585 | -0.000145 |

M202 improves the fixed M193 objective beyond M201 seed `5204`.

## Replay Gates

All replay gates use M201 seed `5204` as the direct-parent retention baseline.

| Corpus | Rows | Baseline drops | M202 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 | 16 | 0.000361 | 0.000102 | true |
| M183 M170 | 17 | 17 | 17 | 0.000356 | 0.000102 | true |
| M193 M189 | 14 | 14 | 14 | 0.000331 | 0.000169 | true |

Artifacts:

- `runs/m202_m183_m168_replay_gate_seed9510`
- `runs/m202_m183_m170_replay_gate_seed9510`
- `runs/m202_m193_m189_replay_gate_seed9630`

M202 preserves the old M183 replay surfaces and the refreshed M193 replay
surface relative to its direct parent.

## Behavior Retention

Artifacts:

- `runs/m202_behavior_gate_seed9505`
- `runs/m202_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m201_5204 | 0.8625 | 0.1375 | 1.836406 |
| 9505 | m202_stage4 | 0.8625 | 0.1375 | 1.836613 |
| 9505 | m202_stage4_noact | 0.8625 | 0.1375 | 1.840309 |
| 9505 | m202_stage4_reset | 0.8500 | 0.1250 | 1.834700 |
| 9505 | m202_stage4_zero_all | 0.8000 | 0.1250 | 1.852089 |
| 9506 | m201_5204 | 0.8625 | 0.1375 | 1.854015 |
| 9506 | m202_stage4 | 0.8625 | 0.1375 | 1.854222 |
| 9506 | m202_stage4_noact | 0.8625 | 0.1375 | 1.857613 |
| 9506 | m202_stage4_reset | 0.8500 | 0.1250 | 1.850988 |
| 9506 | m202_stage4_zero_all | 0.8000 | 0.1250 | 1.870063 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success. Zero-action-history remains behavior-neutral.

## Protected Key

Artifact:

```text
runs/m202_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m199_5201 | 1 / 1 | true | 0.119416 | 0.068219 | 0.051197 |
| m201_5204 | 1 / 1 | true | 0.141907 | 0.071739 | 0.070168 |
| m202_stage4 | 1 / 1 | true | 0.166318 | 0.080886 | 0.085432 |

Protected key `9944|perturbed|28|28` is retained.

## Decision

M202 is positive as a single-seed stage4:

- it starts from M201 seed `5204`;
- fixed M193 objective improves versus M201 seed `5204`;
- behavior seeds `9505` and `9506` keep success `0.8625`;
- old M183 replay drops `16/16` and `17/17` are retained;
- refreshed M193 replay drops `14/14` are retained;
- protected key passes.

Decision:

```text
admit_stage4_repeat_from_m201
```

Next step:

```text
m203-stage4-repeat-from-m201
```

M203 should repeat the same stage4 recipe from M201 seed `5204` on fresh seeds.
Do not chain from M202 until repeat evidence is available.
