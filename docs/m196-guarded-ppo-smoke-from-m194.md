# M196 Guarded PPO Smoke From M194

M196 runs one tiny guarded PPO smoke from the current-best actor-update
checkpoint M194.

This milestone tests retention only. It does not admit a longer PPO
continuation.

## Setup

Initial checkpoint:

```text
runs/m194_m189_actor_coupling_anchor100_s20_seed9850/optimized_checkpoint.pt
```

Training config:

```text
configs/ppo_m196_guarded_from_m194_smoke.json
```

The config is the M185 guarded smoke recipe adapted to the refreshed M193 M189
corpus and the M194 action anchor:

```text
total_steps = 1024
rollout_steps = 128
num_envs = 8
learning_rate = 0.000001
outcome_intervention_aux_coef = 0.03
baseline_action_anchor_coef = 100.0
```

Actor inputs are unchanged.

## Training

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5196 \
  --init-checkpoint runs/m194_m189_actor_coupling_anchor100_s20_seed9850/optimized_checkpoint.pt \
  --run-dir runs/ppo_m196_guarded_from_m194_seed5196
```

Artifact:

```text
runs/ppo_m196_guarded_from_m194_seed5196/checkpoint.pt
```

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Outcome aux loss | Anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 76.494048 | 0.969877 | 9 | 0.164336 | 0.000005892 |

Smoke eval summary:

| Return mean | Steps mean | Termination rate | Lateral RMSE | Beta abs error |
| ---: | ---: | ---: | ---: | ---: |
| 60.416718 | 61.0 | 0.20 | 0.906124 | 0.204211 |

## Fixed M193 Objective Eval

Artifact:

```text
runs/m196_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M189 | Delta vs M194 |
| --- | ---: | ---: | ---: |
| m189_5193 | 0.160647 | 0.000000 | 0.001639 |
| m194_s20 | 0.159008 | -0.001639 | 0.000000 |
| m196_5196 | 0.159017 | -0.001630 | 0.000009 |

M196 stays clearly better than M189 on the fixed M193 objective, but does not
improve over M194. The result is retention, not objective progress.

## Replay Gates

All replay gates use M194 as the retention baseline.

| Corpus | Rows | Baseline drops | M196 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 | 16 | -0.000151 | 0.000122 | true |
| M183 M170 | 17 | 17 | 17 | -0.000159 | 0.000120 | true |
| M193 M189 | 14 | 14 | 14 | -0.000163 | 0.000163 | true |

Artifacts:

- `runs/m196_m183_m168_replay_gate_seed9510`
- `runs/m196_m183_m170_replay_gate_seed9510`
- `runs/m196_m193_m189_replay_gate_seed9630`

M196 preserves the old M183 replay surfaces and the refreshed M193 replay
surface.

## Behavior Retention

Artifacts:

- `runs/m196_behavior_gate_seed9505`
- `runs/m196_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m189_5193 | 0.8625 | 0.1375 | 1.838230 |
| 9505 | m194_s20 | 0.8625 | 0.1375 | 1.835998 |
| 9505 | m196_5196 | 0.8625 | 0.1375 | 1.835845 |
| 9505 | m196_5196_noact | 0.8625 | 0.1375 | 1.839495 |
| 9505 | m196_5196_reset | 0.8500 | 0.1250 | 1.834568 |
| 9505 | m196_5196_zero_all | 0.8000 | 0.1250 | 1.852136 |
| 9506 | m189_5193 | 0.8625 | 0.1375 | 1.855994 |
| 9506 | m194_s20 | 0.8625 | 0.1375 | 1.853627 |
| 9506 | m196_5196 | 0.8625 | 0.1375 | 1.853459 |
| 9506 | m196_5196_noact | 0.8625 | 0.1375 | 1.856507 |
| 9506 | m196_5196_reset | 0.8500 | 0.1250 | 1.850849 |
| 9506 | m196_5196_zero_all | 0.8000 | 0.1250 | 1.870116 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success. Zero-action-history remains a weak ablation on this
surface.

## Protected Key

Artifact:

```text
runs/m196_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m189_5193 | 1 / 1 | true | 0.105758 | 0.070827 | 0.034931 |
| m194_s20 | 1 / 1 | true | 0.086678 | 0.066655 | 0.020023 |
| m196_5196 | 1 / 1 | true | 0.100118 | 0.067073 | 0.033045 |

Protected key `9944|perturbed|28|28` is retained.

## Decision

M196 is positive as a retention smoke:

- it starts from M194 and runs only one 1024-step PPO smoke;
- fixed M193 objective remains better than M189 but does not beat M194;
- behavior seeds `9505` and `9506` keep success `0.8625`;
- protected key passes;
- old M183 replay drops `16/16` and `17/17` are retained;
- refreshed M193 replay drops `14/14` are retained.

Decision:

```text
admit_guarded_ppo_smoke_repeat_from_m194
```

Next step:

```text
m197-guarded-ppo-smoke-repeat-from-m194
```

M197 should repeat the exact M196 PPO smoke recipe from M194 on fresh seeds.
Do not run a longer PPO continuation until repeat smoke seeds preserve the same
behavior, protected key, old replay, and refreshed replay gates.
