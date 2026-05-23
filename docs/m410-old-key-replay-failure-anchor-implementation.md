# M410 Old-Key Replay-Failure Anchor Implementation

M410 implements the old-key compact replay side of the replay-failure
trajectory-anchor path designed in M408 and started in M409. It does not run
PPO, promote a checkpoint, lower any gate threshold, or change the actor input
or output contract.

## Code Changes

New exporter:

```text
src/autodrift/old_key_replay_failure_trajectory_anchor.py
```

The exporter reads the M407 old-key accepted-regression rows, reconstructs the
source and paired hidden snapshots from the M341 old-key neighborhood manifest,
relocates the source obstacle to the failed compact replay case, and records a
branch-specific deterministic M400 trajectory anchor:

- `normal` branch for the single normal-success regression.
- `wrong_history` branch for wrong-history-safe regressions.

The M407 failed-row table uses `baseline_*` margin columns, while the compact
old-key replay helpers use `reference_*` margin columns. M410 adds an internal
schema normalizer for that table shape only.

## Export Result

Run directory:

```text
runs/m410_old_key_replay_failure_trajectory_anchor
```

Primary artifact:

```text
runs/m410_old_key_replay_failure_trajectory_anchor/old_key_replay_failure_trajectory_anchor.npz
```

| Metric | Value |
| --- | ---: |
| failed rows | `7` |
| missing rows | `0` |
| normal branch rows | `1` |
| wrong-history branch rows | `6` |
| trajectory anchor rows | `290` |
| observation shape | `290 x 72` |
| hidden shape | `290 x 128` |
| action shape | `290 x 3` |

The branch split matches the M407 audit: six old-key wrong-history-safe
regressions and one old-key normal-branch failure.

## No-Update Smoke

No-update exact repair smoke:

```text
runs/m410_old_key_replay_trajectory_anchor_no_update_smoke
```

Key result:

| Metric | Value |
| --- | ---: |
| replay trajectory anchor rows | `290` |
| replay trajectory anchor loss | `6.694095e-15` |
| exact M297 delta | `0.0` |
| exact M270 delta | `0.0` |
| old-key surrogate delta | `0.0` |
| exact lexicographic pass | `true` |

The near-zero trajectory loss is expected because the smoke uses the same M400
base checkpoint that generated the reference old-key trajectories.

## Tests

Focused tests:

```text
tests/test_old_key_replay_failure_trajectory_anchor.py
tests/test_exact_post_ppo_repair.py
tests/test_old_key_neighborhood_targeted_replay.py
```

Result:

```text
20 passed
```

## Decision

Admit:

```text
m411-combined-replay-aware-projection-probe
```

M411 should combine the M409 M267/M264 failed-row trajectory anchor with this
M410 old-key anchor, then run a no-PPO replay-aware exact projection probe.
Exact M297/M270/old-key no-regression remains the first feasibility filter, and
closed-loop replay gates remain authoritative.
