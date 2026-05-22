# M279 Recovery-Anchored Actor Update

M279 runs one small no-PPO actor-coupling update from `m272b_a0_01025` using
the M270 objective plus terminal-margin retention/recovery anchors.

No PPO, repeat seed, promotion, or actor-input change was performed.

## Setup

Initial checkpoint:

```text
runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
```

Objective corpus:

```text
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
```

Retention anchor:

```text
runs/m275_terminal_margin_retention_surface/retention_trajectory_anchor.npz
```

Recovery anchor:

```text
runs/m278_terminal_margin_recovery_anchor_probe/recovery_anchor.npz
```

## Combined Anchor

M275 retention and M278 recovery conflict at recovered rows' first step: M275
preserves the current near-cliff action, while M278 provides a safer current-
hidden action target. M279 therefore builds a combined anchor:

```text
runs/m279_combined_retention_recovery_anchor/combined_trajectory_anchor.npz
```

Construction:

```text
drop M275 rows where source_index is recovered and step_index == 0
append M278 recovery rows repeated 16 times
```

Combined-anchor summary:

| Metric | Value |
| --- | ---: |
| retention input rows | 1440 |
| recovery input rows | 30 |
| retention step0 rows replaced | 30 |
| recovery repeat | 16 |
| combined rows | 1890 |
| observation shape | 1890 x 72 |
| hidden shape | 1890 x 128 |
| reference action shape | 1890 x 3 |
| weight min | 1.011909 |
| weight max | 50.000000 |
| weight mean | 3.474452 |

## Actor Update

Run directory:

```text
runs/m279_m272_actor_coupling_m270_retention_recovery_anchor_s10_lr5e5_seed10076
```

Recipe:

```text
steps = 10
learning_rate = 0.00005
train_scope = actor_coupling
action_anchor_coef = 100
snippet_action_anchor_coef = 100
trajectory_action_anchor_coef = 100
trajectory_action_anchor_batch_size = 64
```

The sampled optimizer objective improved:

| Metric | Before | After |
| --- | ---: | ---: |
| optimizer sampled loss | 0.680839 | 0.676945 |
| combined trajectory anchor MSE | 0.000057008 | 0.000045268 |

Fixed and exact M270 eval also improved:

| Eval | M272 | M279 |
| --- | ---: | ---: |
| fixed sampled loss, seed37 | 0.681539 | 0.677615 |
| exact loss | 0.681376 | 0.677437 |

## Replay Gates

M279 passes the old/intermediate replay surfaces and the M183/M170 row16 gate,
but fails the refreshed current-family M267/M264 surface.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.002011 | +0.000339 | true |
| M183/M170 | 17 | 17 / 17 | +0.002037 | +0.000333 | true |
| M193/M189 | 14 | 14 / 14 | +0.001924 | +0.000247 | true |
| M212/M204 | 17 | 17 / 17 | +0.001903 | +0.000242 | true |
| M223/M219 | 17 | 17 / 17 | +0.001903 | +0.000242 | true |
| M267/M264 | 17 | 12 / 17 | +0.001903 | +0.000242 | false |

Artifacts:

- `runs/m279_m183_m168_replay_gate_seed9510`
- `runs/m279_m183_m170_replay_gate_seed9510`
- `runs/m279_m193_m189_replay_gate_seed9630`
- `runs/m279_m212_m204_replay_gate_seed10040`
- `runs/m279_m223_m219_replay_gate_seed10060`
- `runs/m279_m267_m264_replay_gate_seed10070`

## Row16 Result

M183/M170 row16, which blocked M276, is repaired:

| Policy | Normal success | Success drop | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | --- | ---: | ---: | ---: |
| `m272b_a0_01025` | true | true | 0.000000636 | -0.005949 | 0.005950 |
| `m279_10076` | true | true | 0.002459 | -0.003719 | 0.006178 |

This confirms that the recovery anchor fixed the original row16 terminal-margin
cliff.

## Failure Rows

The M267/M264 failure is not a normal-success failure. Normal margins improve,
but wrong-history rollouts also become successful on five current-family rows.

| Row | Physical pair | Candidate normal margin | Candidate wrong margin | Candidate margin gap |
| ---: | --- | ---: | ---: | ---: |
| 6 | 9530:15:9550:18 | 0.012112 | 0.001106 | 0.011005 |
| 11 | 9537:24:9561:24 | 0.008072 | 0.000462 | 0.007609 |
| 13 | 9530:9:9550:9 | 0.007080 | 0.000229 | 0.006851 |
| 15 | 9530:21:9550:21 | 0.006898 | 0.000736 | 0.006162 |
| 16 | 9530:6:9550:6 | 0.006893 | 0.000705 | 0.006188 |

The update improves broad terminal margin but weakens current-family
wrong-history success-drop evidence. This is still a proof washout, even though
the exact M270 objective and most replay surfaces improve.

Because M267/M264 failed, protected-key and behavior-retention gates were not
run for M279.

## Decision

Reject M279 as a promotable driver checkpoint.

Failure types:

```text
proof_washout
objective_overfit
```

Decision:

```text
reject_recovery_anchored_actor_update_current_family_washout
```

Next step:

```text
m280-current-family-wrong-history-washout-audit
```

M280 should audit why the recovery-anchored update makes current-family
wrong-history rollouts safe and design a rejected-hidden or source-aware
contrast repair before any new actor update. PPO remains blocked.
