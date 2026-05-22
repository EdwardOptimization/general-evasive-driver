# M217 Snippet-Anchored Actor-Update Fresh Repeat

M217 repeats the M216 snippet-anchored actor-update recipe on fresh seeds before
any PPO or continuation. No PPO was run. Actor inputs were unchanged.

## Setup

Initial checkpoint:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

Objective corpus:

```text
runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.npz
```

Recipe is exactly the M216 recipe:

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

- `runs/m217_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10053/optimized_checkpoint.pt`
- `runs/m217_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10054/optimized_checkpoint.pt`

## Actor Update

| Candidate | Seed | After loss mean | Improvement | Generic anchor MSE | Snippet preferred-anchor MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| m217_10053 | 10053 | 0.204225 | 0.000898 | 0.000005192 | 0.000001489 |
| m217_10054 | 10054 | 0.204203 | 0.000920 | 0.000005598 | 0.000001491 |

## Fixed Batch Eval

Artifact:

```text
runs/m217_fixed_batch_outcome_eval_seed37
```

| Policy | Fixed M212 loss |
| --- | ---: |
| m204_5209 | 0.205221 |
| m216_10051 | 0.204291 |
| m216_10052 | 0.204297 |
| m217_10053 | 0.204313 |
| m217_10054 | 0.204291 |

Both M217 candidates improve over M204. Seed `10054` is the best fresh-repeat
candidate by fixed M212 loss.

## Replay Gates

Both fresh seeds retain all old and current replay surfaces.

| Candidate | Corpus | Rows | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| m217_10053 | M183 M168 | 16 | 16 / 16 | -0.001253 | 0.000087 | true |
| m217_10053 | M183 M170 | 17 | 17 / 17 | -0.001248 | 0.000084 | true |
| m217_10053 | M193 M189 | 14 | 14 / 14 | -0.001093 | 0.000048 | true |
| m217_10053 | M212 M204 | 17 | 17 / 17 | -0.001141 | 0.000051 | true |
| m217_10054 | M183 M168 | 16 | 16 / 16 | -0.001152 | 0.000090 | true |
| m217_10054 | M183 M170 | 17 | 17 / 17 | -0.001146 | 0.000088 | true |
| m217_10054 | M193 M189 | 14 | 14 / 14 | -0.000995 | 0.000051 | true |
| m217_10054 | M212 M204 | 17 | 17 / 17 | -0.001043 | 0.000056 | true |

## Behavior Retention

Artifacts:

- `runs/m217_behavior_gate_seed9505`
- `runs/m217_behavior_gate_seed9506`

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m204_5209 | 0.8625 | 0.1375 | 1.836804 |
| 9505 | m216_10051 | 0.8625 | 0.1375 | 1.836346 |
| 9505 | m217_10053 | 0.8625 | 0.1375 | 1.836191 |
| 9505 | m217_10054 | 0.8625 | 0.1375 | 1.836247 |
| 9505 | m217_10054_reset | 0.8500 | 0.1500 | 1.834491 |
| 9505 | m217_10054_zero_all | 0.8000 | 0.2000 | 1.851885 |
| 9506 | m204_5209 | 0.8625 | 0.1375 | 1.854415 |
| 9506 | m216_10051 | 0.8625 | 0.1375 | 1.853922 |
| 9506 | m217_10053 | 0.8625 | 0.1375 | 1.853761 |
| 9506 | m217_10054 | 0.8625 | 0.1375 | 1.853820 |
| 9506 | m217_10054_reset | 0.8500 | 0.1500 | 1.850772 |
| 9506 | m217_10054_zero_all | 0.8000 | 0.2000 | 1.869837 |

Behavior success is retained. Reset and zero-all-response ablations still
degrade success.

## Protected Key

Artifact:

```text
runs/m217_critical_key_seed9944
```

| Policy | Accepted cases | Normal margin | Wrong-history margin | Margin gap | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| m204_5209 | 1 / 1 | 0.189607 | 0.094102 | 0.095505 | true |
| m216_10051 | 1 / 1 | 0.177842 | 0.084437 | 0.093405 | true |
| m217_10053 | 1 / 1 | 0.177295 | 0.083835 | 0.093460 | true |
| m217_10054 | 1 / 1 | 0.176641 | 0.083504 | 0.093137 | true |
| m206_stage6 | 0 / 1 | 0.207450 | 0.109548 | 0.097903 | false |
| m208_retry | 0 / 1 | 0.208742 | 0.111262 | 0.097479 | false |

M217 passes the protected key while rejected M206/M208 controls remain rejected.

## Decision

M217 is positive as a fresh-seed repeat of the M216 recipe:

- both fresh seeds improve fixed M212 loss versus M204;
- both keep snippet preferred-action anchor MSE near `1.5e-6`;
- both pass old M183 replay, refreshed M193 replay, and current M212 replay;
- behavior success and protected key are retained.

Decision:

```text
admit_guarded_ppo_smoke_from_m217
```

Best M217 candidate:

```text
runs/m217_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10054/optimized_checkpoint.pt
```

Next step:

```text
m218-guarded-ppo-smoke-from-m217
```

M218 may run one tiny PPO smoke from M217 seed `10054` only. It must keep the
same actor inputs and preserve old/current replay, broad behavior, and protected
key before any repeat or longer continuation.
