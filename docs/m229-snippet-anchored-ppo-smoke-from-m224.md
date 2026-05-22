# M229 Snippet-Anchored PPO Smoke From M224

M229 runs exactly one PPO smoke from M224 with both rollout-state action
anchoring and preferred-only boundary snippet action anchoring.

Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

Config:

```text
configs/ppo_m229_snippet_anchor_from_m224_smoke.json
```

Key guard additions versus M226:

```text
snippet_action_anchor_coef = 100
snippet_action_anchor_checkpoint = M224
snippet_action_anchor_snapshot_npz = runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz
snippet_action_anchor_preferred_only = true
```

## Training

Artifact:

```text
runs/ppo_m229_snippet_anchor_from_m224_seed5219/checkpoint.pt
```

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Built-in eval return | Built-in eval termination | Snippet anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 62.878 | 0.966 | 10 | 66.449768 | 0.0000 | 0.000000019 |

The snippet anchor path was active:

```text
loaded_snippet_action_anchor=... preferred_only=True
```

## Fixed M223 Eval

Artifact:

```text
runs/m229_fixed_batch_outcome_eval_seed37
```

| Policy | Fixed M223 loss |
| --- | ---: |
| m219_5216 | 0.210903 |
| m224_10063 | 0.209824 |
| m225_10064 | 0.210094 |
| m225_10065 | 0.210036 |
| m226_5218 | 0.209834 |
| m229_5219 | 0.209728 |

M229 improves the fixed M223 loss versus M224 and M226.

## Replay Gates

Replay gates compare M229 against M224.

| Corpus | Rows | M229 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | 0.000653 | 0.000079 | true |
| M183 M170 | 17 | 17 / 17 | 0.000649 | 0.000081 | true |
| M193 M189 | 14 | 14 / 14 | 0.000598 | 0.000181 | true |
| M212 M204 | 17 | 17 / 17 | 0.000584 | 0.000173 | true |
| M223 M219 | 17 | 17 / 17 | 0.000585 | 0.000173 | true |

This is the main positive result: the preferred-only snippet anchor restores
the M183 M170 replay row that M226 lost.

## Behavior Diagnostic

Artifacts:

- `runs/m229_behavior_gate_seed9505`
- `runs/m229_behavior_gate_seed9506`

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m224_10063 | 0.8625 | 0.1375 | 1.835461 |
| 9505 | m229_5219 | 0.8625 | 0.1375 | 1.835749 |
| 9505 | m229_5219_reset | 0.8500 | 0.1500 | 1.834142 |
| 9505 | m229_5219_zero_all | 0.8000 | 0.2000 | 1.851472 |
| 9506 | m224_10063 | 0.8625 | 0.1375 | 1.852989 |
| 9506 | m229_5219 | 0.8625 | 0.1375 | 1.853274 |
| 9506 | m229_5219_reset | 0.8500 | 0.1500 | 1.850416 |
| 9506 | m229_5219_zero_all | 0.8000 | 0.2000 | 1.869388 |

Broad behavior is retained, and the reset/zero-all degradation structure remains
visible.

## Protected Key Diagnostic

Artifact:

```text
runs/m229_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m224_10063 | 1 / 1 | true | 0.186385 | 0.086925 | 0.099460 |
| m226_5218 | 0 / 1 | false | 0.203847 | 0.104163 | 0.099684 |
| m229_5219 | 0 / 1 | false | 0.205200 | 0.106179 | 0.099021 |

M229 still fails the protected key. The margin gap remains strong, but the
normal-history margin leaves the near-boundary window:

```text
0.205200 > 0.2
```

This is not broad behavior collapse and not old replay washout. It is a
protected-key normal-margin-window failure.

## Decision

M229 is rejected as a driver candidate:

- fixed M223 loss improves;
- old/current/new replay gates all pass;
- behavior seeds retain success;
- protected key fails by normal margin.

Decision:

```text
reject_protected_key_window_failure
```

Current best remains M224.

Next step:

```text
m230-m229-protected-key-failure-audit
```

Do not repeat or lengthen M229 until the protected-key failure is audited. The
next audit should determine whether the protected key is absent from the M223
snippet surface, whether the key itself should be refreshed into a current
protected surface, or whether PPO needs a separate protected-key snippet anchor.
