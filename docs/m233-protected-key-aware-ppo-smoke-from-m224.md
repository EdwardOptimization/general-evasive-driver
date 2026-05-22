# M233 Protected-Key-Aware PPO Smoke From M224

M233 runs exactly one 1024-step PPO smoke from M224 using the combined M223/M231
snippet corpus. This is the first PPO attempt after explicitly adding the
historical protected key to the snippet action anchor.

Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

Config:

```text
configs/ppo_m233_protected_key_combined_anchor_from_m224_smoke.json
```

Combined corpus:

```text
runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz
```

The M232 corpus has 18 rows:

| Source | Rows |
| --- | ---: |
| M223 boundary proof surface | 17 |
| M231 protected key `9944|perturbed|28|28` | 1 |

## Training

Artifact:

```text
runs/ppo_m233_protected_key_combined_anchor_from_m224_seed5220/checkpoint.pt
```

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Built-in eval termination | Outcome loss | Baseline anchor loss | Snippet anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 75.348 | 1.070 | 10 | 0.2000 | 0.252935 | 0.000004 | 0.000000043 |

The snippet anchor path was active:

```text
loaded_snippet_action_anchor=... snapshot=runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz preferred_only=True
```

## Fixed Objective

M233 does not improve the fixed losses.

Combined M232 objective:

| Policy | Loss |
| --- | ---: |
| m224_10063 | 0.246506 |
| m229_5219 | 0.246407 |
| m233_5220 | 0.246524 |

Original M223 objective:

| Policy | Loss |
| --- | ---: |
| m224_10063 | 0.209824 |
| m229_5219 | 0.209728 |
| m233_5220 | 0.209825 |

M233 is essentially at M224 on M223, but it is worse than M229 and slightly
worse than M224 on the combined M232 objective.

## Replay Gates

Replay gates compare M233 against M224.

| Corpus | Rows | M233 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | -0.000092 | 0.000117 | true |
| M183 M170 | 17 | 16 / 17 | -0.000103 | 0.000118 | false |
| M193 M189 | 14 | 14 / 14 | -0.000125 | 0.000225 | true |
| M212 M204 | 17 | 17 / 17 | -0.000133 | 0.000216 | true |
| M223 M219 | 17 | 17 / 17 | -0.000132 | 0.000216 | true |

The failed M183 M170 row is a very thin near-boundary row:

| Row | Pair | Geometry | M224 normal margin | M233 normal margin |
| ---: | --- | --- | ---: | ---: |
| 16 | 9530:6:9550:6 | x=13.878356, y=0.190667, half_width=0.728162 | 0.000106 | -0.000169 |

M233 turns that row from obstacle-completed to collision, so the old replay
proof surface is not retained.

## Behavior Diagnostic

M233 retains broad behavior on the two public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m224_10063 | 0.8625 | 0.1375 | 1.835461 |
| 9505 | m233_5220 | 0.8625 | 0.1375 | 1.835257 |
| 9505 | m233_5220_reset | 0.8500 | 0.1500 | 1.833939 |
| 9505 | m233_5220_zero_all | 0.8000 | 0.2000 | 1.853231 |
| 9506 | m224_10063 | 0.8625 | 0.1375 | 1.852989 |
| 9506 | m233_5220 | 0.8625 | 0.1375 | 1.852770 |
| 9506 | m233_5220_reset | 0.8500 | 0.1500 | 1.850207 |
| 9506 | m233_5220_zero_all | 0.8000 | 0.2000 | 1.871139 |

This is not broad behavior collapse.

## Protected Key

Artifact:

```text
runs/m233_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m224_10063 | 1 / 1 | true | 0.186385 | 0.086925 | 0.099460 |
| m229_5219 | 0 / 1 | false | 0.205200 | 0.106179 | 0.099021 |
| m233_5220 | 0 / 1 | false | 0.204645 | 0.104993 | 0.099652 |

M233 improves the protected-key normal margin slightly relative to M229, but it
still leaves the protected window:

```text
0.204645 > 0.2
```

## Diagnosis

M233 shows that adding the protected key to the snippet/action anchor is not
sufficient. The training-time snippet action anchor is nearly zero, so the
first-action anchor is being satisfied. The failure is closed-loop: small
policy or hidden-state changes after the anchored decision still move
near-boundary rollout margins outside the protected windows.

Failure taxonomy:

```text
proof_washout
protected_key_window_failure
promotion_gate_failure
```

## Decision

M233 is rejected.

Current best remains:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

Next step:

```text
m234-m233-closed-loop-retention-failure-audit
```

M234 should audit why first-action snippet anchoring is insufficient and decide
whether the next repair needs full rollout retention, multi-step action anchors,
or stricter PPO trust-region gating. Do not repeat or lengthen M233 before that
audit.
