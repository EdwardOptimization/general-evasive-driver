# M204 Guarded Stage5 PPO From M202

M204 runs one short guarded stage5 from the best fixed-loss retained stage4
checkpoint.

This milestone tests one additional 1024-step continuation only. It does not
run stage5 repeats or a longer PPO continuation.

## Setup

Initial checkpoint:

```text
runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt
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
  --seed 5209 \
  --init-checkpoint runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt \
  --run-dir runs/ppo_m204_stage5_from_m202_seed5209
```

Artifact:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Outcome aux loss | Anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 74.501795 | 1.082520 | 9 | 0.159480 | 0.000293412 |

Smoke eval summary:

| Return mean | Steps mean | Termination rate | Lateral RMSE | Beta abs error |
| ---: | ---: | ---: | ---: | ---: |
| 64.183124 | 72.4 | 0.20 | 1.278368 | 0.207660 |

The smoke eval termination rate stays at `0.20`.

## Fixed M193 Objective Eval

Artifact:

```text
runs/m204_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M202 |
| --- | ---: | ---: |
| m202_stage4 | 0.158585 | 0.000000 |
| m203_5207 | 0.158642 | 0.000057 |
| m203_5208 | 0.158616 | 0.000031 |
| m204_stage5 | 0.158475 | -0.000110 |

M204 improves the fixed M193 objective beyond M202.

## Replay Gates

All replay gates use M202 as the direct-parent retention baseline.

| Corpus | Rows | Baseline drops | M204 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 | 16 | 0.000351 | 0.000099 | true |
| M183 M170 | 17 | 17 | 17 | 0.000347 | 0.000099 | true |
| M193 M189 | 14 | 14 | 14 | 0.000326 | 0.000175 | true |

Artifacts:

- `runs/m204_m183_m168_replay_gate_seed9510`
- `runs/m204_m183_m170_replay_gate_seed9510`
- `runs/m204_m193_m189_replay_gate_seed9630`

M204 preserves the old M183 replay surfaces and the refreshed M193 replay
surface relative to its direct parent.

## Behavior Retention

Artifacts:

- `runs/m204_behavior_gate_seed9505`
- `runs/m204_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m202_stage4 | 0.8625 | 0.1375 | 1.836613 |
| 9505 | m203_5208 | 0.8625 | 0.1375 | 1.836582 |
| 9505 | m204_stage5 | 0.8625 | 0.1375 | 1.836804 |
| 9505 | m204_stage5_noact | 0.8625 | 0.1375 | 1.840681 |
| 9505 | m204_stage5_reset | 0.8500 | 0.1250 | 1.834788 |
| 9505 | m204_stage5_zero_all | 0.8000 | 0.1250 | 1.852149 |
| 9506 | m202_stage4 | 0.8625 | 0.1375 | 1.854222 |
| 9506 | m203_5208 | 0.8625 | 0.1375 | 1.854193 |
| 9506 | m204_stage5 | 0.8625 | 0.1375 | 1.854415 |
| 9506 | m204_stage5_noact | 0.8625 | 0.1375 | 1.858073 |
| 9506 | m204_stage5_reset | 0.8500 | 0.1250 | 1.851079 |
| 9506 | m204_stage5_zero_all | 0.8000 | 0.1250 | 1.870128 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success. Zero-action-history remains behavior-neutral.

## Protected Key

Artifact:

```text
runs/m204_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m199_5201 | 1 / 1 | true | 0.119416 | 0.068219 | 0.051197 |
| m202_stage4 | 1 / 1 | true | 0.166318 | 0.080886 | 0.085432 |
| m204_stage5 | 1 / 1 | true | 0.189607 | 0.094102 | 0.095505 |

Protected key `9944|perturbed|28|28` is retained.

## Decision

M204 is positive as a single-seed stage5:

- it starts from M202 seed `5206`;
- fixed M193 objective improves versus M202;
- smoke eval termination stays at `0.20`;
- behavior seeds `9505` and `9506` keep success `0.8625`;
- old M183 replay drops `16/16` and `17/17` are retained;
- refreshed M193 replay drops `14/14` are retained;
- protected key passes.

Decision:

```text
admit_stage5_repeat_from_m202
```

Next step:

```text
m205-stage5-repeat-from-m202
```

M205 should repeat the same stage5 recipe from M202 seed `5206` on fresh seeds.
Do not chain from M204 until repeat evidence is available.
