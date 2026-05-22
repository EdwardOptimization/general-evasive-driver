# M262 Stage2 Repeat Fragility Audit

M262 audits the M260/M261 4096-step stage2 PPO repeats before any medium PPO.
No training, PPO, projection, or actor-input change was performed in this
milestone.

## Question

M260 and M261 both pass promotion after interpolation, but their safe update
sizes are very different:

```text
M260 selected alpha = 0.05
M261 selected alpha = 0.001
```

The audit asks whether this is caused by replay proof fragility, broad behavior
regression, protected-key boundary pressure, protected-source objective
movement, or training instability.

## Raw PPO Direction

Both raw PPO runs improve the M223 source. They differ on the protected-key
source:

| Milestone | Raw PPO seed | Aggregate delta | M223 source delta | Protected-key source delta | Raw exact-source decision |
| --- | ---: | ---: | ---: | ---: | --- |
| M260 | 5227 | -0.000383651261 | -0.000381718051 | -0.000001933210 | pass |
| M261 | 5228 | -0.000322598272 | -0.000329465772 | +0.000006867500 | fail |

M261 repeats the old PPO source conflict: broad M223 movement is favorable, but
the single protected-key source moves in the wrong direction.

## Interpolation Boundary

M260 is exact-source safe at much larger alpha than M261:

| Milestone | Candidate | Alpha | Aggregate delta | M223 source delta | Protected-key source delta | Limiting gate |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| M260 | m260_a050 | 0.05 | -0.000019769062 | -0.000019486752 | -0.000000282310 | protected-key replay window |
| M260 | m260_a100 | 0.10 | -0.000039438177 | -0.000038901174 | -0.000000537003 | protected-key replay window fail |
| M261 | m261_a001 | 0.001 | -0.000000312937 | -0.000000316006 | +0.000000003069 | exact-source safe |
| M261 | m261_a0_0025 | 0.0025 | -0.000000810867 | -0.000000829279 | +0.000000018412 | protected-source exact fail |

This shows two different constraints:

- M260 raw exact-source movement is favorable, but protected-key normal margin
  leaves the safe window at larger alpha.
- M261 raw protected-key source movement is unfavorable, so exact-source gating
  limits alpha before broader proof gates matter.

## Protected-Key Pressure

The protected key remains the main boundary:

| Policy | Accepted | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m259_a010 | true | 0.196134 | 0.095254 | 0.100880 |
| m260_a050 | true | 0.199550 | 0.098920 | 0.100630 |
| m260_a100 | false | 0.202650 | 0.102579 | 0.100071 |
| m261_a001 | true | 0.199615 | 0.098992 | 0.100624 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

M261 is still inside the window, but only barely:

```text
0.200000 - 0.199615 = 0.000385
```

The issue is not that wrong-history dependence disappeared. The margin gap is
still large. The issue is that the normal-history margin is being pushed above
the protected near-boundary window.

## Replay And Behavior

`m261_a001` passes all replay gates versus M260:

| Corpus | Rows | Success drops retained | Gate pass |
| --- | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | true |
| M183 M170 | 17 | 17 / 17 | true |
| M193 M189 | 14 | 14 / 14 | true |
| M212 M204 | 17 | 17 / 17 | true |
| M223 M219 | 17 | 17 / 17 | true |

Behavior retention is unchanged:

| Transition | Seed | Base success | Candidate success | Base margin | Candidate margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| M259 -> M260 | 9505 | 0.8625 | 0.8625 | 1.835358 | 1.835353 |
| M259 -> M260 | 9506 | 0.8625 | 0.8625 | 1.852876 | 1.852870 |
| M260 -> M261 | 9505 | 0.8625 | 0.8625 | 1.835353 | 1.835353 |
| M260 -> M261 | 9506 | 0.8625 | 0.8625 | 1.852870 | 1.852870 |

Therefore the safe-alpha collapse is not a broad behavior regression and not a
public replay collapse.

## Failure Classification

M262 classifies the blocker as:

```text
seed_fragility
protected_key_window_failure
```

The seed fragility is specific: stage2 PPO consistently improves M223, but the
protected-key source direction is not stable across seeds. The protected-key
window failure is also specific: safe candidates remain near the `0.2`
normal-margin boundary, and larger M260 alpha leaves the boundary even when
exact sources improve.

## Decision

Do not start medium PPO from M261 yet.

The next milestone should repair the M261 raw PPO checkpoint with the same
post-PPO trajectory-anchored projection discipline that made M258/M259 useful:

```text
m263-m261-raw-trajectory-projection-repair
```

The M263 test should be no-new-PPO. It should ask whether a protected-source
projection from `runs/ppo_m261_stage2_repeat_from_m260_seed5228/checkpoint.pt`,
anchored by the M235 trajectory surface, can admit a larger and more meaningful
interpolation than M261's `alpha=0.001` while preserving exact-source, row16,
protected-key, replay, and behavior gates.
