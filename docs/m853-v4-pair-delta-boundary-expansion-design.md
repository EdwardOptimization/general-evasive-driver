# M853 V4 Pair-Delta Boundary Expansion Design

## Purpose

M853 designs the first step of the new `v4_pair_delta_boundary_expansion`
branch after M852 synthesis.

The design question is:

```text
Can we expand low-margin boundary coverage over source/fault/seed families that
were absent or weak in M850 balanced pair-delta rows?
```

M853 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Motivation

M850 proved that pair-delta positives are real but concentrated:

```text
accepted_pair_delta_rows: 50
balanced_pair_delta_rows: 24
balanced_unique_left_source_group_count: 3
balanced_unique_left_seed_count: 2
balanced_unique_left_fault_family_count: 3
source_holdout_public_rows: 0
```

The balanced M850 positives used only:

```text
source groups: 35, 41, 47
seeds: 78053, 78059
left fault families: mass_cg_shift, global_mu_drop, delay_noise_fault
```

M825 contains a broader source surface:

```text
source_rows: 64
preferred_fault_family count: 9
seeds include 78048-78059
```

M844 boundary rows already cover more than M850, but still only:

```text
boundary_rows: 39
seeds: 78052, 78053, 78056, 78059
preferred_fault_family count: 7
```

So the next step should expand boundary coverage first, not replay pair-delta on
the same active set.

## Actor Contract

The actor remains P0 human-view. Boundary expansion may use simulator metadata
for offline mining, but deployed actor input must not change:

```text
no hidden parameters as actor input
no fault labels as actor input
no oracle feasibility or controller mode
no TTC or reference-path errors
no slip, tire force, or friction-margin channels
```

Boundary rows are data-construction artifacts, not learned self-ID proof.

## Data Sources

M854 should use:

```text
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/boundary_rows.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/accepted_pair_delta_rows.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/balanced_pair_delta_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

M854 should not require any PPO or newly trained checkpoint.

## Target Selection

M854 should build `target_source_rows.csv` from M825 source rows with a priority
score that favors sources missing from M850 balanced positives.

Hard exclusions:

```text
do not target source groups already dominant in M850 balanced rows unless needed
  for pairability controls:
  35, 41, 47
```

High priority:

```text
seeds absent from M850 balanced rows:
  78048, 78049, 78050, 78051, 78052, 78054, 78055, 78056, 78057, 78058

fault families absent from M850 balanced left side:
  brake_authority_drop
  combined_fault
  drive_authority_drop
  front_lateral_authority_drop
  rear_lateral_authority_drop
  steering_fault

M844 boundary source groups not accepted by M850 balanced pair-delta:
  all source groups except 35, 41, 47
```

Target selection caps:

```text
max_targets_per_seed: 8
max_targets_per_fault_family: 10
max_targets_per_warmup_mode: 16
max_targets_per_source_group: 1
```

Target count:

```text
target_source_rows >= 48
unique_target_seeds >= 8
unique_target_fault_families >= 8
```

## Boundary Bracketing

M854 should reuse the existing adaptive boundary-bracketing semantics:

```text
boundary_axes:
  obstacle_lateral_offset
  obstacle_timing
  obstacle_half_width

boundary_margin_threshold: 0.05
strict_margin_threshold: 0.02
ultra_strict_margin_threshold: 0.005
```

For each target source, M854 should search for a successful, non-collision
low-margin row:

```text
success == true
collision == false
0.0 <= min_clearance_margin <= 0.05
```

Rows should be tagged by whether they are:

```text
new_underrepresented_boundary
existing_boundary_recovered
active_set_control_boundary
```

## Pairability Projection

M854 should not run sequence replay, but it should estimate whether new boundary
rows are pairable:

```text
first_action_l2 >= 0.014
obstacle_geometry_distance <= 0.10 or <= 0.20 diagnostic
left_source_group_id != right_source_group_id
left/right normal margins <= 0.05
```

This should produce:

```text
pairability_projection_rows.csv
```

The projection is only a cheap data-quality diagnostic. It is not pair-delta
outcome evidence.

## Gates

Strong boundary expansion:

```text
accepted_boundary_rows >= 80
new_underrepresented_boundary_rows >= 40
unique_source_group_count >= 32
unique_seed_count >= 8
unique_fault_family_count >= 8
unique_boundary_axis_count >= 3
max_source_group_dominance <= 0.08
max_seed_dominance <= 0.20
pairability_projection_rows >= 160
projected_pairable_source_groups >= 16
```

Sparse useful expansion:

```text
accepted_boundary_rows >= 50
new_underrepresented_boundary_rows >= 24
unique_source_group_count >= 20
unique_seed_count >= 6
unique_fault_family_count >= 6
pairability_projection_rows >= 80
```

All-weak:

```text
accepted_boundary_rows < 24
or new_underrepresented_boundary_rows < 12
```

## Required M854 Artifacts

M854 should write:

```text
src/autodrift/v4_pair_delta_boundary_expansion.py
tests/test_v4_pair_delta_boundary_expansion.py
runs/m854_v4_pair_delta_boundary_expansion/summary.json
runs/m854_v4_pair_delta_boundary_expansion/target_source_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/expanded_boundary_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/accepted_boundary_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/pairability_projection_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/boundary_diversity_summary.json
runs/m854_v4_pair_delta_boundary_expansion/gate_summary.csv
runs/m854_v4_pair_delta_boundary_expansion/rejected_rows.csv
```

## Interpretation Rules

If strong boundary expansion passes:

```text
audit, then run pair-delta-focused mining over the expanded boundary surface
```

If sparse useful expansion passes:

```text
audit, then either tune target selection or run a limited pair-delta-focused
mining pass with source-holdout guard
```

If all-weak:

```text
audit, then return to scenario source generation rather than replaying the same
candidate set
```

## Decision

Decision:

```text
pair_delta_boundary_expansion_design_admit_m854
```

Next:

```text
m854-v4-pair-delta-boundary-expansion-implementation
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, pair-delta objective training, and outcome-coupled objective training
remain blocked.
