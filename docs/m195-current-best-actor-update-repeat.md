# M195 Current-Best Actor-Update Repeat

M194 was a positive single-seed actor update from M189. M195 repeats the same
low-drift actor-coupling recipe from the same M189 checkpoint on fresh seeds
before any PPO smoke.

This milestone does not run PPO.

## Setup

All repeats start from:

```text
runs/ppo_m189_stage3_from_m188_seed5193/checkpoint.pt
```

They use:

```text
runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.npz
```

The update recipe is unchanged from M194:

```text
steps = 20
learning_rate = 0.0001
train_scope = actor_coupling
action_anchor_coef = 100.0
```

## Actor-Update Repeats

| Seed | Checkpoint | Train loss improvement | Action-anchor MSE |
| ---: | --- | ---: | ---: |
| 9850 | `runs/m194_m189_actor_coupling_anchor100_s20_seed9850/optimized_checkpoint.pt` | 0.001666 | 0.000014546 |
| 9851 | `runs/m195_m189_actor_coupling_anchor100_s20_seed9851/optimized_checkpoint.pt` | 0.001155 | 0.000005755 |
| 9852 | `runs/m195_m189_actor_coupling_anchor100_s20_seed9852/optimized_checkpoint.pt` | 0.001267 | 0.000007878 |

Both fresh repeats improve the fixed training eval with very small anchor drift.

## Independent Fixed Eval

Artifact:

```text
runs/m195_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M189 |
| --- | ---: | ---: |
| m189_5193 | 0.160647 | 0.000000 |
| m194_s20 | 0.159008 | -0.001639 |
| m195_9851 | 0.159514 | -0.001133 |
| m195_9852 | 0.159406 | -0.001241 |

M195 repeats are positive versus M189, but M194 remains the best fixed-objective
actor-update checkpoint.

## Replay Gates

| Candidate | Corpus | Rows | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| m195_9851 | M183 M168 | 16 | 16 | -0.001270 | -0.000069 | true |
| m195_9851 | M183 M170 | 17 | 17 | -0.001267 | -0.000062 | true |
| m195_9851 | M193 M189 | 14 | 14 | -0.001104 | -0.000068 | true |
| m195_9852 | M183 M168 | 16 | 16 | -0.001498 | -0.000087 | true |
| m195_9852 | M183 M170 | 17 | 17 | -0.001491 | -0.000081 | true |
| m195_9852 | M193 M189 | 14 | 14 | -0.001252 | -0.000086 | true |

Both repeats preserve the old M183 replay surfaces and the refreshed M193 replay
surface.

## Behavior Retention

Artifacts:

- `runs/m195_behavior_gate_seed9505`
- `runs/m195_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m189_5193 | 0.8625 | 0.1375 | 1.838230 |
| 9505 | m194_s20 | 0.8625 | 0.1375 | 1.835998 |
| 9505 | m195_9851 | 0.8625 | 0.1375 | 1.837606 |
| 9505 | m195_9851_reset | 0.8500 | 0.1250 | 1.835638 |
| 9505 | m195_9851_zero_all | 0.8000 | 0.1250 | 1.853171 |
| 9505 | m195_9852 | 0.8625 | 0.1375 | 1.837615 |
| 9505 | m195_9852_reset | 0.8500 | 0.1250 | 1.835620 |
| 9505 | m195_9852_zero_all | 0.8000 | 0.1250 | 1.853218 |
| 9506 | m189_5193 | 0.8625 | 0.1375 | 1.855994 |
| 9506 | m194_s20 | 0.8625 | 0.1375 | 1.853627 |
| 9506 | m195_9851 | 0.8625 | 0.1375 | 1.855338 |
| 9506 | m195_9851_reset | 0.8500 | 0.1250 | 1.851951 |
| 9506 | m195_9851_zero_all | 0.8000 | 0.1250 | 1.871236 |
| 9506 | m195_9852 | 0.8625 | 0.1375 | 1.855337 |
| 9506 | m195_9852_reset | 0.8500 | 0.1250 | 1.851931 |
| 9506 | m195_9852_zero_all | 0.8000 | 0.1250 | 1.871286 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success.

## Protected Key

Artifact:

```text
runs/m195_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m189_5193 | 1 / 1 | true |
| m194_s20 | 1 / 1 | true |
| m195_9851 | 1 / 1 | true |
| m195_9852 | 1 / 1 | true |

Protected key `9944|perturbed|28|28` is retained.

## Decision

M195 is positive as repeat evidence:

- fresh actor-update seeds both improve the fixed M193 objective versus M189;
- both repeats preserve behavior, protected key, old M183 replay, and refreshed
  M193 replay;
- M194 remains the best fixed-objective actor-update checkpoint.

Decision:

```text
admit_guarded_ppo_smoke_from_m194
```

Next step:

```text
m196-guarded-ppo-smoke-from-m194
```

M196 should run only a tiny guarded PPO smoke from M194. It must be rejected if
it weakens behavior, protected key, old M183 replay, or refreshed M193 replay.
