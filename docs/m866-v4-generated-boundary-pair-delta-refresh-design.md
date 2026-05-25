# M866 V4 Generated Boundary Pair-Delta Refresh Design

## Purpose

M866 designs the next no-training step after M865 audited M864 as sparse-useful
generated-boundary coverage.

The design question is:

```text
Can M864 combined generated-boundary rows produce real pair-delta sequence
outcome evidence, rather than only pairability projection?
```

M866 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Motivation

M864 passes sparse generated-boundary gates:

```text
combined_generated_boundary_rows: 59
combined_boundary_new_to_m844_rows: 59
combined_unique_source_group_count: 27
combined_unique_seed_count: 5
combined_unique_fault_family_count: 9
combined_pairability_projection_rows: 365
```

But M864 is still not pair-delta evidence:

```text
pairability_projection_rows are cheap geometry/action filters;
no pair-delta sequence replay has been executed on the M864 surface;
no learned self-ID claim is allowed from generated boundary rows alone.
```

M867 should convert projection into actual sequence outcomes with explicit
source-aware caps and gates.

## Actor Contract

The actor remains P0 human-view. Pair metadata may be used for offline mining,
but deployed actor input must not change:

```text
no hidden parameters as actor input
no fault labels as actor input
no oracle feasibility or controller mode
no TTC or reference-path errors
no slip, tire force, or friction-margin channels
```

Pair-delta sequence rows are direct intervention diagnostics. They are not
learned self-ID proof.

## Inputs

M867 should use:

```text
runs/m864_v4_generated_boundary_refinement/summary.json
runs/m864_v4_generated_boundary_refinement/combined_generated_boundary_rows.csv
runs/m864_v4_generated_boundary_refinement/pairability_projection_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

M867 may rebuild pair candidates directly from combined rows instead of relying
on M864 pairability row IDs, because the combined artifact contains stable
source/step/axis/parameter/action/obstacle fields.

## Candidate Pair Selection

Primary candidate rows should be successful non-collision boundary rows:

```text
success == true
collision == false
0.0 <= min_clearance_margin <= 0.05
boundary_source_status == boundary_new_to_m844
```

Build pair candidates from left/right combined rows with:

```text
left_source_group_id != right_source_group_id
first_action_l2 >= 0.014
obstacle_geometry_distance <= 0.10 primary
obstacle_geometry_distance <= 0.20 diagnostic
```

Selection should be source-aware:

```text
max_pairs: 180
max_pairs_per_left_source_group: 12
max_pairs_per_right_source_group: 12
max_pairs_per_left_seed: 48
max_pairs_per_fault_family_pair: 16
max_pairs_per_boundary_axis_pair: 64
```

Prioritize:

```text
primary_0_10 pairability tier
different fault families
different seeds when available
balanced left source groups
larger first_action_l2
smaller obstacle_geometry_distance
```

M864 is axis-concentrated, so M867 should record axis-pair dominance rather
than hide it.

## Pair-Delta Sequence Replay

M867 should replay pair-delta directions only:

```text
directions:
  pair_delta_positive
  pair_delta_negative

hold_steps_grid: [4, 6]
epsilon_l2_grid: [0.025, 0.05, 0.075]
```

Component directions may be replayed only after accepted pair-delta rows exist,
as controls:

```text
steer_axis
throttle_axis
brake_axis
```

Component controls must not satisfy primary M867 gates.

## Acceptance

Accepted pair-delta rows should require:

```text
normal_success == true
normal_collision == false
0.0 <= normal_margin <= 0.05
direction_family == pair_delta
effective_delta_l2_mean >= 0.014
abs_margin_delta >= 0.01
or success_flip == true
or collision_flip == true
```

Classify accepted rows:

```text
pair_delta_degradation
pair_delta_improvement
pair_delta_outcome_flip
```

Keep both directions. Do not balance by deleting one direction before writing
the raw accepted artifact.

## Source-Balanced Selection

After raw acceptance, select:

```text
balanced_pair_delta_rows.csv
```

Balance dimensions:

```text
left_source_group_id
left_seed
left_fault_family
right_fault_family
fault_family_pair
left_boundary_axis
right_boundary_axis
hold_steps
direction
```

Caps:

```text
max_rows_per_left_source_group: 8
max_rows_per_left_seed: 16
max_rows_per_left_fault_family: 16
max_rows_per_fault_family_pair: 8
max_rows_per_direction: 24
max_rows_per_axis_pair: 32
```

Write source-aware public splits:

```text
train_public_rows.csv
eval_public_rows.csv
source_holdout_public_rows.csv
```

The split must be by source group or seed, not row-level random split.

## Gates

Candidate selection:

```text
pair_candidate_rows >= 120
selected_replay_pairs >= 80
unique_left_source_group_count >= 16
unique_left_seed_count >= 5
unique_left_fault_family_count >= 8
```

Strong pair-delta corpus:

```text
balanced_pair_delta_rows >= 60
unique_left_source_group_count >= 8
unique_left_seed_count >= 4
unique_left_fault_family_count >= 5
unique_fault_family_pair_count >= 10
unique_hold_steps_count >= 2
unique_direction_count >= 2
max_left_source_group_dominance <= 0.30
max_left_seed_dominance <= 0.40
max_direction_dominance <= 0.60
```

Sparse pair-delta positive:

```text
balanced_pair_delta_rows >= 30
unique_left_source_group_count >= 5
unique_left_seed_count >= 3
unique_left_fault_family_count >= 3
unique_fault_family_pair_count >= 6
```

All-weak:

```text
accepted_pair_delta_rows < 10
and max_abs_margin_delta < 0.01
and no success/collision flips
```

Source-limited:

```text
accepted_pair_delta_rows >= 10
but sparse or strong diversity gates fail
```

Contract gates:

```text
actor_checksum_unchanged == true
residual_head_checksum_unchanged == true
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

## Required Artifacts

M867 should write:

```text
src/autodrift/v4_generated_boundary_pair_delta_refresh.py
tests/test_v4_generated_boundary_pair_delta_refresh.py
runs/m867_v4_generated_boundary_pair_delta_refresh/summary.json
runs/m867_v4_generated_boundary_pair_delta_refresh/pair_candidate_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/pair_delta_sequence_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/accepted_pair_delta_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/balanced_pair_delta_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/component_control_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/train_public_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/eval_public_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/source_holdout_public_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/diversity_summary.json
runs/m867_v4_generated_boundary_pair_delta_refresh/gate_summary.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/rejected_rows.csv
```

## Interpretation Rules

If sparse or strong pair-delta passes:

```text
audit before objective design
```

If raw accepted rows are high but balanced rows fail:

```text
audit as source-limited; do not train
```

If component controls dominate over pair-delta rows:

```text
audit as metric-artifact risk before objective design
```

If all-weak:

```text
audit whether M864 pairability projection was misleading before more replay
```

## Decision

Decision:

```text
generated_boundary_pair_delta_refresh_design_admit_m867
```

Next:

```text
m867-v4-generated-boundary-pair-delta-refresh-implementation
```
