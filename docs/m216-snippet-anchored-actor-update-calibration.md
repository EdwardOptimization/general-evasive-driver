# M216 Snippet-Anchored Actor-Update Calibration

M216 tests the safer actor-update recipe selected by M215. It uses the known
M214 failure seeds to determine whether preferred-only snippet action anchoring
protects near-boundary normal-history success.

No PPO was run. Actor inputs were unchanged.

## Setup

Initial checkpoint:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

Objective corpus:

```text
runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.npz
```

Recipe:

| Field | Value |
| --- | ---: |
| train_scope | actor_coupling |
| steps | 10 |
| learning_rate | 0.00005 |
| action_anchor_coef | 100.0 |
| snippet_action_anchor_coef | 100.0 |
| snippet anchor hidden | preferred only |
| grad_clip_norm | 1.0 |

Candidates:

- `runs/m216_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10051/optimized_checkpoint.pt`
- `runs/m216_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10052/optimized_checkpoint.pt`

## Actor Update

| Candidate | Seed | After loss mean | Improvement | Generic anchor MSE | Snippet preferred-anchor MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| m216_10051 | 10051 | 0.204203 | 0.000920 | 0.000004964 | 0.000001572 |
| m216_10052 | 10052 | 0.204208 | 0.000915 | 0.000005184 | 0.000001541 |

The update is intentionally smaller than M213/M214. The purpose is retention,
not maximizing fixed contrast loss.

## Fixed Batch Eval

Artifact:

```text
runs/m216_fixed_batch_outcome_eval_seed37
```

| Policy | Fixed M212 loss |
| --- | ---: |
| m204_5209 | 0.205221 |
| m213_s20 | 0.201354 |
| m214_10051 | 0.201478 |
| m214_10052 | 0.200899 |
| m216_10051 | 0.204291 |
| m216_10052 | 0.204297 |

Both M216 candidates improve over M204, but the improvement is much smaller than
M213/M214. This is expected from the lower learning rate, lower step count, and
preferred-action anchor.

## Replay Gates

Both seeds retain all old and current replay surfaces.

| Candidate | Corpus | Rows | Candidate normal success | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| m216_10051 | M183 M168 | 16 | 1.0000 | 16 / 16 | -0.001071 | 0.000082 | true |
| m216_10051 | M183 M170 | 17 | 1.0000 | 17 / 17 | -0.001065 | 0.000080 | true |
| m216_10051 | M193 M189 | 14 | 1.0000 | 14 / 14 | -0.000917 | 0.000044 | true |
| m216_10051 | M212 M204 | 17 | 1.0000 | 17 / 17 | -0.000968 | 0.000048 | true |
| m216_10052 | M183 M168 | 16 | 1.0000 | 16 / 16 | -0.001155 | 0.000092 | true |
| m216_10052 | M183 M170 | 17 | 1.0000 | 17 / 17 | -0.001150 | 0.000090 | true |
| m216_10052 | M193 M189 | 14 | 1.0000 | 14 / 14 | -0.000994 | 0.000054 | true |
| m216_10052 | M212 M204 | 17 | 1.0000 | 17 / 17 | -0.001045 | 0.000058 | true |

This fixes the M214 failure mode on the known bad seeds: M214 lost normal
success on the same surfaces, while M216 keeps every normal-history row
successful.

## Behavior Retention

Artifacts:

- `runs/m216_behavior_gate_seed9505`
- `runs/m216_behavior_gate_seed9506`

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m204_5209 | 0.8625 | 0.1375 | 1.836804 |
| 9505 | m216_10051 | 0.8625 | 0.1375 | 1.836346 |
| 9505 | m216_10052 | 0.8625 | 0.1375 | 1.836219 |
| 9505 | m216_10052_reset | 0.8500 | 0.1500 | 1.834448 |
| 9505 | m216_10052_zero_all | 0.8000 | 0.2000 | 1.851882 |
| 9506 | m204_5209 | 0.8625 | 0.1375 | 1.854415 |
| 9506 | m216_10051 | 0.8625 | 0.1375 | 1.853922 |
| 9506 | m216_10052 | 0.8625 | 0.1375 | 1.853788 |
| 9506 | m216_10052_reset | 0.8500 | 0.1500 | 1.850727 |
| 9506 | m216_10052_zero_all | 0.8000 | 0.2000 | 1.869831 |

Behavior success is retained. Reset and zero-all-response ablations still
degrade success.

## Protected Key

Artifact:

```text
runs/m216_critical_key_seed9944
```

| Policy | Accepted cases | Normal margin | Wrong-history margin | Margin gap | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| m204_5209 | 1 / 1 | 0.189607 | 0.094102 | 0.095505 | true |
| m213_s20 | 1 / 1 | 0.155622 | 0.069832 | 0.085791 | true |
| m216_10051 | 1 / 1 | 0.177842 | 0.084437 | 0.093405 | true |
| m216_10052 | 1 / 1 | 0.177680 | 0.084092 | 0.093588 | true |
| m206_stage6 | 0 / 1 | 0.207450 | 0.109548 | 0.097903 | false |
| m208_retry | 0 / 1 | 0.208742 | 0.111262 | 0.097479 | false |

M216 passes the protected key while the rejected M206/M208 controls remain
rejected.

## Decision

M216 is positive as recipe calibration:

- both known M214 failure seeds improve the fixed M212 objective versus M204;
- preferred-only snippet anchoring keeps snippet action drift small;
- all old and current replay gates pass for both seeds;
- behavior success is retained;
- protected key passes.

It is not enough to admit PPO directly because these were known failure seeds
selected after M214. The next step is a fresh-seed repeat of the same
snippet-anchored recipe.

Decision:

```text
admit_fresh_snippet_anchor_repeat
```

Retained base remains:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

Best M216 calibration candidate:

```text
runs/m216_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10051/optimized_checkpoint.pt
```

Next step:

```text
m217-snippet-anchored-actor-update-fresh-repeat
```
