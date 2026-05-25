# M862 V4 Generated Boundary Refinement Design

## Purpose

M862 designs the next no-training implementation after M861 found that M860 is
source-limited but refinement-ready.

The design question is:

```text
Can M860 generated wide/negative brackets be refined into accepted
boundary-new-to-M844 rows before any pair-delta sequence replay?
```

M862 is design-only:

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

M860 did not pass sparse generated-boundary gates:

```text
accepted_generated_boundary_rows: 17 < 32
accepted_boundary_new_to_m844_rows: 17 < 24
unique_seed_count: 4 < 5
pairability_projection_rows: 38 < 40
```

But M861 found a more precise blocker:

```text
groups with accepted boundary row: 17
groups with wide/negative bracket but no accepted row: 13
groups all wide: 84
groups all negative: 18
```

So the next step should not jump straight to broad scenario generation or
pair-delta replay. It should first use the generated sign-change brackets that
already exist.

## Actor Contract

The actor remains P0 human-view. M863 may use simulator metadata and generated
replay artifacts for offline data construction, but deployed actor inputs must
not change:

```text
no hidden parameters as actor input
no fault labels as actor input
no oracle feasibility or controller mode
no TTC or reference-path errors
no slip, tire force, or friction-margin channels
```

Generated/refined boundary rows are data-construction artifacts, not learned
self-ID proof.

## Inputs

M863 should use:

```text
runs/m860_v4_closer_obstacle_source_generation/summary.json
runs/m860_v4_closer_obstacle_source_generation/generation_plan_rows.csv
runs/m860_v4_closer_obstacle_source_generation/generated_replay_rows.csv
runs/m860_v4_closer_obstacle_source_generation/accepted_generated_boundary_rows.csv
runs/m860_v4_closer_obstacle_source_generation/pairability_projection_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

Primary candidate rows are M860 generated replay rows with:

```text
trace_role == primary_boundary_new_to_m844
generation_family == all_safe_closer_obstacle
source_target_class == new_underrepresented_boundary
boundary_source_status == boundary_new_to_m844
```

All-collision safer-side rows are not primary for M863 because M860 showed they
remain all negative. They can be carried as diagnostic all-negative rows, but
they should not define the refinement gate.

## Bracket Selection

Group generated replay rows by:

```text
source_group_id
step
boundary_axis
generation_family
```

Within each group, sort by `parameter_value` and find adjacent sign-change
brackets:

```text
negative endpoint:
  collision == true
  or min_clearance_margin < 0

positive endpoint:
  success == true
  collision == false
  min_clearance_margin > 0
```

Prioritize bracket groups with no M860 accepted boundary row:

```text
bracket_source_class == no_m860_boundary
```

Keep groups with existing accepted M860 rows only as support diagnostics:

```text
bracket_source_class == m860_boundary_already_present
```

M863 should persist bracket provenance:

```text
source_group_id
seed
step
preferred_fault_family
boundary_axis
generation_family
negative_parameter
negative_margin
positive_parameter
positive_margin
bracket_parameter_gap
bracket_margin_gap
bracket_source_class
```

## Refinement Strategy

For each selected bracket:

1. Reconstruct the original temporal snapshot using the M825 source rows and
   candidate plan rows.
2. Replay bisection/refinement between the negative and positive generated
   endpoint parameters.
3. Reuse the existing normal closed-loop `_replay_parameter` semantics.
4. Stop when either:

```text
accepted boundary row found
max refinement iterations reached
parameter tolerance reached
```

Suggested defaults:

```text
max_refinement_iterations: 6
primary_margin_threshold: 0.05
strict_margin_threshold: 0.02
parameter_tolerance:
  obstacle_lateral_offset: 0.01
  obstacle_timing: 0.05
  obstacle_half_width: 0.005
```

M863 should accept all successful non-collision refined rows in the boundary
window, not just the first per bracket:

```text
trace_role == primary_boundary_new_to_m844
success == true
collision == false
0.0 <= min_clearance_margin <= 0.05
```

Duplicate exact generated rows should not be counted as new refined rows:

```text
same source_group_id
same step
same boundary_axis
same parameter_value within tolerance
```

## Combined Coverage

M863 should report two coverage views:

```text
refined_only:
  rows found by M863 refinement

combined_m860_plus_refined:
  M860 accepted generated rows
  + unique M863 accepted refined rows
```

The combined view matters because M862's hypothesis is not that refinement
alone creates a full corpus. The hypothesis is that M860 generation plus
refinement can cross sparse generated-boundary coverage.

## Pairability Projection

M863 may compute cheap pairability projection on combined accepted rows:

```text
first_action_l2 >= 0.014
obstacle_geometry_distance <= 0.10 primary
obstacle_geometry_distance <= 0.20 diagnostic
left_source_group_id != right_source_group_id
```

This remains a projection only:

```text
no pair-delta sequence replay
no wrong-history replay
no learned self-ID claim
```

## Required Artifacts

M863 should write:

```text
src/autodrift/v4_generated_boundary_refinement.py
tests/test_v4_generated_boundary_refinement.py
runs/m863_v4_generated_boundary_refinement/summary.json
runs/m863_v4_generated_boundary_refinement/bracket_seed_rows.csv
runs/m863_v4_generated_boundary_refinement/refinement_rows.csv
runs/m863_v4_generated_boundary_refinement/accepted_refined_boundary_rows.csv
runs/m863_v4_generated_boundary_refinement/combined_generated_boundary_rows.csv
runs/m863_v4_generated_boundary_refinement/pairability_projection_rows.csv
runs/m863_v4_generated_boundary_refinement/refinement_summary.csv
runs/m863_v4_generated_boundary_refinement/gate_summary.csv
runs/m863_v4_generated_boundary_refinement/rejected_rows.csv
```

## Gates

Bracket selection gates:

```text
bracket_seed_rows >= 10
no_m860_boundary_bracket_seed_rows >= 10
unique_bracket_source_group_count >= 10
unique_bracket_seed_count >= 3
```

Refined-only useful signal:

```text
accepted_refined_boundary_rows >= 8
accepted_no_m860_boundary_rows >= 6
unique_refined_source_group_count >= 6
```

Combined sparse generated-boundary surface:

```text
combined_generated_boundary_rows >= 32
combined_boundary_new_to_m844_rows >= 24
combined_unique_source_group_count >= 20
combined_unique_seed_count >= 5
combined_unique_fault_family_count >= 8
combined_pairability_projection_rows >= 40
```

Strong generated-boundary surface:

```text
combined_generated_boundary_rows >= 60
combined_boundary_new_to_m844_rows >= 48
combined_unique_source_group_count >= 32
combined_unique_seed_count >= 8
combined_unique_fault_family_count >= 8
combined_pairability_projection_rows >= 100
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

If combined sparse passes:

```text
audit before pair-delta mining
```

If refined-only is positive but combined sparse still fails:

```text
audit before another targeted source/refinement route
```

If bracket selection is broad but refinement returns few accepted rows:

```text
audit whether generated brackets are too steep or require smaller endpoint
grids / parameter-specific tolerances
```

If all accepted rows duplicate M860 accepted rows:

```text
audit as metric artifact; do not count as new coverage
```

If actor or residual-head checksums change:

```text
contract violation; discard result
```

## Decision

The refinement design is admitted, but the branch has reached its 10-milestone
synthesis cadence. The next step must therefore be branch synthesis before any
implementation.

Decision:

```text
route_to_branch_synthesis_before_generated_boundary_refinement
```

Next:

```text
m863-v4-pair-delta-boundary-expansion-branch-synthesis
```
