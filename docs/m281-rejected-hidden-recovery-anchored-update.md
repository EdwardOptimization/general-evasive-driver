# M281 Rejected-Hidden Recovery-Anchored Update

M281 repeats the M279-style no-PPO actor update, but enables snippet action
anchoring for both preferred and rejected hidden states.

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

Combined retention/recovery trajectory anchor:

```text
runs/m279_combined_retention_recovery_anchor/combined_trajectory_anchor.npz
```

Unlike M279, M281 does not pass:

```text
--snippet-action-anchor-preferred-only
```

so `snippet_action_anchor` includes rejected-hidden action targets.

## Actor Update

Run directory:

```text
runs/m281_m272_actor_coupling_m270_rejected_hidden_recovery_anchor_s10_lr5e5_seed10077
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
| optimizer sampled loss | 0.680839 | 0.677609 |

Fixed and exact M270 eval also improved:

| Eval | M272 | M281 |
| --- | ---: | ---: |
| fixed sampled loss, seed37 | 0.681539 | 0.678267 |
| exact loss | 0.681376 | 0.678091 |

## First Gates

M281 passes M183/M170, including the original row16 cliff:

| Policy | Normal success | Success drop | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | --- | ---: | ---: | ---: |
| `m272b_a0_01025` | true | true | 0.000000636 | -0.005949 | 0.005950 |
| `m281_10077` | true | true | 0.002633 | -0.003545 | 0.006178 |

But M281 fails M267/M264 more strongly than M279:

| Policy | M267/M264 success drops | Wrong-history success rate | Gate pass |
| --- | ---: | ---: | --- |
| `m272b_a0_01025` | 17 / 17 | 0.000000 | true |
| `m279_10076` | 12 / 17 | 0.294118 | false |
| `m281_10077` | 11 / 17 | 0.352941 | false |

M281 failed rows:

```text
4, 6, 11, 13, 15, 16
```

Protected-key and behavior gates were skipped because the M267/M264 proof gate
already failed.

## Interpretation

Rejected-hidden first-action anchoring is not enough. The M281 action update
still makes current-family wrong-history rollouts safe over the closed-loop
continuation. This suggests the next repair needs a trajectory-level
wrong-history retention/contrast surface, not just a one-step rejected-hidden
action anchor.

The next artifact should explicitly preserve rejected-history rollout behavior
on the M267/M264 current-family surface while allowing normal-history recovery.
That is a stronger and more targeted proof constraint than the generic snippet
action anchor used in M281.

## Decision

Reject M281 as a promotable driver checkpoint.

Failure types:

```text
proof_washout
objective_overfit
```

Decision:

```text
reject_rejected_hidden_action_anchor_update
```

Next step:

```text
m282-current-family-rejected-trajectory-anchor-design
```

M282 should design or export a current-family rejected-history trajectory anchor
before any further actor update. PPO remains blocked.
