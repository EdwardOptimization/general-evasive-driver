# M237 Trajectory-Anchored PPO Smoke From M224

M237 runs exactly one 1024-step PPO smoke from M224 with the combined M232
snippet anchor and the M235 closed-loop trajectory action anchor. This tests
whether multi-step action anchoring can repair the M233 closed-loop proof
washout.

Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

Config:

```text
configs/ppo_m237_trajectory_anchor_from_m224_smoke.json
```

Anchors:

```text
runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz
runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
```

The M235 trajectory anchor contains 97 M224 trajectory rows:

| Source | Rows |
| --- | ---: |
| M183 M170 row 16 | 57 |
| Protected key `9944|perturbed|28|28` | 40 |

## Training

Artifact:

```text
runs/ppo_m237_trajectory_anchor_from_m224_seed5221/checkpoint.pt
```

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Built-in eval termination | Outcome loss | Baseline anchor loss | Snippet anchor loss | Trajectory anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 77.575 | 1.043 | 10 | 0.2000 | 0.240428 | 0.00000670 | 0.000000027 | 0.000000134 |

The trajectory anchor path was active:

```text
loaded_trajectory_action_anchor=... snapshot=runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz rows=97
```

## Fixed Objective

M237 slightly improves both fixed losses.

Combined M232 objective:

| Policy | Loss |
| --- | ---: |
| m224_10063 | 0.246506 |
| m233_5220 | 0.246524 |
| m237_5221 | 0.246479 |

Original M223 objective:

| Policy | Loss |
| --- | ---: |
| m224_10063 | 0.209824 |
| m233_5220 | 0.209825 |
| m237_5221 | 0.209789 |

This is a positive objective signal, but M237 is governed by proof retention
gates, not objective loss alone.

## Replay Gates

Replay gates compare M237 against M224.

| Corpus | Rows | M237 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | -0.000041 | 0.000105 | true |
| M183 M170 | 17 | 16 / 17 | -0.000050 | 0.000106 | false |
| M193 M189 | 14 | 14 / 14 | -0.000061 | 0.000208 | true |
| M212 M204 | 17 | 17 / 17 | -0.000073 | 0.000199 | true |
| M223 M219 | 17 | 17 / 17 | -0.000073 | 0.000199 | true |

The same fragile M183 M170 row still fails:

| Row | Pair | Geometry | M224 normal margin | M237 normal margin |
| ---: | --- | --- | ---: | ---: |
| 16 | 9530:6:9550:6 | x=13.878356, y=0.190667, half_width=0.728162 | 0.000106 | -0.000084 |

M237 improves this row relative to M233's `-0.000169`, but it still turns the
row from obstacle-completed to collision. The M183 M170 proof surface is
therefore not retained.

## Behavior Diagnostic

M237 retains broad behavior on the two public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m224_10063 | 0.8625 | 0.1375 | 1.835461 |
| 9505 | m237_5221 | 0.8625 | 0.1375 | 1.835257 |
| 9505 | m237_5221_reset | 0.8500 | 0.1500 | 1.833886 |
| 9505 | m237_5221_zero_all | 0.8000 | 0.2000 | 1.853149 |
| 9506 | m224_10063 | 0.8625 | 0.1375 | 1.852989 |
| 9506 | m237_5221 | 0.8625 | 0.1375 | 1.852764 |
| 9506 | m237_5221_reset | 0.8500 | 0.1500 | 1.850153 |
| 9506 | m237_5221_zero_all | 0.8000 | 0.2000 | 1.871050 |

This is not broad behavior collapse.

## Protected Key

Artifact:

```text
runs/m237_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m224_10063 | 1 / 1 | true | 0.186385 | 0.086925 | 0.099460 |
| m233_5220 | 0 / 1 | false | 0.204645 | 0.104993 | 0.099652 |
| m237_5221 | 0 / 1 | false | 0.204386 | 0.104743 | 0.099643 |

M237 slightly improves the protected-key normal margin relative to M233, but it
still leaves the protected window:

```text
0.204386 > 0.2
```

## Diagnosis

Trajectory anchoring helped numerically but did not repair the closed-loop proof
washout. The training-time trajectory anchor loss is near zero, so the saved
teacher-forced trajectory states are being matched. The remaining failure is
that teacher-forced action matching does not constrain the actual on-policy
closed-loop state distribution tightly enough for near-boundary rows.

Failure taxonomy:

```text
proof_washout
protected_key_window_failure
promotion_gate_failure
```

## Decision

M237 is rejected.

Current best remains:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

Next step:

```text
m238-trajectory-anchor-retention-failure-audit
```

M238 should audit whether the next repair needs stronger trajectory-anchor
weighting, full hidden/state rollout anchoring, KL or trust-region tightening,
or a different PPO update structure. Do not repeat or lengthen M237 before that
audit.
