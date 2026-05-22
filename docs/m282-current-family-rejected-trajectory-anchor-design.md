# M282 Current-Family Rejected-Trajectory Anchor Design

M282 designs the next repair after M281 showed that one-step rejected-hidden
action anchoring does not preserve closed-loop wrong-history failure.

No PPO, actor update, promotion, or actor-input change was performed.

## Failure Mechanism

M279 and M281 both repair the original M183/M170 row16 terminal-margin cliff,
but both fail M267/M264 current-family wrong-history retention:

| Candidate | Exact M270 loss | Row16 margin | M267/M264 success drops | Gate |
| --- | ---: | ---: | ---: | --- |
| `m272b_a0_01025` | 0.681376 | 0.000000636 | 17 / 17 | baseline |
| `m279_10076` | 0.677437 | 0.002459 | 12 / 17 | fail |
| `m281_10077` | 0.678091 | 0.002633 | 11 / 17 | fail |

M281 included rejected-hidden one-step action anchors, but wrong-history
rollouts still became safe over the continuation. That means the issue is not
only the first action mean; it is the closed-loop rejected-history trajectory.

## Design Goal

The next constraint should preserve the current base's wrong-history rollout
behavior on M267/M264 while still allowing normal-history recovery.

Target behavior:

```text
normal/current history:
  allow M278 recovery and better terminal margin

wrong/rejected history:
  preserve M272 wrong-history action trajectory on current-family rows
  so success-drop evidence remains causal and source-local
```

This is a training-time proof anchor. It does not add privileged actor inputs
and does not deploy wrong-history behavior.

## Anchor Contract

M283 should export a `TrajectoryActionAnchor`-compatible NPZ for rejected
history on M267/M264.

For each selected M267/M264 row:

1. Reconstruct the current M272 left snapshot.
2. Reconstruct the current M272 right hidden state for the matched wrong
   history.
3. Relocate the left snapshot obstacle to the registered boundary geometry.
4. Start the continuation from:

```text
observation = relocated left human-view observation
hidden      = current M272 right/wrong-history hidden
```

5. Roll out the M272 actor under that rejected hidden branch.
6. At every continuation step, record:

```text
observation before action
hidden before action
reference_action = M272 rejected-history action
source_index
step_index
weight
```

The exported rows must use current M272 observations and hidden states only.
They must not use old checkpoint hidden states or hidden vehicle parameters.

## Row Selection

Use the full M267/M264 replay corpus first:

```text
runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
```

The six rows that failed in M281 must be included:

```text
4, 6, 11, 13, 15, 16
```

Prefer exporting all 17 rows so the update does not overfit only the currently
failed subset.

## Combined Training Anchor

M283 should create two artifacts:

```text
rejected_trajectory_anchor.npz
combined_recovery_rejected_anchor.npz
```

The combined anchor should append the rejected-history trajectory rows to the
existing M279 normal retention/recovery anchor:

```text
runs/m279_combined_retention_recovery_anchor/combined_trajectory_anchor.npz
```

Because M267/M264 is the current blocker, M283 may repeat or upweight rejected
trajectory rows, but this must be declared in the export summary. A conservative
first setting is:

```text
rejected_repeat = 16
max_continuation_steps = 60
```

## Gate Order For Next Update

The first actor update using this anchor must be no-PPO and must gate in this
order:

1. fixed sampled and exact M270 objective;
2. M183/M170 row16;
3. M267/M264 success-drop retention;
4. remaining replay surfaces;
5. protected key;
6. behavior seeds 9505 and 9506.

If M267/M264 still fails, reject the update and audit source-aware contrast or
terminal-outcome pairwise loss. Do not run PPO.

## Decision

M282 completes the design.

Decision:

```text
implement_current_family_rejected_trajectory_anchor_export
```

Next step:

```text
m283-current-family-rejected-trajectory-anchor-export
```
