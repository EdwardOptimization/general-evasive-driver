# M1228 Paper-Route Terminal-Boundary Negative Audit

## Summary

M1228 audits the negative M1227 relocation smoke before any further relocation
or training.

Decision:

```text
terminal_boundary_negative_audit_route_to_source_geometry_consistency
```

M1227 did not fail because a source-diverse candidate pool was missing. It
failed after source and candidate gates passed:

```text
source_budget_ready: true
candidate_selection_ready: true
selected_rows: 100
selected_physical_pairs: 100
selected_left_steps: 5
selected_targets: 2
relocation rows: 7200
accepted_wrong_rows: 0
```

The dominant failure mode is:

```text
all relocated normal-history rollouts collided
```

Therefore M1227 cannot be used as causal-history or self-identification
evidence.

## Failure Classification

Failure type:

```text
scenario_sampling_failure
```

More specific label:

```text
source_geometry_replay_consistency_gap
```

M1227's downstream robustness decision was:

```text
reject_duplicate_dominated_boundary_surface
```

That label is generic and misleading for this case. There were no accepted rows
to be duplicate dominated. The useful diagnosis is:

```text
normal_success:        0 / 7200
variant_success:       0 / 7200
normal_collision:   7200 / 7200
variant_collision:  7200 / 7200
normal_near_boundary:  0 / 7200
accepted:              0 / 7200
```

## Source-Geometry Diagnostic

The first suspicion was that obstacle offsets or half-width inflation were too
aggressive. However, filtering M1227 rows to exact source geometry still shows
normal-history collision:

```text
dx = 0, dy = 0, all widths:
  rows: 800
  normal_success: 0
  normal_margin range: [-0.2999323157, -0.0000110193]

dx = 0, dy = 0, half_width_inflation = 0:
  rows: 100
  normal_success: 0
  normal_margin range: [-0.1945879451, -0.0080074171]

dx = 0, dy = 0, half_width_inflation = 0.1:
  rows: 100
  normal_success: 0
  normal_margin range: [-0.2269237245, -0.0508360686]
```

This is stronger than "grid too aggressive": even the apparent source geometry
is not reproducing M1222's normal-success condition inside M1227's replay path.

## Likely Causes

There are three plausible causes that must be separated before another
materialization attempt:

1. **Continuation horizon mismatch.**
   M1222 source mining used a short continuation window. M1227 used
   `max_continuation_steps=60`. Rows that survived the M1222 short window may
   collide under the longer materialization horizon.

2. **Replay-path geometry/state mismatch.**
   M1227 recomputes source obstacle geometry from the collected left snapshot
   and then relocates the snapshot. This may not be exactly equivalent to the
   M1222 source-rollout state used for candidate scoring.

3. **Near-zero terminal target overshoot.**
   Some rows with positive wrong-history margin gap have normal margins very
   close to zero but slightly negative, for example around `-1e-5`. These rows
   are not valid proof rows because the normal branch collided, but they suggest
   the relocation machinery can reach the boundary if source consistency is
   repaired.

## Rejected Shortcuts

Do not:

- train from M1227;
- weaken `accepted` to allow normal-collision rows;
- count positive `margin_gap` when `normal_success` is false;
- expand the relocation grid before understanding source replay consistency;
- claim recurrent belief or self-identification.

## Selected Next Route

M1229 should run a source-geometry consistency audit before any new relocation
grid:

```text
source geometry only:
  body_longitudinal_offsets = 0
  body_lateral_offsets = 0
  half_width_inflations = 0
  target_normal_margins = 999
```

Run two horizons:

```text
short horizon: max_continuation_steps = 12
long horizon:  max_continuation_steps = 60
```

Interpretation:

```text
short succeeds, long fails:
  M1222 candidates are short-horizon-safe but long-horizon-colliding.
  Next route should define terminal-boundary materialization horizon explicitly.

short fails, long fails:
  M1226/M1227 source replay path does not reproduce M1222 candidate scoring.
  Next route should repair source snapshot/schema consistency before relocation.

short succeeds, long succeeds:
  M1227 failure was caused by half-width/offset target grid.
  Next route can use a narrower positive-margin relocation grid.
```

## Decision

```text
terminal_boundary_negative_audit_route_to_source_geometry_consistency
```

Outcome-level causal-history evidence remains blocked until a later run
produces normal-success wrong-history margin or success degradation.
