# M1121 V4 Public Base Failed Wrong-History Retention First Replay Failure Audit

## Purpose

M1121 audits the M1120 first-replay failure before any further update or replay
escalation.

This milestone reads existing M1115/M1118/M1120 artifacts only. It does not
train actor weights, run PPO, run replay, mine rows, promote a checkpoint, use
private holdout, or change actor inputs.

## Parent Result

M1120 rejected the M1118 best candidate:

```text
candidate: m1118_seed111800
checkpoint:
  runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt

result_class: failed_wrong_history_retention_first_replay_failed_wrong_history_safe
surface_count: 6
passed_surface_count: 2
failed_surface_count: 4
normal_lost_events: 0
wrong_history_safe_events: 4
```

The two passing surfaces were `m183_m168` and `m223_m219`. The failing surfaces
were `m267_m264`, `current_m333_surface`, `m314_continuity_surface`, and
`m317_continuity_surface`.

## Row-Level Failure

All four M1120 lost success-drop events are the same row:

```text
row_id: 15
target: future_braking_deceleration
physical_pair_key: 9530:21:9550:21
left_step/right_step: 21/21
normal_lost: false
wrong_history_safe: true
```

M1120 wrong-history terminal margins:

```text
m267_m264:
  base:      -0.000561981
  candidate:  0.001226317

current_m333_surface:
  base:      -0.001337010
  candidate:  0.000452670

m314_continuity_surface:
  base:      -0.001053794
  candidate:  0.000735468

m317_continuity_surface:
  base:      -0.001054539
  candidate:  0.000734725
```

The passing `m223_m219` row 15 had more negative base wrong-history slack and
remained just negative after the update:

```text
m223_m219:
  base wrong-history margin:      -0.002520876
  candidate wrong-history margin: -0.000730622
```

This means the update produced a similar positive shift in row15 wrong-history
margin across variants, but only surfaces with less initial negative slack
crossed zero.

## Anchor Coverage

Row 15 was not missing from the M1115 target-base retention anchor.

M1115 target-base rejected-history trajectory anchor:

```text
anchor_rows_total: 707
row15_anchor_rows: 170
row15_surfaces:
  m223_m219:              34 rows
  m267_m264:              34 rows
  current_m333_surface:   34 rows
  m314_continuity_surface:34 rows
  m317_continuity_surface:34 rows
row15_step_range: 0..33 for every listed surface
```

M1118 target-base-only trajectory-anchor audit also stayed far below the
pre-replay threshold:

```text
base target-base-only trajectory MSE:       0.0000000000000057
m1118_seed111800 target-base-only MSE:      0.0000014984544805
registered threshold:                       0.0001000000000000
```

Therefore M1120 is not an anchor-coverage miss. It is an anchor-insufficiency
case: a small trajectory-action drift can still change the wrong-history
terminal outcome when the wrong-history margin is near zero.

## Action and Outcome Pattern

For the failing `m267_m264` row15 replay:

```text
base wrong-history terminal:      collision
candidate wrong-history terminal: obstacle_completed

base wrong-history first action:
  steer:    0.660116
  throttle:-0.004611
  brake:    0.097558

candidate wrong-history first action:
  steer:    0.661982
  throttle:-0.006257
  brake:    0.098026
```

The first-action movement is small, and M1118's aggregate target-base trajectory
MSE is small. The terminal margin nevertheless crosses zero. This is consistent
with a near-boundary wrong-history row where action imitation or MSE retention
does not encode the real proof constraint:

```text
correct-history branch should remain safe;
wrong-history branch should remain unsafe by margin, not merely action-close.
```

## Classification

```text
failure_type: proof_washout
subtype: wrong_history_safe_terminal_margin_crossing
normal_history_collapse: false
anchor_coverage_miss: false
action_anchor_threshold_failure: false
metric_artifact: false
```

This is narrower than M1112. M1112 lost `47` success-drop events. M1120 loses
`4`, all row15 variants. The M1115/M1118 route is directionally useful, but it
does not fully protect the remaining near-zero wrong-history terminal margins.

## Decision

```text
failed_wrong_history_retention_failure_audit_route_to_row15_unsafe_margin_retention_design
```

The next repair should not simply add more generic trajectory-action anchor
pressure. M1122 should design a row15-focused unsafe-margin or terminal-margin
retention objective that explicitly penalizes wrong-history margins crossing
zero while preserving normal-history success and the M1107 exact objective.

Next milestone:

```text
m1122-v4-public-base-row15-unsafe-margin-retention-design
```
