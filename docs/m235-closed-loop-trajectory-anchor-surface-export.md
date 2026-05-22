# M235 Closed-Loop Trajectory Anchor Surface Export

M235 exports a multi-step trajectory/action-anchor surface from M224 before any
new PPO. No PPO is run in this milestone.

Actor inputs are unchanged.

## Motivation

M234 showed that M233 satisfied first-action snippet anchors but still failed
closed-loop proof retention. The next anchor surface must therefore cover
teacher-forced action sequences along protected rollouts, not only the first
decision action.

## Exported Sources

The M235 corpus includes the two minimum fragile sources from M234:

| Source | Rows | Why included |
| --- | ---: | --- |
| `m183_m170_row16` | 57 | M233 flipped this row from obstacle-completed to collision |
| `protected_key_9944_perturbed_28_28` | 40 | Historical protected key that M229/M233 leave outside the near-boundary window |

Artifacts:

```text
runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.csv
runs/m235_closed_loop_trajectory_anchor_surface/summary.json
```

## Array Contract

The NPZ contains deployable state/action arrays:

| Array | Shape | Meaning |
| --- | ---: | --- |
| observation | 97 x 72 | human-view observation before action |
| hidden | 97 x 128 | recurrent hidden before action |
| reference_action | 97 x 3 | M224 deterministic action |
| source_index | 97 | trajectory source id |
| step_index | 97 | step within source trajectory |
| weight | 97 | positive trajectory-anchor weight |

All arrays are finite.

## Source Validation

M183 M170 failed row:

| Field | Value |
| --- | --- |
| row id | 16 |
| seed | 9530 |
| snapshot step | 6 |
| geometry | x=13.878356, y=0.190667, half_width=0.728162 |
| exported steps | 57 |
| terminal margin under M224 | 0.000106 |
| obstacle completed | true |

Protected key:

| Field | Value |
| --- | --- |
| key | 9944\|perturbed\|28\|28 |
| seed | 9944 |
| snapshot step | 28 |
| geometry | x=11.0, y=-1.0, half_width=0.9 |
| exported steps | 40 |
| terminal margin under M224 | 0.186385 |
| matches M224 guard margin | true |

The protected-key export initially failed to reproduce the guard margin because
the M133 obstacle perception override was missing from the reconstruction. The
final export applies the same override and matches the M224 guard exactly.

## Decision

M235 completes as infrastructure.

Next blocker:

```text
m236-trajectory-action-anchor-implementation
```

M236 should add a trajectory-level action anchor loader/loss path to training.
It should not run PPO. The loss should sample M235 trajectory rows and anchor
the candidate policy action mean to `reference_action` at each saved
observation/hidden pair.
