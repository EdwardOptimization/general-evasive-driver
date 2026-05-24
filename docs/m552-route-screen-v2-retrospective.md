# M552 Route-Screen V2 Retrospective

## Purpose

M552 retrospectively tests the M551 route-screen v2 rule on the M549 selected
checkpoint.

Question:

```text
Would route-screen v2 have rejected M549 before the M550 public-surface eval?
```

This is a process gate. It does not train or promote a checkpoint.

## Implementation Note

M551 initially described the route screen as using the M548 L3 env config. In
implementation, L0/L2/L3 checkpoints require level-matched observation history
lengths:

```text
L0: history_length = 1
L2: history_length = 4
L3: history_length = 1
```

M552 therefore keeps the same task distribution while using each checkpoint's
matching history-level config. This preserves checkpoint observation contracts
and avoids forcing the L2 finite-window actor into an incompatible observation
shape.

## Evaluated Checkpoints

| Label | Level | Checkpoint |
| --- | --- | --- |
| `l0_s3540` | L0 | `runs/m542_matched_l0_variance_seed3540/checkpoint.pt` |
| `l2_s3540` | L2 | `runs/m542_matched_l2_variance_seed3540/checkpoint.pt` |
| `l3_m542_s3540` | L3 | `runs/m542_matched_l3_variance_seed3540/checkpoint.pt` |
| `l3_m549_fast2816` | L3 | `runs/m549_l3_repair_fast_select_ckpt256_seed3540/checkpoints/checkpoint_step_2816.pt` |

Route screen:

```text
episodes = 64
seed = 14540
uses_public_frozen_source_rows = false
```

Artifacts:

```text
runs/m552_route_screen_v2_retrospective/summary.json
runs/m552_route_screen_v2_retrospective/policy_summary.csv
runs/m552_route_screen_v2_retrospective/episodes.csv
```

## Result

| Label | Success | Termination | Collision | Completion | Return | Margin Mean | Margin Median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `l0_s3540` | `0.062500` | `0.937500` | `0.859375` | `0.062500` | `22.679497` | `-0.044126` | `-0.109331` |
| `l2_s3540` | `0.609375` | `0.390625` | `0.390625` | `0.609375` | `60.225915` | `1.027347` | `0.754775` |
| `l3_m542_s3540` | `0.078125` | `0.921875` | `0.578125` | `0.078125` | `22.632401` | `0.437544` | `-0.027147` |
| `l3_m549_fast2816` | `0.046875` | `0.953125` | `0.718750` | `0.046875` | `22.035721` | `0.213472` | `-0.067931` |

Route-screen v2 checks for `l3_m549_fast2816`:

```text
candidate_success_minus_l0 = -0.015625
candidate_margin_minus_l0  = +0.257598
candidate_collision_minus_l0 = -0.140625

candidate_success_minus_l2 = -0.562500
candidate_margin_minus_l2  = -0.813875

passes_l0_success = false
passes_l0_margin = true
passes_l0_collision_tolerance = true
would_admit_public_eval = false
```

## Interpretation

M552 validates the workflow fix:

```text
route-screen v2 would have rejected the M549 selected checkpoint before M550.
```

The candidate has better mean clearance margin and lower collision rate than L0
on this route screen, but it fails the first lexicographic rule because obstacle
success is below L0. It is also far below L2, which remains the strong
finite-window baseline.

This means the M550 failure was not inevitable. A stronger public-neutral route
screen would have caught it before spending public frozen-source eval budget.

## Next Step

The next milestone should make route-screen v2 reusable rather than leaving it
as an ad hoc retrospective script.

M553 should implement a route-screen v2 runner/selector that:

- evaluates candidate checkpoints with L0/L2 references;
- uses level-matched env configs to preserve observation contracts;
- writes `policy_summary.csv`, `episodes.csv`, and `summary.json`;
- applies the M551 lexicographic route-screen v2 rule;
- blocks public diagnostics when a candidate is below L0.

## Decision

```text
route_screen_v2_rejects_m549_admit_m553_runner
```
