# M213 M212 Guarded Actor Update

M213 runs one tiny anchored actor-coupling update from M204 using the M212 M204
boundary-outcome corpus.

This is not PPO. Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

Objective corpus:

```text
runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.npz
```

Candidate:

```text
runs/m213_m204_actor_coupling_anchor100_s20_seed10050/optimized_checkpoint.pt
```

## Actor Update

Recipe:

| Field | Value |
| --- | ---: |
| seed | 10050 |
| train_scope | actor_coupling |
| steps | 20 |
| learning_rate | 0.0001 |
| action_anchor_coef | 100.0 |
| grad_clip_norm | 1.0 |

Training/eval result:

| Metric | Value |
| --- | ---: |
| before loss mean | 0.205123 |
| after loss mean | 0.201290 |
| loss mean improvement | 0.003834 |
| after action-anchor MSE | 0.000017875 |
| objective sanity | true |

## Fixed Batch Eval

Artifact:

```text
runs/m213_fixed_batch_outcome_eval_seed37
```

| Policy | Fixed loss mean |
| --- | ---: |
| m204_5209 | 0.205221 |
| m213_s20 | 0.201354 |

Independent fixed-batch improvement:

```text
0.003867
```

## Replay Gates

| Corpus | Rows | Baseline drops | M213 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 | 16 | -0.001857 | 0.000018 | true |
| M183 M170 | 17 | 17 | 17 | -0.001830 | 0.000018 | true |
| M193 M189 | 14 | 14 | 14 | -0.001466 | -0.000054 | true |
| M212 M204 | 17 | 17 | 17 | -0.001623 | -0.000042 | true |

Artifacts:

- `runs/m213_m183_m168_replay_gate_seed9510`
- `runs/m213_m183_m170_replay_gate_seed9510`
- `runs/m213_m193_m189_replay_gate_seed9630`
- `runs/m213_m212_m204_replay_gate_seed10040`

M213 preserves both old replay surfaces and the new M212 replay surface.

## Behavior Retention

Artifacts:

- `runs/m213_behavior_gate_seed9505`
- `runs/m213_behavior_gate_seed9506`

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m204_5209 | 0.8625 | 0.1375 | 1.836804 |
| 9505 | m213_s20 | 0.8625 | 0.1375 | 1.837023 |
| 9505 | m213_s20_reset | 0.8500 | 0.1500 | 1.835076 |
| 9505 | m213_s20_zero_all | 0.8000 | 0.2000 | 1.852507 |
| 9506 | m204_5209 | 0.8625 | 0.1375 | 1.854415 |
| 9506 | m213_s20 | 0.8625 | 0.1375 | 1.854666 |
| 9506 | m213_s20_reset | 0.8500 | 0.1500 | 1.851377 |
| 9506 | m213_s20_zero_all | 0.8000 | 0.2000 | 1.870518 |

Behavior success is retained on both seeds. Reset and zero-all ablations still
degrade success.

## Protected Key

Artifact:

```text
runs/m213_critical_key_seed9944
```

Protected key:

```text
9944|perturbed|28|28
```

| Policy | Accepted cases | Normal success | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m204_5209 | 1 / 1 | true | 0.189607 | 0.094102 | 0.095505 |
| m206_stage6 | 0 / 1 | true | 0.207450 | 0.109548 | 0.097903 |
| m208_retry | 0 / 1 | true | 0.208742 | 0.111262 | 0.097479 |
| m213_s20 | 1 / 1 | true | 0.155622 | 0.069832 | 0.085791 |

M213 passes the protected key while M206 and M208 remain rejected controls.

## Decision

M213 is positive as a single-seed guarded actor update:

- M212 fixed objective improves on training and independent eval seeds;
- old M183 replay gates pass;
- refreshed M193 replay gate passes;
- new M212 replay gate passes;
- behavior success is retained on seeds `9505` and `9506`;
- protected key passes;
- reset/zero-all degradation remains visible.

Decision:

```text
admit_actor_update_repeat
```

Next step:

```text
m214-m212-actor-update-repeat
```

M214 should repeat the same anchored actor-update recipe from M204 on fresh
seeds. Do not chain from M213 and do not run PPO before repeat evidence passes.
