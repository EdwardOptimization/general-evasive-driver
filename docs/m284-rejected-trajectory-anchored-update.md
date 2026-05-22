# M284 Rejected-Trajectory-Anchored Update

M284 runs one small no-PPO actor update using the M283 combined
recovery/rejected trajectory anchor.

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

Trajectory anchor:

```text
runs/m283_current_family_rejected_trajectory_anchor/combined_recovery_rejected_anchor.npz
```

M284 uses preferred-only snippet action anchoring again; rejected-history
retention is handled by the M283 trajectory anchor.

## Actor Update

Run directory:

```text
runs/m284_m272_actor_coupling_m270_rejected_trajectory_anchor_s10_lr5e5_seed10078
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

The objective improved:

| Metric | Before | After |
| --- | ---: | ---: |
| optimizer sampled loss | 0.680839 | 0.676221 |
| fixed sampled loss, seed37 | 0.681539 | 0.676860 |
| exact loss | 0.681376 | 0.676685 |
| trajectory anchor MSE | 0.000001398 | 0.000015717 |

## First Gates

M284 solves the M267/M264 current-family wrong-history washout:

| Surface | Baseline success drops | M284 success drops | Normal success | Gate pass |
| --- | ---: | ---: | ---: | --- |
| M267/M264 | 17 / 17 | 17 / 17 | 1.000000 | true |

But the rejected trajectory anchor is too strong for old M183/M170 normal
behavior:

| Surface | Baseline normal success | M284 normal success | Baseline drops | M284 drops | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M170 | 1.000000 | 0.176471 | 17 / 17 | 3 / 17 | false |

M183/M170 row16 fails normal success:

| Policy | Normal success | Success drop | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | --- | ---: | ---: | ---: |
| `m272b_a0_01025` | true | true | 0.000000636 | -0.005949 | 0.005950 |
| `m284_10078` | false | false | -0.001808 | -0.007818 | 0.006010 |

Protected-key and behavior gates were skipped because M183/M170 already failed.

## Interpretation

M284 is directionally useful but over-weighted. Compared with M279/M281:

- M279/M281 preserved or repaired M183/M170 row16 but failed M267/M264.
- M284 preserves M267/M264 perfectly but destroys M183/M170 normal success.

This indicates a balance problem, not a dead end. The M284 update direction
contains useful current-family wrong-history retention, but the raw step is too
large or the rejected trajectory anchor is too dominant.

The next cheapest test is no-training interpolation from M272 toward M284. If a
small alpha preserves both M183/M170 and M267/M264 while improving exact M270
loss, that gives a safe base or a better trust-region target. If no alpha works,
then the repair needs lower rejected-repeat/weight or a source-balanced
trajectory anchor.

## Decision

Reject raw M284 as a promotable driver checkpoint.

Failure types:

```text
proof_washout
objective_overfit
```

Decision:

```text
reject_rejected_trajectory_raw_update_old_surface_washout
```

Next step:

```text
m285-m284-interpolation-balance-probe
```

M285 should run no-training interpolation from M272 to M284 and gate M183/M170
and M267/M264 before any broader replay or PPO.
