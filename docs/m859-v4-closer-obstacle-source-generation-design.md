# M859 V4 Closer Obstacle Source Generation Design

## Purpose

M859 designs the next no-training data route after M858.

The design question is:

```text
Can M857 all-safe-wide traces be converted into closer obstacle/source
candidates that create genuinely new boundary-new-to-M844 low-margin rows?
```

M859 is design-only:

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

M857 made the boundary-new-to-M844 failure mode explicit:

```text
primary source-axis rows: 132
all_safe_wide: 114 / 132 = 0.863636
all_collision_or_negative: 18 / 132 = 0.136364
accepted_boundary_found_extended: 0
bracket_found_extended: 0
```

So the current new-source pool is mostly too safe/wide. The next step should not
blindly widen the same axis grid. It should generate closer obstacle/source
states from the trace evidence.

## Actor Contract

The actor remains P0 human-view. M860 may use simulator/source metadata and
M857 trace artifacts for offline data generation, but deployed actor inputs
must not change:

```text
no hidden parameters as actor input
no fault labels as actor input
no oracle feasibility or controller mode
no TTC or reference-path errors
no slip, tire force, or friction-margin channels
```

Generated boundary rows are data-construction artifacts, not learned self-ID
proof.

## Inputs

M860 should use:

```text
runs/m857_v4_boundary_new_to_m844_bracket_trace/summary.json
runs/m857_v4_boundary_new_to_m844_bracket_trace/axis_trace_summary.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/bracket_trace_rows.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/target_trace_source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

Primary target rows:

```text
trace_role == primary_boundary_new_to_m844
cause_class in {all_safe_wide, all_collision_or_negative}
```

Recovered existing-boundary controls may be used only as diagnostic controls.
They cannot satisfy primary gates.

## Generation Strategy

M860 should create two separately tagged plan families.

### Family A: All-Safe-Wide Closer Obstacle

For each `all_safe_wide` source-axis row:

1. Load all trace rows for the same source group, step, and axis.
2. Find the closest wide-safe row:

```text
min positive min_clearance_margin
```

3. Estimate which direction made the margin smaller by comparing sorted
parameter values and margins.
4. Generate a bounded extrapolation beyond the closest wide-safe point:

```text
parameter = closest_parameter + direction * delta
```

Candidate deltas should be axis-specific:

```text
obstacle_lateral_offset: [0.15, 0.30, 0.50, 0.75, 1.00]
obstacle_timing: [0.50, 1.00, 1.50, 2.00, 3.00]
obstacle_half_width: [0.05, 0.10, 0.16, 0.24, 0.32]
```

If the closest row is still very wide (`margin > 0.50`), the first pass should
prefer combined tightening:

```text
same axis extrapolation + moderate half-width increase
same axis extrapolation + modest earlier obstacle timing
```

Combined tightening must be bounded and tagged as `combined_tighten_safe_wide`.

### Family B: All-Collision Safer Side

For each `all_collision_or_negative` source-axis row:

1. Find the least-negative row closest to zero.
2. Generate safer-side candidates by moving back toward the source parameter.
3. Add source-step neighborhood shifts when available:

```text
step - 3
step + 3
```

This family is not expected to dominate. It is included to avoid losing the
minority collision-side information.

## Replay And Acceptance

M860 should replay only normal closed-loop outcomes for generated candidates.
It must not run pair-delta sequence replay.

Accepted generated boundary rows require:

```text
trace_role == primary_boundary_new_to_m844
success == true
collision == false
0.0 <= min_clearance_margin <= 0.05
```

Rows should retain provenance:

```text
source_group_id
seed
step
preferred_fault_family
source_axis
boundary_axis
trace_cause_class
generation_family
base_trace_parameter
base_trace_margin
generated_parameter
combined_tightening_fields
```

## Pairability Projection

M860 may compute cheap pairability projection after accepted generated rows:

```text
first_action_l2 >= 0.014
obstacle_geometry_distance <= 0.10 primary
obstacle_geometry_distance <= 0.20 diagnostic
left_source_group_id != right_source_group_id
```

This remains a projection only, not pair-delta outcome evidence.

## Required Artifacts

M860 should write:

```text
src/autodrift/v4_closer_obstacle_source_generation.py
tests/test_v4_closer_obstacle_source_generation.py
runs/m860_v4_closer_obstacle_source_generation/summary.json
runs/m860_v4_closer_obstacle_source_generation/generation_plan_rows.csv
runs/m860_v4_closer_obstacle_source_generation/generated_replay_rows.csv
runs/m860_v4_closer_obstacle_source_generation/accepted_generated_boundary_rows.csv
runs/m860_v4_closer_obstacle_source_generation/pairability_projection_rows.csv
runs/m860_v4_closer_obstacle_source_generation/source_generation_summary.csv
runs/m860_v4_closer_obstacle_source_generation/gate_summary.csv
runs/m860_v4_closer_obstacle_source_generation/rejected_rows.csv
```

## Gates

Trace-source coverage:

```text
generation_plan_rows >= 300
primary_source_groups_planned >= 32
primary_seed_count_planned >= 8
primary_fault_family_count_planned >= 6
```

Strong generated boundary surface:

```text
accepted_generated_boundary_rows >= 80
accepted_boundary_new_to_m844_rows >= 60
unique_source_group_count >= 24
unique_seed_count >= 8
unique_fault_family_count >= 6
unique_boundary_axis_count >= 3
max_source_group_dominance <= 0.10
max_seed_dominance <= 0.25
pairability_projection_rows >= 120
```

Sparse useful generated surface:

```text
accepted_generated_boundary_rows >= 32
accepted_boundary_new_to_m844_rows >= 24
unique_source_group_count >= 10
unique_seed_count >= 5
unique_fault_family_count >= 4
pairability_projection_rows >= 40
```

All-weak:

```text
accepted_generated_boundary_rows < 16
or accepted_boundary_new_to_m844_rows < 12
```

Contract gates:

```text
actor_checksum_unchanged == true
residual_head_checksum_unchanged == true
training_started == false
optimizer_started == false
ppo_used == false
pair_delta_sequence_replay_used == false
promoted == false
```

## Interpretation Rules

If strong or sparse generated boundary surface passes:

```text
audit before pair-delta mining
```

If all-weak and generated rows remain mostly safe-wide:

```text
audit before broader scenario generation
```

If all-weak and generated rows become mostly collision:

```text
audit before safer-side source-step neighborhood generation
```

If only recovered controls pass:

```text
do not claim new-source coverage
audit as metric artifact
```

## Decision

Decision:

```text
closer_obstacle_source_generation_design_admit_m860
```

Next:

```text
m860-v4-closer-obstacle-source-generation-implementation
```
