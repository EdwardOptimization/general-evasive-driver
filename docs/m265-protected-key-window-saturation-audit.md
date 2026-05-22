# M265 Protected-Key Window Saturation Audit

M265 audits the protected-key normal-margin window after M264. No PPO, no
projection, and no actor-input change was performed.

## Question

The recent milestones keep passing broad replay and behavior gates, but the
selected interpolation alpha keeps shrinking because the protected key
`9944|perturbed|28|28` is near the `0.2` normal-margin window.

M265 asks whether more PPO is admissible, or whether the next step must refresh
the protected surface before continuing.

## Protected-Key Margin Trajectory

The protected-key normal margin has been pushed steadily toward the boundary:

| Policy | Protected pass | Normal margin | Slack to 0.2 | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: | ---: |
| m253_a0_00008 | true | 0.195820 | 0.004180 | 0.095022 | 0.100799 |
| m258_a010 | true | 0.195973 | 0.004027 | 0.095118 | 0.100855 |
| m259_a010 | true | 0.196134 | 0.003866 | 0.095254 | 0.100880 |
| m260_a050 | true | 0.199550 | 0.000450 | 0.098920 | 0.100630 |
| m261_a001 | true | 0.199615 | 0.000385 | 0.098992 | 0.100624 |
| m263_a005 | true | 0.199909 | 0.000091 | 0.099300 | 0.100609 |
| m264_a001 | true | 0.199971 | 0.000029 | 0.099368 | 0.100604 |

Known nearby failures:

| Policy | Protected pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m260_a100 | false | 0.202650 | 0.102579 | 0.100071 |
| m263_a010 | false | 0.200200 | 0.099606 | 0.100594 |
| m264_a0_0025 | false | 0.200065 | 0.099470 | 0.100595 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

The wrong-history gap remains large. The failure mechanism is not loss of
history dependence. It is normal-history margin leaving the near-boundary
window.

## Source Improvement Versus Slack

The exact-source objective is still moving in the desired direction:

| Milestone | Raw / repaired source result | Selected alpha | Protected slack after selection |
| --- | --- | ---: | ---: |
| M260 | raw improves M223 and protected-key sources | 0.050 | 0.000450 |
| M261 | raw improves M223 but regresses protected-key source | 0.001 | 0.000385 |
| M263 | projection repairs M261 raw protected-key source | 0.005 | 0.000091 |
| M264 | raw improves M223 and protected-key sources | 0.001 | 0.000029 |

M264 is important because exact source is not the blocker. The raw update has:

```text
M223 source delta = -0.000364444
protected-key source delta = -0.000000644
```

Yet `alpha=0.0025` already fails protected-key replay because normal margin is
`0.200065`.

## Replay And Behavior Are Not The Blocker

The latest promoted checkpoints retain the public replay surfaces and behavior
seeds. For M264:

| Corpus | Rows | Success drops retained | Gate pass |
| --- | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | true |
| M183 M170 | 17 | 17 / 17 | true |
| M193 M189 | 14 | 14 / 14 | true |
| M212 M204 | 17 | 17 / 17 | true |
| M223 M219 | 17 | 17 / 17 | true |

Behavior remains:

```text
success = 0.8625
reset success = 0.8500
zero-all success = 0.8000
```

Therefore continuing the same PPO loop would mostly optimize around one
saturated protected key rather than produce stronger simulation evidence.

## Failure Classification

M265 classifies the current blocker as:

```text
protected_key_window_failure
```

This is not a reason to loosen the old key. The old key remains valuable as a
regression diagnostic. But it is no longer enough as the only protected surface
for deciding PPO continuation.

## Decision

Do not run another PPO continuation yet.

Refresh the current-family protected surface around the M263/M264 family before
more PPO:

```text
m266-m264-family-protected-surface-refresh
```

The refresh should look for multiple current-family protected rows and should
record whether the old single-key failure is representative or just one
over-saturated local boundary. Only after that should the project decide
whether to add a stronger window-aware anchor, convert a refreshed surface into
objective/replay gates, or admit another repaired PPO repeat.
