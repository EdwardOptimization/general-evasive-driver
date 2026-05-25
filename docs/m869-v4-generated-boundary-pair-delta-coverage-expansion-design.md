# M869 V4 Generated Boundary Pair-Delta Coverage Expansion Design

## Purpose

M869 designs the next no-training step after M868 audited M867 as real but
source-limited pair-delta outcome evidence.

The design question is:

```text
How should the branch expand accepted pair-delta coverage across missing
seeds, directions, and axes before objective training is allowed?
```

M869 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## M867 Blocker

M867 candidate selection was diverse:

```text
selected_replay_pairs: 118
selected_unique_left_source_group_count: 27
selected_unique_left_seed_count: 5
selected_unique_left_fault_family_count: 9
```

But accepted pair-delta outcomes were concentrated:

```text
accepted_pair_delta_rows: 234
accepted left seeds:
  78058: 192
  78050: 42

balanced_pair_delta_rows: 32
balanced_unique_left_seed_count: 2
balanced_max_direction_dominance: 0.75
balanced_max_axis_pair_dominance: 0.96875
```

The missing accepted seeds are:

```text
78048
78055
78057
```

On these seeds M867 replay produced no flips and weak maximum margin deltas:

```text
78048 max_abs_margin_delta: 0.002866466559805936
78055 max_abs_margin_delta: 0.0015455967148021443
78057 max_abs_margin_delta: 0.0011730096064392903
```

So the next implementation should not directly convert M867 to objective data.
It should first expand the accepted outcome surface.

## Design Principles

M870 should remain no-training:

```text
freeze actor
freeze M761 residual head
preserve actor checksum
preserve residual-head checksum
do not run PPO
do not promote
```

M870 should not lower acceptance thresholds just to pass:

```text
do not reduce margin_delta_threshold below 0.01 for primary gates
do not count component-control rows as primary pair-delta rows
do not count pairability projection as outcome evidence
do not admit objective training from weak non-flip rows
```

The target is accepted pair-delta coverage, not more raw pairability.

## Two-Stage Implementation

### Stage A: Rebalance Existing Accepted Rows

Before generating new replay rows, M870 should compute a rebalanced view of
M867's existing accepted rows using stronger selection priorities:

```text
inputs:
  runs/m867_v4_generated_boundary_pair_delta_refresh/accepted_pair_delta_rows.csv
  runs/m867_v4_generated_boundary_pair_delta_refresh/pair_delta_sequence_rows.csv
```

The diagnostic should write:

```text
existing_rebalanced_pair_delta_rows.csv
existing_rebalance_summary.json
```

Selection priorities:

```text
1. include both pair_delta_positive and pair_delta_negative;
2. include obstacle_timing rows when available;
3. cap per left seed, left source, fault pair, direction, and axis pair;
4. preserve high abs_margin_delta and outcome flips within each quota.
```

This stage cannot satisfy final M870 gates alone because M867 accepted rows only
cover two left seeds. It is only a diagnostic to distinguish balance-selection
artifacts from true source gaps.

### Stage B: Target Missing Accepted Seeds

M870 should build target pairs from M867 weak-but-near-sensitive rows for left
seeds:

```text
78048
78055
78057
```

Candidate target criteria:

```text
left_seed in missing accepted seeds
normal_success == true
normal_collision == false
0.0 <= normal_margin <= 0.03
max_abs_margin_delta within the top rows for that seed
prefer hold_steps == 6 and epsilon_l2 == 0.075 from M867, because those were
the strongest weak responses
```

For each target, generate bounded obstacle retargets around the left boundary
row:

```text
obstacle_lateral_offset:
  move toward smaller clearance in small deltas

obstacle_timing:
  move obstacle slightly earlier/later around the existing target

obstacle_half_width:
  widen obstacle in small bounded deltas
```

Retarget acceptance for the normal branch:

```text
normal_success == true
normal_collision == false
0.0 <= normal_margin <= 0.03
```

Then replay pair-delta sequence directions:

```text
directions:
  pair_delta_positive
  pair_delta_negative

hold_steps_grid:
  [6, 8, 10]

epsilon_l2_grid:
  [0.075, 0.10, 0.125]
```

This expands sequence effect strength without changing actor inputs or actor
parameters. Severe clipping must be tracked, and rows dominated by clipping
should be rejected from primary gates.

## Component Controls

Component controls may be replayed only after accepted pair-delta rows exist:

```text
steer_positive / steer_negative
throttle_positive / throttle_negative
brake_positive / brake_negative
```

They must be written as diagnostics only:

```text
component_control_rows.csv
component-control accepted rows do not count toward primary M870 gates
```

## Required Artifacts

M870 should write:

```text
src/autodrift/v4_generated_boundary_pair_delta_coverage_expansion.py
tests/test_v4_generated_boundary_pair_delta_coverage_expansion.py
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/summary.json
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/existing_rebalanced_pair_delta_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/existing_rebalance_summary.json
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/target_weak_seed_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/retarget_candidate_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/retarget_replay_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/pair_delta_sequence_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/accepted_pair_delta_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/balanced_pair_delta_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/component_control_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/train_public_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/eval_public_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/source_holdout_public_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/diversity_summary.json
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/gate_summary.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/rejected_rows.csv
docs/m870-v4-generated-boundary-pair-delta-coverage-expansion-implementation.md
```

## Gates

Construction gates:

```text
target_weak_seed_rows >= 24
unique_target_left_seed_count >= 3
retarget_candidate_rows >= 96
retarget_replay_rows > 0
pair_delta_sequence_rows > 0
```

Primary accepted coverage gates:

```text
accepted_pair_delta_rows >= 60
balanced_pair_delta_rows >= 36
balanced_unique_left_seed_count >= 3
balanced_unique_left_source_group_count >= 6
balanced_unique_left_fault_family_count >= 5
balanced_unique_fault_family_pair_count >= 8
balanced_unique_direction_count >= 2
balanced_unique_axis_pair_count >= 2
balanced_max_left_seed_dominance <= 0.45
balanced_max_direction_dominance <= 0.65
balanced_max_axis_pair_dominance <= 0.85
```

Strong target gates:

```text
balanced_pair_delta_rows >= 60
balanced_unique_left_seed_count >= 4
balanced_unique_left_source_group_count >= 8
balanced_unique_left_fault_family_count >= 6
balanced_unique_fault_family_pair_count >= 10
balanced_max_left_seed_dominance <= 0.35
balanced_max_direction_dominance <= 0.60
balanced_max_axis_pair_dominance <= 0.75
```

All-weak classification:

```text
accepted_pair_delta_rows < 10
and max_abs_margin_delta < 0.01
and no success/collision flips
```

Source-limited classification:

```text
accepted_pair_delta_rows >= 10
but primary accepted coverage gates fail
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

## Interpretation Rules

If primary accepted coverage passes:

```text
audit before objective conversion
```

If raw accepted rows grow but balanced gates fail:

```text
classify as source-limited; do not train
```

If missing seeds remain weak:

```text
audit whether current M864 generated-boundary rows are intrinsically
pair-delta-insensitive under short-horizon sequence overrides, then route to
broader source generation rather than PPO
```

If component controls dominate:

```text
classify as metric-artifact risk and do not use component controls as primary
pair-delta evidence
```

## Decision

Decision:

```text
generated_boundary_pair_delta_coverage_expansion_design_admit_m870
```

Next:

```text
m870-v4-generated-boundary-pair-delta-coverage-expansion-implementation
```
