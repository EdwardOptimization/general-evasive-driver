# M413 Replay/Recovery Balance Design

M413 is a design milestone. It does not run PPO, promote a checkpoint, lower
thresholds, or change actor inputs.

## Problem

M411 showed that a single global replay-trajectory coefficient has a sharp
tradeoff:

| Coefficient | M267/M264 | old-key compact | Recovery retained |
| --- | ---: | ---: | ---: |
| `1e11` | `5 / 17` | `34 / 40` | more movement, failed proof |
| `1e12` | `17 / 17` | `37 / 40` | partial movement, failed old-key |
| `1e13` | `17 / 17` | `40 / 40` | only `5.8%` of M406 recovery improvement |

The current-family side is already solved at `1e12`; the remaining failure at
that coefficient is old-key compact. Raising the global coefficient to `1e13`
also over-anchors the current-family rows and collapses useful recovery
movement.

So the next test should not keep increasing one scalar coefficient.

## Design Choice

Use a source-weighted combined trajectory anchor:

```text
M267/M264 rows: keep existing weight
old-key rows: multiply weight by 10
global lambda_replay_trajectory_anchor: 1e12
```

This creates an effective pressure of:

```text
M267/M264: 1e12
old-key:   1e13
```

The design is intentionally minimal and no-code if the existing `weight` field
in the trajectory-anchor NPZ is sufficient. It directly tests the M411 finding:
`1e12` already repairs M267/M264 but not old-key; old-key therefore needs more
branch pressure without over-anchoring the entire replay surface.

## Acceptance Rule

M414 should accept a candidate only if all proof gates pass and utility is not
collapsed.

Hard proof filters:

```text
exact M297 no-regression
exact M270 no-regression
old-key surrogate no-regression
M267/M264 first replay: 17 / 17 success drops
old-key compact replay: 0 accepted regressions
M183/M170 first replay: 17 / 17 success drops
```

Utility filters:

```text
recovery improvement retained vs M406 >= 0.20
candidate is not promoted without a later full public gate
```

The `0.20` recovery-retention threshold is deliberately modest but rules out
the M411 `1e13` result, which retained only `0.058176` of M406's recovery
improvement.

## If M414 Fails

If source-weighted replay anchoring still fails old-key compact, then the issue
is not just source imbalance. The next design should move to an active-set hinge
residual:

```text
loss = weight * relu(action_distance_to_safe_anchor - slack_radius)^2
```

where rows with replay slack get a nonzero radius and only near-failure rows
are pulled tightly toward the safe branch. That would avoid punishing harmless
movement on rows that already have replay margin.

If M414 passes proof but fails the `0.20` recovery-retention utility filter, the
source-weighted approach is still retention-heavy and should not go to full
public gate.

## Decision

Admit:

```text
m414-source-weighted-replay-anchor-probe
```

M414 should create a weighted combined anchor artifact, run no-PPO exact repair
from the same M403 alpha `0.1` raw proposal, and evaluate exact plus first proof
gates and the recovery-retention utility metric.
