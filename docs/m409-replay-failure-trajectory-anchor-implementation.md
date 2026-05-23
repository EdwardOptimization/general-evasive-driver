# M409 Replay-Failure Trajectory Anchor Implementation

M409 implements the first replay-failure trajectory-anchor path for exact
projection. It does not run PPO, promote a checkpoint, lower thresholds, or
change actor inputs.

## Code Changes

`exact_post_ppo_repair` now accepts an optional replay trajectory anchor:

```text
--replay-trajectory-anchor-npz
--lambda-replay-trajectory-anchor
```

The anchor is loaded through the existing
`load_trajectory_action_anchor` contract and evaluated with a deterministic
full-batch exact loss:

```text
exact_trajectory_action_anchor_loss
```

This loss is a secondary projection residual. It is not part of the exact
lexicographic pass, and it does not replace closed-loop replay gates.

## M267/M264 Anchor Export

M409 reuses the existing current-family rejected-history trajectory exporter on
the M407 M267/M264 failed rows.

Run directory:

```text
runs/m409_m407_m267_replay_failure_trajectory_anchor
```

Input failed row ids:

```text
0,1,2,4,5,6,7,8,9,10,11,12,13,14,15,16
```

The exporter selected the full 17-row M267/M264 corpus, with all 16 required
failed rows present.

| Metric | Value |
| --- | ---: |
| rows selected | `17` |
| rejected trajectory rows | `669` |
| required rows present | `true` |
| rejected anchor shape | `669 x 72`, `669 x 128`, `669 x 3` |
| combined anchor rows | `2559` |

Primary artifact for exact repair:

```text
runs/m409_m407_m267_replay_failure_trajectory_anchor/rejected_trajectory_anchor.npz
```

## No-Update Smoke

No-update exact repair smoke:

```text
runs/m409_replay_trajectory_anchor_no_update_smoke
```

Key result:

| Metric | Value |
| --- | ---: |
| replay trajectory anchor rows | `669` |
| replay trajectory anchor loss | `5.700356e-15` |
| exact M297 delta | `0.0` |
| exact M270 delta | `0.0` |
| old-key surrogate delta | `0.0` |
| exact lexicographic pass | `true` |

The near-zero trajectory loss is expected because the no-update smoke uses the
same M400 base checkpoint that generated the reference trajectory.

## Tests

Focused tests:

```text
tests/test_exact_post_ppo_repair.py
tests/test_intervention_objectives.py
tests/test_rejected_history_trajectory_anchor.py
```

Result:

```text
27 passed
```

## Old-Key Status

Old-key replay-failure trajectory export is explicitly deferred. The existing
trajectory exporter operates on boundary-outcome corpus rows; old-key compact
rows have a different replay shape. M409 therefore only proves the generic
exact-repair loading path and the current-family M267/M264 export path.

The old-key side still matters because M407 found:

```text
6 wrong-history-safe old-key regressions
1 old-key normal-branch failure
```

The next milestone should implement the old-key-specific replay-failure anchor
export before a full replay-aware projection probe.

## Decision

Admit:

```text
m410-old-key-replay-failure-anchor-implementation
```
