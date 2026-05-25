# M856 V4 Boundary-New-To-M844 Bracket Trace Design

## Purpose

M856 designs the next no-training diagnostic after M855.

The design question is:

```text
Why do M854 boundary-new-to-M844 sources fail to produce collision/success
brackets?
```

M856 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
no pair-delta sequence replay
```

## Motivation

M854 target selection was broad:

```text
target_source_rows: 61
target_unique_seed_count: 12
target_unique_fault_family_count: 9
```

But accepted boundary rows came only from recovered M844 boundary sources:

```text
accepted_boundary_rows: 32
accepted boundary_new_to_m844 rows: 0
rejected_rows: 151
rejection_reason: no_collision_safe_bracket
```

The current artifacts do not preserve the full initial/expansion evaluation
trace for rejected axes. Therefore the branch cannot yet distinguish:

```text
all-safe wide-margin sources
all-collision sources
axis range miss
non-monotone or ambiguous traces
source-step mismatch
geometry outside the useful boundary window
```

M857 should be a trace-first implementation, not another blind expansion.

## Actor Contract

The actor remains P0 human-view. The trace diagnostic may use simulator and
source metadata for offline mining, but it must not change deployable actor
inputs:

```text
no hidden parameters as actor input
no fault labels as actor input
no oracle feasibility or controller mode
no TTC or reference-path errors
no slip, tire force, or friction-margin channels
```

Trace rows are data-construction diagnostics, not learned self-ID proof.

## Inputs

M857 should use:

```text
runs/m854_v4_pair_delta_boundary_expansion/target_source_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/rejected_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/accepted_boundary_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

Target rows:

```text
boundary_source_status == boundary_new_to_m844
source_target_class == new_underrepresented_boundary
```

M857 should include existing-boundary recovered rows only as a small positive
control set. They cannot satisfy the primary trace gates.

## Trace Grid

For every selected source and boundary axis, M857 should log every evaluated
parameter, not only refined rows.

Axes:

```text
obstacle_lateral_offset
obstacle_timing
obstacle_half_width
```

Initial deltas should match M854:

```text
timing: [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0]
lateral: [-0.45, -0.25, -0.12, 0.0, 0.12, 0.25, 0.45]
half_width: [-0.08, -0.04, 0.0, 0.04, 0.08, 0.14]
```

Extended diagnostic deltas should be wider but still bounded:

```text
timing: [-4.0, -3.0, -2.0, -1.5, -1.0, -0.5, 0.0,
          0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
lateral: [-1.40, -1.00, -0.70, -0.45, -0.25, -0.12, 0.0,
           0.12, 0.25, 0.45, 0.70, 1.00, 1.40]
half_width: [-0.20, -0.14, -0.08, -0.04, 0.0, 0.04, 0.08,
              0.14, 0.20, 0.28, 0.36]
```

Timing values must still be clipped to a positive longitudinal obstacle
distance, and half-width must stay at least `0.05`.

## Required Artifacts

M857 should write:

```text
src/autodrift/v4_boundary_new_to_m844_bracket_trace.py
tests/test_v4_boundary_new_to_m844_bracket_trace.py
runs/m857_v4_boundary_new_to_m844_bracket_trace/summary.json
runs/m857_v4_boundary_new_to_m844_bracket_trace/target_trace_source_rows.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/bracket_trace_rows.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/axis_trace_summary.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/source_trace_summary.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/cause_summary.json
runs/m857_v4_boundary_new_to_m844_bracket_trace/candidate_expansion_plan_rows.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/gate_summary.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/rejected_rows.csv
```

## Trace Row Schema

Each `bracket_trace_rows.csv` row should include:

```text
trace_id
source_group_id
seed
step
preferred_fault_family
warmup_mode
boundary_axis
grid_family                  # initial or extended
parameter_value
target_obstacle_body_x
target_obstacle_body_y
target_obstacle_half_width
reconstructed
success
collision
terminal_reason
min_clearance_margin
outcome_class                # safe_boundary, safe_wide, negative, ambiguous
first_steer
first_throttle
first_brake
```

Outcome classes:

```text
safe_boundary:
  success and not collision and 0.0 <= margin <= 0.05

safe_wide:
  success and not collision and margin > 0.05

negative:
  collision or margin < 0.0

ambiguous:
  non-finite margin, reconstruction failure, or neither safe nor negative
```

## No-Bracket Cause Taxonomy

Each source-axis summary should classify into exactly one primary cause:

```text
bracket_found_initial
bracket_found_extended
accepted_boundary_found_initial
accepted_boundary_found_extended
all_safe_wide
all_collision_or_negative
mixed_no_adjacent_bracket
ambiguous_or_nonfinite
reconstruction_error
insufficient_trace
```

The implementation should also report secondary flags:

```text
has_negative
has_safe_boundary
has_safe_wide
has_ambiguous
min_margin
max_margin
margin_sign_changes
closest_margin_abs
```

## Gates

Trace completeness:

```text
target_boundary_new_to_m844_sources >= 40
traced_source_axis_rows >= 100
bracket_trace_rows >= 1000
cause_classified_source_axis_share >= 0.95
actor_checksum_unchanged == true
residual_head_checksum_unchanged == true
pair_delta_sequence_replay_used == false
ppo_used == false
```

Actionable positive diagnostic:

```text
accepted_boundary_found_extended_source_axes >= 12
accepted_boundary_found_extended_source_groups >= 6
unique_fault_family_count_for_extended_accepts >= 4
```

If this passes, M858 should implement a bounded boundary-new-to-M844 expansion
using the discovered source-axis ranges.

All-safe diagnostic:

```text
all_safe_wide_source_axis_share >= 0.60
```

If this dominates, the branch should design closer obstacle/source generation
instead of widening the same axes.

All-collision diagnostic:

```text
all_collision_or_negative_source_axis_share >= 0.60
```

If this dominates, the branch should design safer-side bracketing or source-step
shifts before pair-delta mining.

Ambiguous diagnostic:

```text
ambiguous_or_nonfinite_source_axis_share >= 0.20
```

If this dominates, M857 should be audited as a trace-quality problem before any
data route change.

## Forbidden Interpretations

M857 must not claim:

```text
learned self-ID evidence
pair-delta outcome evidence
objective-ready corpus
PPO readiness
driver checkpoint improvement
```

It may only classify no-bracket causes and identify a no-training next route.

## Decision

Decision:

```text
boundary_new_to_m844_bracket_trace_design_admit_m857
```

Next:

```text
m857-v4-boundary-new-to-m844-bracket-trace-implementation
```
