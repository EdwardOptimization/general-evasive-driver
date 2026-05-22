# M280 Current-Family Wrong-History Washout Audit

M280 audits why M279 repairs terminal margin but fails the refreshed M267/M264
current-family replay surface.

No PPO, actor update, promotion, or actor-input change was performed.

## Starting Point

M279 improved the M270 objective and repaired the original M183/M170 row16
terminal-margin cliff:

```text
exact M270 loss:          0.681376 -> 0.677437
M183/M170 row16 margin:  0.000000636 -> 0.002459
```

But M279 failed M267/M264:

```text
baseline success drops:   17 / 17
M279 success drops:       12 / 17
```

Protected-key and behavior gates were correctly skipped.

## Failed Rows

The M267/M264 failure is caused by wrong-history rollouts becoming successful,
not by normal rollouts regressing.

| Row | Physical pair | Baseline wrong margin | M279 wrong margin | Wrong margin delta |
| ---: | --- | ---: | ---: | ---: |
| 6 | 9530:15:9550:18 | -0.000781 | 0.001106 | +0.001887 |
| 11 | 9537:24:9561:24 | -0.000704 | 0.000462 | +0.001166 |
| 13 | 9530:9:9550:9 | -0.001908 | 0.000229 | +0.002137 |
| 15 | 9530:21:9550:21 | -0.000961 | 0.000736 | +0.001697 |
| 16 | 9530:6:9550:6 | -0.001526 | 0.000705 | +0.002231 |

All five rows keep normal success. The proof loss is specifically that the
wrong-history branch no longer fails.

## Action Drift

On the failed rows, M279 moves wrong-history first actions in a consistent
safer direction: slightly less steer and more brake.

| Row | Wrong steer: base -> M279 | Wrong throttle: base -> M279 | Wrong brake: base -> M279 |
| ---: | ---: | ---: | ---: |
| 6 | 0.667639 -> 0.663820 | -0.024835 -> -0.022666 | 0.090386 -> 0.095535 |
| 11 | 0.622404 -> 0.619245 | 0.030752 -> 0.034718 | 0.079820 -> 0.084389 |
| 13 | 0.709721 -> 0.705947 | -0.147834 -> -0.146206 | 0.041924 -> 0.048740 |
| 15 | 0.660202 -> 0.656470 | -0.014336 -> -0.012266 | 0.091500 -> 0.096233 |
| 16 | 0.725072 -> 0.721786 | -0.198846 -> -0.198902 | 0.013935 -> 0.020560 |

This is exactly the wrong failure mode for self-ID proof: the update repairs
the normal branch but also makes the wrong-history branch recover.

## Snippet Anchor Finding

M279 used:

```text
--snippet-action-anchor-preferred-only
```

That anchors preferred/current hidden actions but does not anchor rejected or
wrong-history hidden actions.

A direct action-drift audit against the M272 base on the M270 snippet corpus
shows rejected hidden actions drift more than preferred hidden actions:

| Scope | Preferred action L2 mean | Preferred max | Rejected action L2 mean | Rejected max |
| --- | ---: | ---: | ---: | ---: |
| all M270 snippets | 0.005260 | 0.010613 | 0.007316 | 0.012039 |
| M267/M264 snippets | 0.005319 | 0.006638 | 0.007328 | 0.011967 |

For M267/M264, the largest rejected-hidden action drifts include added brake
and throttle changes. This matches the boundary replay failure rows where
wrong-history margins cross from negative to positive.

## Interpretation

M279 proves that current-hidden recovery anchors can repair the near-cliff
normal branch. It also proves that normal-branch recovery alone is insufficient:
the update can smooth the wrong-history branch into a safe behavior and erase
the current-family success-drop evidence.

The next repair should not loosen M267/M264. It should make the recovery update
source-aware:

```text
preserve or contrast rejected-hidden actions
keep M278 normal-branch recovery target
gate M267/M264 before protected-key or behavior gates
```

The simplest next experiment is to rerun the small M279-style actor update with
the existing rejected-hidden snippet action anchor enabled. In CLI terms, do
not pass:

```text
--snippet-action-anchor-preferred-only
```

This makes `build_snippet_action_anchor(... include_rejected_hidden=True)` keep
the M272 rejected-hidden action surface while the M278 recovery anchor repairs
normal fragile-row actions.

## Decision

M280 completes the audit.

Decision:

```text
admit_rejected_hidden_anchored_recovery_update
```

Next step:

```text
m281-rejected-hidden-recovery-anchored-update
```

M281 may run one small no-PPO actor-coupling update from M272 using the M279
combined retention/recovery anchor and rejected-hidden snippet action anchoring.
It must gate M183/M170 row16 and M267/M264 before broader proof gates.
