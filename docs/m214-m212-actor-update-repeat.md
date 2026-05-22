# M214 M212 Actor-Update Repeat

M214 repeats the M213 actor-update recipe from M204 on fresh seeds before any
PPO or continuation.

Every repeat restarts from:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

No repeat chains from M213.

## Actor Updates

Objective corpus:

```text
runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.npz
```

Both repeats use the M213 recipe:

| Field | Value |
| --- | ---: |
| train_scope | actor_coupling |
| steps | 20 |
| learning_rate | 0.0001 |
| action_anchor_coef | 100.0 |
| grad_clip_norm | 1.0 |

| Candidate | Seed | After loss mean | Improvement | Action-anchor MSE |
| --- | ---: | ---: | ---: | ---: |
| m214_10051 | 10051 | 0.201411 | 0.003712 | 0.000022536 |
| m214_10052 | 10052 | 0.200836 | 0.004287 | 0.000027340 |

Both repeats improve the objective during the actor-update run.

## Fixed Batch Eval

Artifact:

```text
runs/m214_fixed_batch_outcome_eval_seed37
```

| Policy | Fixed loss mean |
| --- | ---: |
| m204_5209 | 0.205221 |
| m213_s20 | 0.201354 |
| m214_10051 | 0.201478 |
| m214_10052 | 0.200899 |

Both repeats improve the fixed M212 objective versus M204. Seed `10052` is the
best fixed-loss candidate, but fixed objective improvement is not enough for
promotion.

## Replay Gates

Both repeats fail hard replay-retention gates.

| Candidate | Corpus | Rows | Candidate normal success | Candidate drops | Gate pass |
| --- | --- | ---: | ---: | ---: | --- |
| m214_10051 | M183 M168 | 16 | 0.1875 | 3 / 16 | false |
| m214_10051 | M183 M170 | 17 | 0.1765 | 3 / 17 | false |
| m214_10051 | M193 M189 | 14 | 0.2857 | 4 / 14 | false |
| m214_10051 | M212 M204 | 17 | 0.2941 | 5 / 17 | false |
| m214_10052 | M183 M168 | 16 | 0.1875 | 3 / 16 | false |
| m214_10052 | M183 M170 | 17 | 0.1765 | 3 / 17 | false |
| m214_10052 | M193 M189 | 14 | 0.3571 | 5 / 14 | false |
| m214_10052 | M212 M204 | 17 | 0.4118 | 7 / 17 | false |

Artifacts:

- `runs/m214_10051_m183_m168_replay_gate_seed9510`
- `runs/m214_10051_m183_m170_replay_gate_seed9510`
- `runs/m214_10051_m193_m189_replay_gate_seed9630`
- `runs/m214_10051_m212_m204_replay_gate_seed10040`
- `runs/m214_10052_m183_m168_replay_gate_seed9510`
- `runs/m214_10052_m183_m170_replay_gate_seed9510`
- `runs/m214_10052_m193_m189_replay_gate_seed9630`
- `runs/m214_10052_m212_m204_replay_gate_seed10040`

The failure is not a wrong-history-gap collapse. The core failure is
normal-history success retention: after the actor update, many near-boundary rows
that M204 solved under normal history no longer succeed.

## Behavior And Protected-Key Checks

The broad behavior and protected-key gates were run for manifest completeness
after the replay-retention failure was already known. They do not rescue M214.

Behavior artifacts:

- `runs/m214_behavior_gate_seed9505`
- `runs/m214_behavior_gate_seed9506`

| Candidate | Seed 9505 success | Seed 9505 margin | Seed 9506 success | Seed 9506 margin |
| --- | ---: | ---: | ---: | ---: |
| m204_5209 | 0.8625 | 1.836804 | 0.8625 | 1.854415 |
| m213_s20 | 0.8625 | 1.837023 | 0.8625 | 1.854666 |
| m214_10051 | 0.8625 | 1.834041 | 0.8625 | 1.851602 |
| m214_10052 | 0.8625 | 1.834200 | 0.8625 | 1.851715 |

For seed `10052`, reset-hidden success remains `0.85` and zero-all-response
success remains `0.80` on both behavior gates.

Protected-key artifact:

```text
runs/m214_critical_key_seed9944
```

| Candidate | Accepted cases | Normal margin | Wrong-history margin | Margin gap | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| m204_5209 | 1 / 1 | 0.189607 | 0.094102 | 0.095505 | true |
| m213_s20 | 1 / 1 | 0.155622 | 0.069832 | 0.085791 | true |
| m214_10051 | 1 / 1 | 0.139752 | 0.063222 | 0.076530 | true |
| m214_10052 | 1 / 1 | 0.136634 | 0.063396 | 0.073238 | true |

Interpretation: M214 preserves the broad aggregate behavior and the single
protected key, but it breaks the replay surfaces that are supposed to protect
near-boundary normal-history success. The hard reject therefore remains the
replay-retention failure.

## Decision

M214 is negative.

What it proves:

- the M212 objective can be improved by multiple actor-update seeds;
- objective improvement and small aggregate action-anchor MSE are not sufficient
  to retain near-boundary replay behavior;
- the M213 single-seed result is not repeat-stable under the current recipe.

Decision:

```text
reject_actor_update_repeat_replay_failure
```

Current retained base remains:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

M213 remains an interesting single-seed candidate, but it is not enough to admit
PPO.

Next step:

```text
m215-actor-update-repeat-failure-audit
```

M215 should audit why the repeat recipe can improve the objective while breaking
normal-success replay retention, then design a safer actor-update recipe before
any new update.
