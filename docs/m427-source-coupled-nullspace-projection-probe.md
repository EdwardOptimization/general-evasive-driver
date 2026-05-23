# M427 Source-Coupled Nullspace Projection Probe

M427 runs the first no-PPO exact projection with projected recovery gradients
enabled. It does not run PPO, promote a checkpoint, lower thresholds, or change
actor inputs.

## Projection

Run directory:

```text
runs/m427_projected_recovery_ltraj1e13_s40_seed10156
```

Candidate:

```text
runs/m427_projected_recovery_ltraj1e13_s40_seed10156/candidate_checkpoint.pt
```

Exact metrics:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs base | `-0.000010252` |
| exact M270 delta vs base | `-0.000080943` |
| old-key surrogate delta vs base | `-0.000388145` |
| exact lexicographic pass | `true` |
| hard-guard trajectory loss | `2.107883e-09` |
| recovery retained vs M406 | `0.174354` |

This improves recovery retention beyond M423 `mixed_b` (`0.133154`) but remains
below the primary `0.20` target.

Projection diagnostics near the selected endpoint:

| Step | Conflicts | Retained gradient norm ratio | Recovery preferred loss |
| ---: | ---: | ---: | ---: |
| `38` | `4` | `0.139359` | `0.003703812` |
| `39` | `3` | `0.157972` | `0.003698657` |
| `40` | `3` | `0.169457` | `0.003692045` |

The projection is active and utility movement is not just the old scalar
objective repeating M423.

## Proof Gates

M267/M264 first replay passes:

```text
runs/m427_projected_m267_m264_first_replay
```

| Gate | Result |
| --- | ---: |
| normal success rate | `1.0` |
| wrong-history success rate | `0.0` |
| success drops | `17 / 17` |
| gate pass | `true` |

Old-key compact replay fails:

```text
runs/m427_projected_old_key_targeted_replay
runs/m427_projected_old_key_replay_gate
```

| Metric | Value |
| --- | ---: |
| accepted cases | `36 / 40` |
| normal-success cases | `38 / 40` |
| policy pass | `false` |

Failed old-key rows:

| Key | Normal success | Normal margin | Wrong-history margin | Mechanism |
| --- | --- | ---: | ---: | --- |
| `10004|perturbed|31|31` | true | `0.001654052` | `0.000953258` | wrong-history branch became safe |
| `10023|perturbed|12|12` | true | `0.048193868` | `0.046255871` | gap erosion on guard row |
| `9872|perturbed|21|18` | false | `-0.000458062` | `-0.007648332` | normal-branch collision |
| `9872|perturbed|21|18` | false | `-0.000753041` | `-0.008037479` | normal-branch collision |

M183/M170 was not run because old-key compact replay failed first.

## Interpretation

The projected recovery direction is useful but the hard guard set is incomplete:

- M267 rows `6` and `15` are preserved, so projection fixed the M423 `mixed_c`
  current-family washout.
- Excluding `10004` entirely from the hard guard lets the wrong-history branch
  become safe. This row needs a branch split: allow normal-history recovery,
  but keep rejected-history behavior guarded.
- Old-key `9872` was not in the hard guard and now fails by normal-branch
  collision. It needs a normal-branch hard guard if this direction is pursued.
- Old-key `10023` remains a guard row but still loses gap, so branch-specific
  old-key guard reporting is needed before another projection.

This is not a candidate for promotion, but it is positive partial evidence for
the projected-recovery idea: utility improves and M267 proof survives.

## Decision

Reject the M427 candidate and audit branch-specific old-key guard design:

```text
m428-old-key-branch-split-guard-audit
```
