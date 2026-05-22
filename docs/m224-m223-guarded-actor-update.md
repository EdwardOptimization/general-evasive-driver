# M224 M223 Guarded Actor Update

M224 runs exactly one small preferred-only snippet-anchored actor update from
M219 seed `5216` using the M223 M219 boundary-outcome corpus.

Actor inputs are unchanged. No PPO is run.

## Setup

Initial checkpoint:

```text
runs/ppo_m219_guarded_from_m217_seed5216/checkpoint.pt
```

Snippet corpus:

```text
runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz
```

Recipe:

```text
steps = 10
learning_rate = 0.00005
train_scope = actor_coupling
action_anchor_coef = 100
snippet_action_anchor_coef = 100
snippet_action_anchor_preferred_only = true
```

This is the smaller M216-style recipe, adapted to the M223 corpus and M219
source checkpoint.

## Actor Update

Artifact:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

| Metric | Value |
| --- | ---: |
| before eval loss mean | 0.210572 |
| after eval loss mean | 0.209490 |
| loss improvement | 0.001082 |
| after action anchor MSE | 0.000006931 |
| after snippet action anchor MSE | 0.000002688 |
| objective sanity pass | true |

## Fixed M223 Eval

Artifact:

```text
runs/m224_fixed_batch_outcome_eval_seed37
```

| Policy | Fixed M223 loss |
| --- | ---: |
| m219_5216 | 0.210903 |
| m224_10063 | 0.209824 |

M224 improves the fixed M223 objective on independent eval seed `37`.

## Replay Gates

Replay gates compare M224 against M219 seed `5216`.

| Corpus | Rows | M224 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | -0.001835 | 0.000039 | true |
| M183 M170 | 17 | 17 / 17 | -0.001830 | 0.000038 | true |
| M193 M189 | 14 | 14 / 14 | -0.001615 | -0.000003 | true |
| M212 M204 | 17 | 17 / 17 | -0.001674 | -0.000001 | true |
| M223 M219 | 17 | 17 / 17 | -0.001674 | -0.000001 | true |

All old, current, and new replay surfaces are retained. Normal-margin deltas are
negative but remain inside the pre-registered `0.005` tolerance.

## Behavior Retention

Artifacts:

- `runs/m224_behavior_gate_seed9505`
- `runs/m224_behavior_gate_seed9506`

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m219_5216 | 0.8625 | 0.1375 | 1.836432 |
| 9505 | m224_10063 | 0.8625 | 0.1375 | 1.835461 |
| 9505 | m224_10063_reset | 0.8500 | 0.1500 | 1.834120 |
| 9505 | m224_10063_zero_all | 0.8000 | 0.2000 | 1.853346 |
| 9506 | m219_5216 | 0.8625 | 0.1375 | 1.854007 |
| 9506 | m224_10063 | 0.8625 | 0.1375 | 1.852989 |
| 9506 | m224_10063_reset | 0.8500 | 0.1500 | 1.850393 |
| 9506 | m224_10063_zero_all | 0.8000 | 0.2000 | 1.871262 |

Behavior success is retained. Reset-hidden and zero-all-response ablations still
degrade success.

## Protected Key

Artifact:

```text
runs/m224_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m219_5216 | 1 / 1 | true | 0.199571 | 0.100774 | 0.098797 |
| m224_10063 | 1 / 1 | true | 0.186385 | 0.086925 | 0.099460 |
| m220_5217 | 0 / 1 | false | 0.214602 | 0.119100 | 0.095502 |

M224 retains the historical protected key. Unlike M220, it stays inside the
near-boundary normal-margin window.

## Decision

M224 is positive as a single-seed actor update:

- fixed M223 objective improves from `0.210903` to `0.209824`;
- old M183, refreshed M193, current M212, and new M223 replay gates pass;
- behavior seeds `9505` and `9506` retain success `0.8625`;
- protected key `9944|perturbed|28|28` passes.

Decision:

```text
admit_actor_update_repeat
```

Next step:

```text
m225-m223-actor-update-repeat
```

M225 must repeat the same M224 actor-update recipe from the same M219 seed
`5216` source checkpoint on fresh seeds. Do not chain from M224 and do not run
PPO before repeat evidence.
