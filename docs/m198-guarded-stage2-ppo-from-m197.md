# M198 Guarded Stage2 PPO From M197

M198 runs one short guarded stage2 from the best fixed-loss M197 repeat.

This milestone tests one additional 1024-step continuation only. It does not
run stage2 repeats or a longer PPO continuation.

## Setup

Initial checkpoint:

```text
runs/ppo_m197_guarded_from_m194_seed5197/checkpoint.pt
```

Training config:

```text
configs/ppo_m196_guarded_from_m194_smoke.json
```

The config still anchors actions to M194:

```text
runs/m194_m189_actor_coupling_anchor100_s20_seed9850/optimized_checkpoint.pt
```

Actor inputs are unchanged.

## Training

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5200 \
  --init-checkpoint runs/ppo_m197_guarded_from_m194_seed5197/checkpoint.pt \
  --run-dir runs/ppo_m198_stage2_from_m197_seed5200
```

Artifact:

```text
runs/ppo_m198_stage2_from_m197_seed5200/checkpoint.pt
```

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Outcome aux loss | Anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 70.420810 | 0.979966 | 12 | 0.154335 | 0.000034307 |

Smoke eval summary:

| Return mean | Steps mean | Termination rate | Lateral RMSE | Beta abs error |
| ---: | ---: | ---: | ---: | ---: |
| 58.687986 | 59.6 | 0.20 | 1.040563 | 0.180163 |

## Fixed M193 Objective Eval

Artifact:

```text
runs/m198_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M197_5197 |
| --- | ---: | ---: |
| m189_5193 | 0.160647 | 0.001729 |
| m194_s20 | 0.159008 | 0.000116 |
| m196_5196 | 0.159017 | 0.000124 |
| m197_5197 | 0.158919 | 0.000000 |
| m197_5198 | 0.158976 | 0.000057 |
| m198_stage2 | 0.158892 | -0.000026 |

M198 improves the fixed M193 objective slightly beyond the best M197 repeat.

## Replay Gates

All replay gates use M197 seed `5197` as the retention baseline.

| Corpus | Rows | Baseline drops | M198 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 | 16 | 0.000267 | 0.000101 | true |
| M183 M170 | 17 | 17 | 17 | 0.000263 | 0.000100 | true |
| M193 M189 | 14 | 14 | 14 | 0.000254 | 0.000152 | true |

Artifacts:

- `runs/m198_m183_m168_replay_gate_seed9510`
- `runs/m198_m183_m170_replay_gate_seed9510`
- `runs/m198_m193_m189_replay_gate_seed9630`

M198 preserves the old M183 replay surfaces and the refreshed M193 replay
surface.

## Behavior Retention

Artifacts:

- `runs/m198_behavior_gate_seed9505`
- `runs/m198_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m197_5197 | 0.8625 | 0.1375 | 1.836155 |
| 9505 | m198_stage2 | 0.8625 | 0.1375 | 1.836316 |
| 9505 | m198_stage2_noact | 0.8625 | 0.1375 | 1.839659 |
| 9505 | m198_stage2_reset | 0.8500 | 0.1250 | 1.834717 |
| 9505 | m198_stage2_zero_all | 0.8000 | 0.1250 | 1.852191 |
| 9506 | m197_5197 | 0.8625 | 0.1375 | 1.853776 |
| 9506 | m198_stage2 | 0.8625 | 0.1375 | 1.853935 |
| 9506 | m198_stage2_noact | 0.8625 | 0.1375 | 1.856767 |
| 9506 | m198_stage2_reset | 0.8500 | 0.1250 | 1.851004 |
| 9506 | m198_stage2_zero_all | 0.8000 | 0.1250 | 1.870174 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success. Zero-action-history remains behavior-neutral.

## Protected Key

Artifact:

```text
runs/m198_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m189_5193 | 1 / 1 | true | 0.105758 | 0.070827 | 0.034931 |
| m197_5197 | 1 / 1 | true | 0.100966 | 0.067359 | 0.033607 |
| m198_stage2 | 1 / 1 | true | 0.119167 | 0.068359 | 0.050808 |

Protected key `9944|perturbed|28|28` is retained.

## Decision

M198 is positive as a single-seed stage2:

- it starts from M197 seed `5197`;
- fixed M193 objective improves slightly versus M197 seed `5197`;
- behavior seeds `9505` and `9506` keep success `0.8625`;
- old M183 replay drops `16/16` and `17/17` are retained;
- refreshed M193 replay drops `14/14` are retained;
- protected key passes.

Decision:

```text
admit_stage2_repeat_from_m197
```

Next step:

```text
m199-stage2-repeat-from-m197
```

M199 should repeat the same stage2 recipe from M197 seed `5197` on fresh seeds.
Do not chain from M198 until repeat evidence is available.
