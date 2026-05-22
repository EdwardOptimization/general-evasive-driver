# M200 Guarded Stage3 PPO From M199

M200 runs one short guarded stage3 from the best fixed-loss M199 repeat.

This milestone tests one additional 1024-step continuation only. It does not
run stage3 repeats or a longer PPO continuation.

## Setup

Initial checkpoint:

```text
runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt
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
  --seed 5203 \
  --init-checkpoint runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt \
  --run-dir runs/ppo_m200_stage3_from_m199_seed5203
```

Artifact:

```text
runs/ppo_m200_stage3_from_m199_seed5203/checkpoint.pt
```

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Outcome aux loss | Anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 77.065895 | 1.078283 | 10 | 0.159806 | 0.000055756 |

Smoke eval summary:

| Return mean | Steps mean | Termination rate | Lateral RMSE | Beta abs error |
| ---: | ---: | ---: | ---: | ---: |
| 50.831632 | 63.4 | 0.40 | 0.960989 | 0.131208 |

The smoke eval termination rate is worse than earlier stages. M200 acceptance
therefore depends on the formal gates, not on this smoke eval.

## Fixed M193 Objective Eval

Artifact:

```text
runs/m200_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M199_5201 |
| --- | ---: | ---: |
| m199_5201 | 0.158850 | 0.000000 |
| m199_5202 | 0.158857 | 0.000006 |
| m200_stage3 | 0.158756 | -0.000094 |

M200 improves the fixed M193 objective beyond the best M199 repeat.

## Replay Gates

All replay gates use M199 seed `5201` as the retention baseline.

| Corpus | Rows | Baseline drops | M200 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 | 16 | 0.000262 | 0.000127 | true |
| M183 M170 | 17 | 17 | 17 | 0.000254 | 0.000126 | true |
| M193 M189 | 14 | 14 | 14 | 0.000208 | 0.000189 | true |

Artifacts:

- `runs/m200_m183_m168_replay_gate_seed9510`
- `runs/m200_m183_m170_replay_gate_seed9510`
- `runs/m200_m193_m189_replay_gate_seed9630`

M200 preserves the old M183 replay surfaces and the refreshed M193 replay
surface.

## Behavior Retention

Artifacts:

- `runs/m200_behavior_gate_seed9505`
- `runs/m200_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m199_5201 | 0.8625 | 0.1375 | 1.836142 |
| 9505 | m200_stage3 | 0.8625 | 0.1375 | 1.836232 |
| 9505 | m200_stage3_noact | 0.8625 | 0.1375 | 1.839662 |
| 9505 | m200_stage3_reset | 0.8500 | 0.1250 | 1.834652 |
| 9505 | m200_stage3_zero_all | 0.8000 | 0.1250 | 1.852106 |
| 9506 | m199_5201 | 0.8625 | 0.1375 | 1.853758 |
| 9506 | m200_stage3 | 0.8625 | 0.1375 | 1.853846 |
| 9506 | m200_stage3_noact | 0.8625 | 0.1375 | 1.856867 |
| 9506 | m200_stage3_reset | 0.8500 | 0.1250 | 1.850938 |
| 9506 | m200_stage3_zero_all | 0.8000 | 0.1250 | 1.870085 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success. Zero-action-history remains behavior-neutral.

## Protected Key

Artifact:

```text
runs/m200_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m199_5201 | 1 / 1 | true | 0.119416 | 0.068219 | 0.051197 |
| m200_stage3 | 1 / 1 | true | 0.142441 | 0.071530 | 0.070911 |

Protected key `9944|perturbed|28|28` is retained.

## Decision

M200 is positive as a single-seed stage3:

- it starts from M199 seed `5201`;
- fixed M193 objective improves versus M199 seed `5201`;
- behavior seeds `9505` and `9506` keep success `0.8625`;
- old M183 replay drops `16/16` and `17/17` are retained;
- refreshed M193 replay drops `14/14` are retained;
- protected key passes.

The smoke eval termination rate was `0.40`, so M200 should not admit a longer
continuation directly.

Decision:

```text
admit_stage3_repeat_from_m199
```

Next step:

```text
m201-stage3-repeat-from-m199
```

M201 should repeat the same stage3 recipe from M199 seed `5201` on fresh seeds.
Do not chain from M200 until repeat evidence is available.
