# M276 Terminal-Margin Anchored Actor Update

M276 runs one small actor-coupling update from `m272b_a0_01025` using the M270
source-balanced objective plus the M275 terminal-margin trajectory anchor.

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

Terminal-margin trajectory anchor:

```text
runs/m275_terminal_margin_retention_surface/retention_trajectory_anchor.npz
```

Recipe:

```text
steps = 10
learning_rate = 0.00005
train_scope = actor_coupling
action_anchor_coef = 100
snippet_action_anchor_coef = 100
trajectory_action_anchor_coef = 100
trajectory_action_anchor_batch_size = 32
```

## Actor Update

Artifact:

```text
runs/m276_m272_actor_coupling_m270_terminal_margin_anchor100_s10_lr5e5_seed10075/optimized_checkpoint.pt
```

The update improves the M270 objective:

| Metric | Before | After |
| --- | ---: | ---: |
| optimizer sampled loss | 0.680839 | 0.675900 |
| fixed sampled loss | 0.681592 | 0.676587 |
| exact loss | 0.681376 | 0.676400 |
| trajectory anchor MSE | ~0 | 0.000017532 |

## Row16 Gate

The raw update fails the first required proof gate.

| Policy | Row16 success | Success drop | Row16 normal margin | Wrong-history margin | Margin gap |
| --- | --- | --- | ---: | ---: | ---: |
| `m272b_a0_01025` | true | true | 0.000000636 | -0.005949 | 0.005950 |
| `m276_10075` | false | false | -0.002258 | -0.008289 | 0.006031 |

Full M183/M170 replay also fails:

```text
candidate normal success = 0.176471
candidate success drops = 3 / 17
gate pass = false
```

Since row16 fails, broader replay, protected-key, and behavior gates are not
run for the raw update.

## Interpolation Check

A no-training interpolation from M272 toward the rejected M276 update shows that
the useful trust region is still tiny.

| Policy | Alpha | Exact M270 loss | Row16 success | Row16 normal margin |
| --- | ---: | ---: | --- | ---: |
| `m272b_a0_01025` | 0.00000 | 0.681375623 | true | 0.000000636 |
| `m276i_a0_00005` | 0.00005 | 0.681375384 | true | 0.000000571 |
| `m276i_a0_0001` | 0.00010 | 0.681375146 | true | 0.000000436 |
| `m276i_a0_0002` | 0.00020 | 0.681374609 | true | 0.000000170 |
| `m276i_a0_0003` | 0.00030 | 0.681374192 | false | -0.000000022 |
| `m276i_a001` | 0.00100 | 0.681370735 | false | -0.000001663 |
| `m276i_a010` | 0.01000 | 0.681326628 | false | -0.000021981 |

The largest tested row16-safe interpolation is `alpha=0.0002`, with sampled
M270 loss:

```text
m272b_a0_01025 = 0.681591687
m276i_a0_0002 = 0.681590700
```

This is technically an objective improvement, but it is too small to solve the
learning problem and still leaves row16 with almost no margin.

## Interpretation

M276 shows that retention anchoring alone is insufficient. The M275 anchor
preserves the current near-cliff behavior, but the current behavior already has
only `6.36e-7` row16 margin. A useful update must first recover terminal-margin
slack or use a stronger current-hidden recovery target.

This is not a reason to run PPO. PPO remains blocked.

## Decision

Reject M276 as an update recipe.

Failure types:

```text
proof_washout
objective_overfit
```

Decision:

```text
reject_terminal_margin_retention_anchor_update
```

Next step:

```text
m277-terminal-margin-recovery-anchor-design
```

M277 should design a recovery anchor that uses current checkpoint hidden states
and safer action targets, rather than directly importing hidden states from old
source checkpoints.
