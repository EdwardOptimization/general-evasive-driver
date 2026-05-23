# M397 M395 Alpha02 Old-Key Boundary Audit

M397 audits the first known boundary after the M395 promotion. It does not run
PPO, promote a checkpoint, lower thresholds, or change actor inputs.

## Boundary

Current public-gate base:

```text
runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
```

First known failing candidate:

```text
runs/m394_s02_micro_interpolation/checkpoints/alpha_0_2.pt
```

Failing compact old-key case:

```text
9958|perturbed|39|36|9.500000|-1.200000|0.900000
```

Formal gate:

```text
runs/m396_s02a020_old_key_replay_gate
```

## Alpha 0.1 vs Alpha 0.2

| Candidate | Accepted rows | Normal success | Active normal margin | Active wrong-history margin | Active gap delta |
| --- | ---: | --- | ---: | ---: | ---: |
| M395 selected, alpha 0.1 | 40 / 40 | true | +0.000086 | -0.002055 | +0.000002 |
| alpha 0.2 | 39 / 40 | false | -0.000089 | -0.002232 | +0.000005 |

The active row does not lose wrong-history separation. The wrong-history branch
stays collision-side and the margin gap slightly improves. The failure is
normal-branch terminal-margin sign crossing.

## Larger Alpha Check

At alpha `0.4`, the old-key compact failure broadens:

```text
runs/m397_s02a040_old_key_replay_gate
```

| Metric | Value |
| --- | ---: |
| accepted regressions | 2 |
| normal-success regressions | 2 |
| candidate gap p10 | -0.000361449 |
| candidate gap min | -0.000584687 |

Failing / stressed rows:

| Case | Accepted | Normal success | Normal margin | Wrong-history margin | Gap delta |
| --- | --- | --- | ---: | ---: | ---: |
| 10004\|perturbed\|31\|31\|9.500000\|-1.000000\|0.800000 | false | false | -0.000133 | -0.000933 | +0.000001 |
| 9958\|perturbed\|39\|36\|9.500000\|-1.200000\|0.900000 | false | false | -0.000439 | -0.002587 | +0.000009 |
| 10033\|perturbed\|29\|23\|9.500000\|-1.200000\|0.700000 | true | true | +0.033792 | +0.012717 | -0.000585 |

This means the alpha `0.2` failure is initially a one-row boundary, but the
same direction starts stressing a small old-key normal-margin family as alpha
increases. It should not be treated as a stale singleton veto.

## Classification

The current blocker is:

```text
old_key_normal_branch_terminal_margin_cliff
```

It is not:

```text
wrong_history_sensitivity_loss
gap_distribution_erosion
actor_input_contract_issue
PPO_instability
```

## Decision

The next task should export training-only local recovery targets for the
current old-key normal-branch boundary rows. The target should improve normal
branch margin while keeping wrong-history history anchored, and closed-loop
old-key replay must remain the outer gate.

Admit:

```text
m398-old-key-normal-margin-recovery-target-export
```

Decision:

```text
admit_m398_old_key_normal_margin_recovery_target_export
```
