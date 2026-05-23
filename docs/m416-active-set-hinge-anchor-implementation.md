# M416 Active-Set Hinge Anchor Implementation

M416 implements the radius-aware trajectory hinge infrastructure designed in
M415. It does not run PPO, promote a checkpoint, lower thresholds, or change
actor inputs.

## Code Changes

Trajectory anchors now support an optional `radius` field:

```text
observation
hidden
reference_action
source_index
step_index
weight
radius
```

If `radius` is missing from an older NPZ, the loader fills zeros for backward
compatibility.

The replay trajectory loss now uses a radius hinge:

```text
action_mse = mean((action - reference_action)^2)
distance = sqrt(action_mse)
loss = weight * relu(distance - radius)^2
```

With `radius = 0`, this is numerically equivalent to the previous MSE anchor
scale, so existing tight anchors keep the same behavior.

## Active-Set Anchor

Run directory:

```text
runs/m416_active_set_hinge_anchor
```

Primary artifact:

```text
runs/m416_active_set_hinge_anchor/active_set_hinge_trajectory_anchor.npz
```

| Source | Role | Rows |
| --- | --- | ---: |
| M267/M264 row `6` | active | `40` |
| M267/M264 row `15` | active | `34` |
| old-key `10004...0.800000` | active | `37` |
| old-key `9998...1.400000` | active | `40` |
| old-key `10023...1.200000` | guard | `41` |
| total |  | `192` |

All exported rows currently use explicit `radius = 0.0`. The important change
is that the anchor is active-set selective: it contains only current failed or
guard rows, not the full replay surface.

## No-Update Smoke

No-update exact repair smoke:

```text
runs/m416_active_set_hinge_anchor_no_update_smoke
```

Key result:

| Metric | Value |
| --- | ---: |
| replay trajectory anchor rows | `192` |
| replay trajectory hinge loss | `6.152432e-15` |
| exact M297 delta | `0.0` |
| exact M270 delta | `0.0` |
| old-key surrogate delta | `0.0` |
| exact lexicographic pass | `true` |

## Tests

Focused tests cover:

- missing `radius` backward compatibility;
- explicit `radius` loading;
- hinge zero inside radius and positive outside radius;
- exact repair loss integration.

Result:

```text
31 passed
```

## Decision

Admit:

```text
m417-active-set-hinge-projection-probe
```

M417 should run the no-PPO exact projection from the same M403 alpha `0.1` raw
proposal, using this active-set hinge anchor, and then evaluate exact gates,
M267/M264, old-key compact, M183/M170, and recovery-retention utility.
