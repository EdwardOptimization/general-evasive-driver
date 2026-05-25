# M860 V4 Closer Obstacle Source Generation Implementation

## Purpose

M860 implements the M859 no-training generation route after M857/M858 showed
that most boundary-new-to-M844 source-axis traces were all-safe-wide.

The implementation question is:

```text
Can M857 all-safe-wide and all-collision source-axis traces be converted into
new successful non-collision low-margin boundary rows before pair-delta mining?
```

M860 is not a training milestone:

```text
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
no pair-delta sequence replay
```

## Implementation

Added:

```text
src/autodrift/v4_closer_obstacle_source_generation.py
tests/test_v4_closer_obstacle_source_generation.py
```

The runner consumes M857 trace artifacts, selects primary
`boundary_new_to_m844` source-axis rows with:

```text
trace_role == primary_boundary_new_to_m844
cause_class in {all_safe_wide, all_collision_or_negative}
```

It generates two tagged plan families:

```text
all_safe_closer_obstacle
all_collision_safer_side
```

For all-safe-wide rows, it finds the closest wide-safe trace point and
extrapolates in the direction that reduced clearance margin. For
all-collision rows, it finds the least-negative trace point and moves back
toward the original source parameter.

Accepted rows require:

```text
trace_role == primary_boundary_new_to_m844
success == true
collision == false
0.0 <= min_clearance_margin <= 0.05
```

Pairability projection is cheap geometry/action filtering only. It does not
execute pair-delta sequence replay.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_closer_obstacle_source_generation \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --m857-axis-summary runs/m857_v4_boundary_new_to_m844_bracket_trace/axis_trace_summary.csv \
  --m857-trace-rows runs/m857_v4_boundary_new_to_m844_bracket_trace/bracket_trace_rows.csv \
  --m857-target-trace-source-rows runs/m857_v4_boundary_new_to_m844_bracket_trace/target_trace_source_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m860_v4_closer_obstacle_source_generation \
  --device cpu
```

## Artifacts

```text
runs/m860_v4_closer_obstacle_source_generation/summary.json
runs/m860_v4_closer_obstacle_source_generation/generation_plan_rows.csv
runs/m860_v4_closer_obstacle_source_generation/generated_replay_rows.csv
runs/m860_v4_closer_obstacle_source_generation/accepted_generated_boundary_rows.csv
runs/m860_v4_closer_obstacle_source_generation/all_accepted_generated_rows.csv
runs/m860_v4_closer_obstacle_source_generation/pairability_projection_rows.csv
runs/m860_v4_closer_obstacle_source_generation/source_generation_summary.csv
runs/m860_v4_closer_obstacle_source_generation/gate_summary.csv
runs/m860_v4_closer_obstacle_source_generation/rejected_rows.csv
```

## Result

M860 completed and preserved frozen parameters:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
pair_delta_sequence_replay_used: false
promoted: false
checkpoint_promoted: false
```

Generation-plan coverage passed:

```text
generation_plan_rows: 660
primary_source_groups_planned: 44
primary_seed_count_planned: 8
primary_fault_family_count_planned: 9
generated_replay_rows: 660
snapshot_rejection_rows: 0
```

Generated boundary coverage remained below sparse gate:

```text
accepted_generated_boundary_rows: 17
accepted_boundary_new_to_m844_rows: 17
unique_source_group_count: 17
unique_seed_count: 4
unique_fault_family_count: 8
unique_boundary_axis_count: 2
max_source_group_dominance: 0.058824
max_seed_dominance: 0.294118
```

Pairability projection was close to sparse but still below threshold:

```text
pairability_projection_rows: 38
diagnostic_pairability_projection_rows: 61
sparse_min_pairability_projection_rows: 40
```

Result class:

```text
v4_closer_obstacle_source_generation_source_limited
```

## Gate Summary

Passed:

```text
actor checksum unchanged
residual-head checksum unchanged
generation_plan_rows: 660 >= 300
pair_delta_sequence_replay_blocked: true
ppo_blocked: true
```

Failed strong gates:

```text
accepted_generated_boundary_rows: 17 < 80
accepted_boundary_new_to_m844_rows: 17 < 60
pairability_projection_rows: 38 < 120
```

Failed sparse gates:

```text
accepted_generated_boundary_rows: 17 < 32
accepted_boundary_new_to_m844_rows: 17 < 24
unique_seed_count: 4 < 5
pairability_projection_rows: 38 < 40
```

## Source Generation Audit

Acceptance was concentrated in the all-safe closer-obstacle route:

```text
all_safe_closer_obstacle: 570 replay rows, 17 accepted
all_collision_safer_side: 90 replay rows, 0 accepted
```

By axis:

```text
obstacle_lateral_offset: 220 replay rows, 14 accepted
obstacle_timing: 220 replay rows, 3 accepted
obstacle_half_width: 220 replay rows, 0 accepted
```

By fault family, accepted rows covered eight families, but only four seeds:

```text
brake_authority_drop: 2
combined_fault: 4
delay_noise_fault: 1
drive_authority_drop: 1
front_lateral_authority_drop: 3
mass_cg_shift: 1
rear_lateral_authority_drop: 3
steering_fault: 2
global_mu_drop: 0
```

The result is better than M857's zero generated boundary rows, but it is not yet
an objective-ready pair-delta source surface. The most informative near-miss is:

```text
accepted rows: 17
primary pairability rows: 38
sparse thresholds: 32 rows and 40 primary pairability rows
```

This suggests single-axis closer obstacle generation is a valid route, but not
yet broad enough. All-collision safer-side and half-width-only generation did
not contribute accepted rows in this pass.

## Interpretation

M860 is a clean source-limited diagnostic:

```text
trace-derived source generation works;
snapshot reconstruction and normal replay work;
actor and M761 contracts are preserved;
all-safe closer obstacle generation opens some new boundary rows;
single-axis generation is still below sparse-useful coverage.
```

Unsupported claims:

```text
pair-delta outcome evidence
objective-ready self-ID corpus
learned policy improvement
PPO admission
checkpoint promotion
```

The next step should audit whether to:

```text
1. add bounded combined tightening for very wide all-safe rows;
2. add source-step neighborhood shifts for collision-side rows;
3. broaden obstacle/source scenario generation beyond single-axis trace moves;
4. defer pair-delta mining until sparse generated-boundary coverage is reached.
```

Objective training, PPO, residual-head mutation, actor mutation, pair-delta
sequence replay, and promotion remain blocked.

## Tests

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_v4_closer_obstacle_source_generation.py
```

Result:

```text
3 passed
```

Compile check:

```bash
python -m compileall -q src tests
```

Result:

```text
passed
```

## Decision

Decision:

```text
v4_closer_obstacle_source_generation_source_limited
```

Next:

```text
m861-v4-closer-obstacle-source-generation-audit
```
