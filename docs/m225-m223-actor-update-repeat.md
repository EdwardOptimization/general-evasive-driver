# M225 M223 Actor Update Repeat

M225 repeats the M224 snippet-anchored actor-update recipe from the same M219
seed `5216` source checkpoint on fresh seeds `10064` and `10065`.

The repeats are not chained from M224. Actor inputs are unchanged and no PPO is
run.

## Setup

Initial checkpoint for both repeats:

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

## Actor Updates

Artifacts:

- `runs/m225_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10064/optimized_checkpoint.pt`
- `runs/m225_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10065/optimized_checkpoint.pt`

| Seed | Before loss | After loss | Improvement |
| ---: | ---: | ---: | ---: |
| 10064 | 0.210572 | 0.209759 | 0.000813 |
| 10065 | 0.210572 | 0.209702 | 0.000870 |

Both repeats improve the objective on the optimizer's internal eval.

## Fixed M223 Eval

Artifact:

```text
runs/m225_fixed_batch_outcome_eval_seed37
```

| Policy | Fixed M223 loss |
| --- | ---: |
| m219_5216 | 0.210903 |
| m224_10063 | 0.209824 |
| m225_10064 | 0.210094 |
| m225_10065 | 0.210036 |

Both M225 repeats improve versus M219. They do not beat the single-seed M224
fixed loss, so M224 remains the best fixed-loss actor-update checkpoint.

## Replay Gates

Replay gates compare each M225 repeat against M219 seed `5216`.

| Candidate | Corpus | Rows | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| m225_10064 | M183 M168 | 16 | 16 / 16 | -0.001120 | 0.000058 | true |
| m225_10064 | M183 M170 | 17 | 17 / 17 | -0.001114 | 0.000056 | true |
| m225_10064 | M193 M189 | 14 | 14 / 14 | -0.000948 | 0.000030 | true |
| m225_10064 | M212 M204 | 17 | 17 / 17 | -0.001002 | 0.000032 | true |
| m225_10064 | M223 M219 | 17 | 17 / 17 | -0.001002 | 0.000032 | true |
| m225_10065 | M183 M168 | 16 | 16 / 16 | -0.001291 | 0.000036 | true |
| m225_10065 | M183 M170 | 17 | 17 / 17 | -0.001285 | 0.000035 | true |
| m225_10065 | M193 M189 | 14 | 14 / 14 | -0.001102 | 0.000001 | true |
| m225_10065 | M212 M204 | 17 | 17 / 17 | -0.001156 | 0.000003 | true |
| m225_10065 | M223 M219 | 17 | 17 / 17 | -0.001156 | 0.000003 | true |

Both repeats preserve old, current, and new replay surfaces.

## Behavior Retention

Artifacts:

- `runs/m225_behavior_gate_seed9505`
- `runs/m225_behavior_gate_seed9506`

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m219_5216 | 0.8625 | 0.1375 | 1.836432 |
| 9505 | m224_10063 | 0.8625 | 0.1375 | 1.835461 |
| 9505 | m225_10064 | 0.8625 | 0.1375 | 1.836139 |
| 9505 | m225_10065 | 0.8625 | 0.1375 | 1.835940 |
| 9505 | m225_10065_reset | 0.8500 | 0.1500 | 1.834284 |
| 9505 | m225_10065_zero_all | 0.8000 | 0.2000 | 1.851696 |
| 9506 | m219_5216 | 0.8625 | 0.1375 | 1.854007 |
| 9506 | m224_10063 | 0.8625 | 0.1375 | 1.852989 |
| 9506 | m225_10064 | 0.8625 | 0.1375 | 1.853706 |
| 9506 | m225_10065 | 0.8625 | 0.1375 | 1.853493 |
| 9506 | m225_10065_reset | 0.8500 | 0.1500 | 1.850561 |
| 9506 | m225_10065_zero_all | 0.8000 | 0.2000 | 1.869626 |

Behavior success is retained. Reset-hidden and zero-all-response ablations still
degrade success.

## Protected Key

Artifact:

```text
runs/m225_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m219_5216 | 1 / 1 | true | 0.199571 | 0.100774 | 0.098797 |
| m224_10063 | 1 / 1 | true | 0.186385 | 0.086925 | 0.099460 |
| m225_10064 | 1 / 1 | true | 0.190592 | 0.091350 | 0.099243 |
| m225_10065 | 1 / 1 | true | 0.188994 | 0.089702 | 0.099293 |
| m220_5217 | 0 / 1 | false | 0.214602 | 0.119100 | 0.095502 |

Both repeats retain the historical protected key.

## Decision

M225 is positive as repeat evidence:

- both repeats improve fixed M223 loss versus M219;
- both repeats preserve old M183, refreshed M193, current M212, and new M223
  replay gates;
- behavior seeds `9505` and `9506` retain success `0.8625`;
- protected key `9944|perturbed|28|28` passes for both repeats.

M224 remains the best fixed-loss actor-update checkpoint, while M225 proves the
recipe is repeat-stable.

Decision:

```text
admit_guarded_ppo_smoke_from_m224
```

Next step:

```text
m226-guarded-ppo-smoke-from-m224
```

M226 should run exactly one tiny guarded PPO smoke from M224, using the M223
M219 corpus and M224 as the action anchor. Do not run a longer PPO continuation
or a repeat before the single smoke is gated.
