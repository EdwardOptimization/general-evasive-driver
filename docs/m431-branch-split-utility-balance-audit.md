# M431 Branch-Split Utility Balance Audit

M431 audits why M430 restored proof but collapsed recovery utility. It does not
run PPO, promote a checkpoint, lower thresholds, or change actor inputs.

## Audit Artifacts

Run directory:

```text
runs/m431_branch_split_utility_balance_audit
```

Generated files:

```text
runs/m431_branch_split_utility_balance_audit/policy_utility_summary.csv
runs/m431_branch_split_utility_balance_audit/trajectory_anchor_loss_by_source.csv
runs/m431_branch_split_utility_balance_audit/recovery_gradient_conflicts_by_source.csv
runs/m431_branch_split_utility_balance_audit/branch_split_source_summary.csv
runs/m431_branch_split_utility_balance_audit/summary.json
```

The audit uses the M429 branch-split hard guard and compares M400, M423,
M427, M430, M406, and M403 raw under the same M398 recovery objective.

## Utility Comparison

| Policy | Recovery preferred loss | Recovery retained vs M406 | Branch-split anchor loss |
| --- | ---: | ---: | ---: |
| M400 base | `0.003873638` | `0.000000` | `0.000000000` |
| M423 mixed_b | `0.003734955` | `0.133154` | `0.000000062` |
| M427 projected | `0.003692045` | `0.174354` | `0.000001262` |
| M430 projected | `0.003809374` | `0.061702` | `0.000000003` |
| M406 utility target | `0.002832120` | `1.000000` | `0.000065157` |

M430's branch-split anchor loss is nearly zero. That is proof-safe, but it
also means the new hard guard has pulled the candidate almost back to the base
trajectory surface before recovery can move.

## Dominant Source

M427 under the M429 branch-split guard:

| Source | Branch | Weighted loss | Max action distance | Radius | Recovery-gradient relation |
| --- | --- | ---: | ---: | ---: | --- |
| `10004|perturbed|31|31|9.5|-1.0|0.8` | wrong-history | `1.075796e-05` | `0.003843` | `0.000200` | conflict, cosine `-0.904241` |
| `9872|perturbed|21|18|12.5|-0.8|1.3` | normal | `6.782884e-07` | `0.001165` | `0.000200` | aligned, cosine `+0.934464` |
| `9872|perturbed|21|18|12.0|-1.2|1.2` | normal | `5.867425e-07` | `0.001136` | `0.000200` | aligned, cosine `+0.933484` |
| base hard guard source `4` | existing | `1.410074e-09` | `0.000270` | `0.000200` | conflict, cosine `-0.893468` |
| `10023|perturbed|12|12|11.0|-0.8|1.2` | wrong-history | `1.410074e-09` | `0.000270` | `0.000200` | conflict, cosine `-0.893468` |

The dominant source is `10004` wrong-history. It is both the largest M427
branch-split violation and a direct first-order conflict with recovery
descent. The `9872` normal-branch rows are not the main utility blocker:
their hard gradients are aligned with recovery, so recovery movement tends to
reduce their anchor loss rather than increase it.

## Interpretation

The M429 branch-split guard is semantically correct but mechanically too hard.
It anchors the full `10004` rejected-history trajectory to M400 with radius
`0.0002`. That exactly fixes the M427 proof failure, where `10004`
wrong-history became safe, but it also cuts away the same actor-coupling
direction that was producing most of the M427 recovery improvement.

The branch-specific conclusion is:

- keep `10004` wrong-history as a protected branch;
- do not keep it as an all-steps, all-hard, tiny-radius action anchor;
- leave `9872` normal-branch guards hard for now because they are not the
  primary recovery conflict;
- keep `10023` as a guard, but it is a secondary conflict compared with
  `10004`.

This is not evidence to run PPO. The blocker is still proof/utility residual
design.

## Next Experiment

Admit:

```text
m432-selective-10004-guard-design
```

M432 should design a no-PPO selective guard around `10004` wrong-history:

- sweep or export larger radii for `10004` wrong-history only, while keeping
  `10023`, `9872`, and base hard guards unchanged;
- prefer branch-specific hinge/radius control over lowering replay gates;
- require exact M297/M270/old-key no-regression, M267/M264 `17/17`,
  old-key compact `40/40`, and M183/M170 `17/17`;
- use recovery retained vs M406 as the utility gate, with `>= 0.20` as the
  primary target and M427 `0.174354` as the minimum useful comparison.
