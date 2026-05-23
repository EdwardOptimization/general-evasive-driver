# M412 Replay-Aware Projection Utility Audit

M412 audits whether the M411 proof-passing candidate is useful enough to chain
or whether it is primarily a retention-heavy projection back toward M400.

No PPO was run, no checkpoint was promoted, no thresholds were changed, and the
actor input/output contract was unchanged.

## Audited Policies

| Policy | Checkpoint |
| --- | --- |
| M400 base | `runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt` |
| M403 raw alpha `0.1` | `runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt` |
| M406 exact projection | `runs/m406_repair_from_alpha01_s40_seed10137/candidate_checkpoint.pt` |
| M411 lambda `1e13` | `runs/m411_combined_anchor_projection_ltraj1e13_s40_seed10144/candidate_checkpoint.pt` |

Audit artifact:

```text
runs/m412_replay_aware_projection_utility_audit
```

## Surface Metrics

Primary CSV:

```text
runs/m412_replay_aware_projection_utility_audit/policy_surface_metrics.csv
```

| Metric | M400 base | M406 projection | M411 lambda `1e13` |
| --- | ---: | ---: | ---: |
| parameter L2 to M400 | `0.000000` | `0.011096` | `0.003700` |
| combined replay-anchor MSE | `6.009236e-15` | `7.238024e-05` | `2.168418e-08` |
| combined replay-anchor L2 | `1.219995e-07` | `1.460897e-02` | `1.670792e-04` |
| old-key recovery preferred MSE | `0.003873638` | `0.002832120` | `0.003813047` |
| old-key recovery preferred L2 | `0.107800` | `0.092172` | `0.106953` |

Derived ratios:

| Ratio | Value |
| --- | ---: |
| M411 parameter L2 / M406 parameter L2 | `0.333494` |
| M411 replay-anchor MSE / M406 replay-anchor MSE | `0.000300` |
| M411 retained recovery improvement vs M406 | `0.058176` |

## Interpretation

M411 `lambda=1e13` is a valid proof-retention projection, but it is not a
useful driver-improvement candidate.

It repairs the M406 replay washout by almost fully returning the replay-failure
trajectory surface to M400 behavior:

```text
M411 replay-anchor MSE is only 0.03% of M406 replay-anchor MSE.
```

At the same time, it keeps only about `5.8%` of M406's recovery-target
improvement:

```text
M400 recovery MSE: 0.003873638
M406 recovery MSE: 0.002832120
M411 recovery MSE: 0.003813047
```

This explains why M411 passes proof gates: the strong trajectory residual has
mostly converted the projection into proof retention. That is useful evidence
for the residual's authority, but it should not be promoted or sent directly to
full public gate as driver progress.

## Decision

Reject M411 as a promotion candidate and admit residual-balance redesign:

```text
m413-replay-recovery-balance-design
```

The next design should avoid a single scalar trajectory-anchor coefficient that
forces a binary choice between M406-style recovery movement and M400-style
proof retention. It should instead separate active replay failures from already
safe rows, preserve recovery movement where replay is not threatened, and keep
closed-loop replay gates as the final authority.
