# M140 Rollout Key Survival Audit

M140 follows M139's negative result. M139 showed that fixed retained-key action
anchoring can keep behavior and make retained action drift extremely small, but
strict rollout proof-surface diversity still falls below M133.

The goal of M140 is to identify which M133 keys are actually lost and whether
the loss is explained by rollout-level margin/selection effects rather than
fixed snippet logprob or fixed action MSE.

## Command

The audit joins M136 retained keys against M133 and M139 strict selected
`outcome_intervention_snippets.csv` files:

```text
runs/m133_zero_relvel_s60_strict_60ep_seed9900
runs/m133_zero_relvel_s60_strict_60ep_seed9920
runs/m139_s40_snip100_strict_60ep_seed9900
runs/m139_s40_snip100_strict_60ep_seed9920
runs/m139_s40_snip500_strict_60ep_seed9900
runs/m139_s40_snip500_strict_60ep_seed9920
runs/m139_s20_snip1000_strict_60ep_seed9900
runs/m139_s20_snip1000_strict_60ep_seed9920
```

Artifacts:

```text
runs/m140_rollout_key_survival_audit/key_survival_audit.csv
runs/m140_rollout_key_survival_audit/audit_summary.json
```

## Key Survival

M136 contains `11` unique M133 keys.

| candidate | retained unique keys | lost unique keys |
| --- | ---: | ---: |
| s40 snip100 | 9 | 2 |
| s40 snip500 | 10 | 1 |
| s20 snip1000 | 10 | 1 |

Lost keys:

| candidate | lost keys |
| --- | --- |
| s40 snip100 | `9942|perturbed|23|23`, `9944|perturbed|28|28` |
| s40 snip500 | `9944|perturbed|28|28` |
| s20 snip1000 | `9944|perturbed|28|28` |

The shared lost key is:

```text
seed=9944
source_condition=perturbed
source_step=28
paired_step=28
```

## Lost-Key Mechanism

The `9944` key is a near-threshold selected row in M133, not a high-margin row.

At miner seed `9900`, M133 accepts the relocated width `0.9` case:

| policy | half width | normal margin | wrong-history margin | margin gap | accepted |
| --- | ---: | ---: | ---: | ---: | --- |
| M133 s60 | 0.9 | 0.076748 | 0.071552 | 0.005196 | yes |

This barely clears the strict `min_margin_gap=0.005` threshold.

The conservative M139 candidate changes the same row to:

| policy | half width | normal margin | wrong-history margin | margin gap | accepted |
| --- | ---: | ---: | ---: | ---: | --- |
| s20 snip1000 | 0.9 | 0.075643 | 0.070968 | 0.004675 | no |

Wider obstacle cases have margin gaps above `0.005`, but their normal margins
are negative, so they are not accepted outcome-sensitive rows:

| policy | half width | normal margin | wrong-history margin | margin gap | accepted |
| --- | ---: | ---: | ---: | ---: | --- |
| s20 snip1000 | 1.0 | -0.023842 | -0.028936 | 0.005094 | no |
| s20 snip1000 | 1.1 | -0.123299 | -0.128580 | 0.005281 | no |

So the key disappears because a narrow rollout-margin threshold crossing moves
the only valid accepted row below `min_margin_gap`. This is not visible from
the fixed retained-key action MSE alone.

## Interpretation

M140 explains why M139 failed despite very small action drift:

- strict selected-key survival is threshold-discontinuous;
- a margin-gap decrease of about `0.00052` can remove a key;
- fixed action MSE near `2e-7` does not guarantee the accepted row remains
  accepted;
- the next repair should protect exact rollout-margin acceptance for critical
  near-threshold keys.

This also means that simply increasing snippet action-anchor coefficient is not
a good next step. It would mostly freeze M132 without creating a reliable repair
mechanism.

## Decision

Close M140 as a diagnostic positive.

The next step should be a critical-key exact replay guard:

```text
Given a candidate checkpoint,
replay the exact M133 critical relocated cases,
and reject if any protected key loses its accepted row.
```

This should run before expensive strict mining and before PPO continuation. It
is a guard, not a driver-success claim.
