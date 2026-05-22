# M197 Guarded PPO Smoke Repeat From M194

M197 repeats the M196 guarded PPO smoke recipe from M194 on fresh seeds.

Every repeat starts from M194. No repeat chains from M196 or another M197
checkpoint.

## Setup

Initial checkpoint for every repeat:

```text
runs/m194_m189_actor_coupling_anchor100_s20_seed9850/optimized_checkpoint.pt
```

Training config:

```text
configs/ppo_m196_guarded_from_m194_smoke.json
```

The M196 recipe is unchanged:

```text
total_steps = 1024
rollout_steps = 128
num_envs = 8
learning_rate = 0.000001
outcome_intervention_aux_coef = 0.03
baseline_action_anchor_coef = 100.0
```

Actor inputs are unchanged.

## Training Repeats

Commands:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5197 \
  --init-checkpoint runs/m194_m189_actor_coupling_anchor100_s20_seed9850/optimized_checkpoint.pt \
  --run-dir runs/ppo_m197_guarded_from_m194_seed5197

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5198 \
  --init-checkpoint runs/m194_m189_actor_coupling_anchor100_s20_seed9850/optimized_checkpoint.pt \
  --run-dir runs/ppo_m197_guarded_from_m194_seed5198
```

Artifacts:

- `runs/ppo_m197_guarded_from_m194_seed5197/checkpoint.pt`
- `runs/ppo_m197_guarded_from_m194_seed5198/checkpoint.pt`

| Seed | Rollout return mean | Reward mean | Episodes | Outcome aux loss | Anchor loss | Eval return | Eval termination |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5197 | 71.341391 | 1.009382 | 10 | 0.157255 | 0.000006568 | 57.462138 | 0.20 |
| 5198 | 74.757165 | 1.112671 | 11 | 0.155242 | 0.000005011 | 58.257886 | 0.20 |

## Fixed M193 Objective Eval

Artifact:

```text
runs/m197_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M189 | Delta vs M194 |
| --- | ---: | ---: | ---: |
| m189_5193 | 0.160647 | 0.000000 | 0.001639 |
| m194_s20 | 0.159008 | -0.001639 | 0.000000 |
| m196_5196 | 0.159017 | -0.001630 | 0.000009 |
| m197_5197 | 0.158919 | -0.001728 | -0.000090 |
| m197_5198 | 0.158976 | -0.001671 | -0.000032 |

Both repeats improve the fixed M193 objective versus M194. Seed `5197` is the
best fixed-loss repeat.

## Replay Gates

All replay gates use M194 as the retention baseline.

| Candidate | Corpus | Rows | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| m197_5197 | M183 M168 | 16 | 16 | 0.000379 | 0.000113 | true |
| m197_5197 | M183 M170 | 17 | 17 | 0.000373 | 0.000112 | true |
| m197_5197 | M193 M189 | 14 | 14 | 0.000329 | 0.000160 | true |
| m197_5198 | M183 M168 | 16 | 16 | 0.000320 | 0.000097 | true |
| m197_5198 | M183 M170 | 17 | 17 | 0.000316 | 0.000096 | true |
| m197_5198 | M193 M189 | 14 | 14 | 0.000299 | 0.000142 | true |

Artifacts:

- `runs/m197_5197_m183_m168_replay_gate_seed9510`
- `runs/m197_5197_m183_m170_replay_gate_seed9510`
- `runs/m197_5197_m193_m189_replay_gate_seed9630`
- `runs/m197_5198_m183_m168_replay_gate_seed9510`
- `runs/m197_5198_m183_m170_replay_gate_seed9510`
- `runs/m197_5198_m193_m189_replay_gate_seed9630`

Both repeats preserve the old M183 replay surfaces and the refreshed M193
replay surface.

## Behavior Retention

Artifacts:

- `runs/m197_behavior_gate_seed9505`
- `runs/m197_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m194_s20 | 0.8625 | 0.1375 | 1.835998 |
| 9505 | m196_5196 | 0.8625 | 0.1375 | 1.835845 |
| 9505 | m197_5197 | 0.8625 | 0.1375 | 1.836155 |
| 9505 | m197_5197_reset | 0.8500 | 0.1250 | 1.834731 |
| 9505 | m197_5197_zero_all | 0.8000 | 0.1250 | 1.852215 |
| 9505 | m197_5198 | 0.8625 | 0.1375 | 1.836144 |
| 9505 | m197_5198_reset | 0.8500 | 0.1250 | 1.834684 |
| 9505 | m197_5198_zero_all | 0.8000 | 0.1250 | 1.852181 |
| 9506 | m194_s20 | 0.8625 | 0.1375 | 1.853627 |
| 9506 | m196_5196 | 0.8625 | 0.1375 | 1.853459 |
| 9506 | m197_5197 | 0.8625 | 0.1375 | 1.853776 |
| 9506 | m197_5197_reset | 0.8500 | 0.1250 | 1.851016 |
| 9506 | m197_5197_zero_all | 0.8000 | 0.1250 | 1.870199 |
| 9506 | m197_5198 | 0.8625 | 0.1375 | 1.853761 |
| 9506 | m197_5198_reset | 0.8500 | 0.1250 | 1.850968 |
| 9506 | m197_5198_zero_all | 0.8000 | 0.1250 | 1.870163 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success. Zero-action-history remains behavior-neutral.

## Protected Key

Artifact:

```text
runs/m197_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m189_5193 | 1 / 1 | true | 0.105758 | 0.070827 | 0.034931 |
| m194_s20 | 1 / 1 | true | 0.086678 | 0.066655 | 0.020023 |
| m196_5196 | 1 / 1 | true | 0.100118 | 0.067073 | 0.033045 |
| m197_5197 | 1 / 1 | true | 0.100966 | 0.067359 | 0.033607 |
| m197_5198 | 1 / 1 | true | 0.100804 | 0.067345 | 0.033459 |

Protected key `9944|perturbed|28|28` is retained.

## Decision

M197 is positive repeat evidence:

- both fresh seeds start from M194, not M196;
- both improve the fixed M193 objective versus M194;
- both preserve behavior seeds `9505` and `9506`;
- both preserve old M183 replay drops `16/16` and `17/17`;
- both preserve refreshed M193 replay drops `14/14`;
- protected key passes for both repeats.

Decision:

```text
admit_guarded_stage2_from_m197
```

Next step:

```text
m198-guarded-stage2-ppo-from-m197
```

M198 should start from the best fixed-loss retained repeat:

```text
runs/ppo_m197_guarded_from_m194_seed5197/checkpoint.pt
```

Run only one short guarded stage2 before any repeat or longer continuation.
