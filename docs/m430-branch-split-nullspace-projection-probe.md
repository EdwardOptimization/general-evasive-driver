# M430 Branch-Split Nullspace Projection Probe

M430 tests the M429 branch-split old-key guard in the projected recovery
path. It does not run PPO, promote a checkpoint, lower thresholds, or change
actor inputs.

## Projection

Run directory:

```text
runs/m430_branch_split_projected_ltraj1e13_s40_seed10157
```

Candidate:

```text
runs/m430_branch_split_projected_ltraj1e13_s40_seed10157/candidate_checkpoint.pt
```

Exact metrics:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs base | `-0.000035524` |
| exact M270 delta vs base | `-0.000070035` |
| old-key surrogate delta vs base | `-0.000482082` |
| exact lexicographic pass | `true` |
| branch-split trajectory-anchor loss | `2.546580e-09` |
| recovery preferred loss | `0.003809374` |
| recovery retained vs M406 | `0.061702` |

The branch-split guard restores exact feasibility and closed-loop proof, but it
also collapses most of the recovery movement. M427 retained `0.174354` of the
M406 recovery improvement, while M430 retains only `0.061702`.

Projection diagnostics at the selected endpoint:

| Metric | Value |
| --- | ---: |
| selected step | `40` |
| retained recovery-gradient norm ratio | `0.056439` |
| active hard gradients | `11` |
| projection conflict count | `8` |

The guard is active: it projects away most of the recovery gradient before the
optimizer step is applied.

## Proof Gates

M267/M264 first replay passes:

```text
runs/m430_branch_split_m267_m264_first_replay
```

| Gate | Result |
| --- | ---: |
| normal success rate | `1.0` |
| wrong-history success rate | `0.0` |
| success drops | `17 / 17` |
| normal margin mean delta | `-0.000366` |
| margin gap mean delta | `-0.000142` |
| gate pass | `true` |

Old-key compact replay passes:

```text
runs/m430_branch_split_old_key_targeted_replay
runs/m430_branch_split_old_key_replay_gate
```

| Gate | Result |
| --- | ---: |
| accepted cases | `40 / 40` |
| normal-success cases | `40 / 40` |
| margin gap mean | `0.008356` |
| margin gap min | `0.000807` |
| candidate gate pass | `true` |

M183/M170 first replay passes:

```text
runs/m430_branch_split_m183_m170_first_replay
```

| Gate | Result |
| --- | ---: |
| normal success rate | `1.0` |
| wrong-history success rate | `0.0` |
| success drops | `17 / 17` |
| normal margin mean delta | `-0.000407` |
| margin gap mean delta | `-0.000178` |
| gate pass | `true` |

## Interpretation

M430 resolves the proof failures found in M427:

- M267/M264 remains `17 / 17`, so the current-family wrong-history proof stays
  intact.
- Old-key compact returns to `40 / 40`, so the `10004`, `10023`, and `9872`
  branch-split additions cover the M427 old-key regressions.
- M183/M170 remains `17 / 17`, so the new branch-split guard does not wash out
  the older replay surface.

The cost is utility. The selected candidate is proof-safe but retention-heavy:
recovery retained vs M406 falls to `0.061702`, below the `0.20` primary target
and below M423 `mixed_b` (`0.133154`) and M427 (`0.174354`).

This means branch-split old-key hard guards are sufficient to restore proof, but
the current all-hard guard formulation overconstrains the projected recovery
direction.

## Decision

Reject the M430 candidate for promotion and do not use it as a new base.

Admit a utility-balance audit:

```text
m431-branch-split-utility-balance-audit
```

M431 should inspect which branch-split rows dominate the projection conflict
and whether source/branch-specific weights, radii, or soft/hard separation can
recover M427-level utility without reopening the M430 proof gates.
