# M872 V4 Boundary-Preserving Missing-Seed Pair-Delta Refresh Design

## Purpose

M872 designs the next no-training implementation after M871 audited M870 as
clean but source-limited.

The design question is:

```text
How should the branch retarget missing seeds while preserving the accepted
normal-branch boundary window before replaying pair-delta sequence overrides?
```

M872 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## M871 Blocker

M870 did not fail because target construction was absent:

```text
target_weak_seed_rows: 24
target_unique_left_seed_count: 3
retarget_candidate_rows: 96
pair_delta_sequence_rows: 1728
```

It failed because the retarget grid missed the accepted normal-branch window:

```text
normal_ok rows: 0 / 1728
normal_margin < 0.0: 1152 rows
normal_margin > 0.03: 576 rows
0.0 <= normal_margin <= 0.03: 0 rows
```

So the next implementation must not start with pair-delta replay. It must first
construct normal-branch accepted boundary rows for missing seeds.

## Design Principles

M873 must preserve the evidence contract:

```text
normal_success == true
normal_collision == false
0.0 <= normal_margin <= 0.03
```

M873 must not:

```text
lower accepted-row thresholds
count colliding-normal rows as pair-delta evidence
count too-safe rows as near-boundary evidence
train actor or residual-head parameters
run PPO
promote a checkpoint
```

The implementation should separate two stages with separate artifacts:

```text
Stage A: normal-boundary search
Stage B: pair-delta sequence replay on accepted normal-boundary rows only
```

## Stage A: Normal-Boundary Search

Inputs:

```text
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/target_weak_seed_rows.csv
runs/m864_v4_generated_boundary_refinement/combined_generated_boundary_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
```

Target seeds:

```text
78048
78055
78057
```

For each target pair, reconstruct the left and right temporal snapshots once.
Then evaluate normal closed-loop outcomes over boundary-preserving retarget
axes:

```text
obstacle_lateral_offset
obstacle_timing
obstacle_half_width
```

The grid must include the original target point:

```text
delta = 0.0
```

Then evaluate small signed deltas around it. M870 showed that coarse deltas can
jump directly from too-safe to colliding, so M873 should bracket and refine:

```text
1. run normal-only replay on initial deltas;
2. classify each point as accepted_window, wide_safe, collision_or_negative,
   nonfinite, or reconstruction_error;
3. when a wide_safe and collision_or_negative pair are adjacent on the same
   axis, run bounded bisection or interpolation refinement;
4. keep only accepted_window rows for pair-delta replay.
```

Suggested initial deltas:

```text
obstacle_lateral_offset: [-0.20, -0.10, -0.05, 0.0, 0.05, 0.10, 0.20]
obstacle_timing: [-1.00, -0.50, -0.25, 0.0, 0.25, 0.50]
obstacle_half_width: [-0.10, -0.05, 0.0, 0.05, 0.10, 0.20]
```

Suggested refinement:

```text
max_refine_iters: 8
target_margin_low: 0.0
target_margin_high: 0.03
preferred_margin: 0.005 to 0.02
```

Stage A artifacts:

```text
normal_boundary_trace_rows.csv
normal_boundary_candidate_rows.csv
normal_boundary_rejected_rows.csv
normal_boundary_summary.json
```

Stage A gates:

```text
normal_boundary_candidate_rows >= 24
normal_boundary_unique_left_seed_count >= 3
normal_boundary_unique_axis_count >= 2
normal_boundary_max_left_seed_dominance <= 0.50
```

If Stage A cannot produce accepted normal-window rows for at least three seeds,
M873 should stop and classify the result as normal-boundary-limited. It should
not run pair-delta replay on colliding-normal rows.

## Stage B: Pair-Delta Sequence Replay

Only Stage A accepted normal-boundary candidates may enter Stage B.

Directions:

```text
pair_delta_positive
pair_delta_negative
```

Replay grid:

```text
hold_steps: [6, 8, 10]
epsilon_l2: [0.075, 0.10, 0.125]
```

Primary accepted pair-delta criteria remain unchanged:

```text
normal_success == true
normal_collision == false
0.0 <= normal_margin <= 0.03
effective_delta_l2_mean >= 0.014
abs_margin_delta >= 0.01 or success/collision flip
```

Stage B artifacts:

```text
pair_delta_sequence_rows.csv
new_accepted_pair_delta_rows.csv
accepted_pair_delta_rows.csv
balanced_pair_delta_rows.csv
component_control_rows.csv
train_public_rows.csv
eval_public_rows.csv
source_holdout_public_rows.csv
diversity_summary.json
gate_summary.csv
summary.json
```

Component controls may run only after new accepted pair-delta rows exist and
must remain diagnostic-only.

## Gates

Primary construction gates:

```text
target_weak_seed_rows >= 24
normal_boundary_candidate_rows >= 24
normal_boundary_unique_left_seed_count >= 3
retarget_pair_delta_replay_rows > 0
```

Primary pair-delta gates:

```text
new_accepted_pair_delta_rows >= 24
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

Frozen-parameter gates:

```text
actor_checksum_unchanged == true
residual_head_checksum_unchanged == true
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

## Classification

M873 should distinguish:

```text
v4_boundary_preserving_missing_seed_pair_delta_refresh_pass
v4_boundary_preserving_missing_seed_pair_delta_refresh_source_limited
v4_boundary_preserving_missing_seed_pair_delta_refresh_normal_boundary_limited
v4_boundary_preserving_missing_seed_pair_delta_refresh_all_weak
v4_boundary_preserving_missing_seed_pair_delta_refresh_contract_violation
```

Important distinction:

```text
normal_boundary_limited:
  accepted normal-window rows cannot be constructed for missing seeds.

all_weak:
  accepted normal-window rows exist, but pair-delta sequence interventions do
  not change margin or outcome enough.

source_limited:
  some accepted pair-delta evidence exists, but diversity gates fail.
```

## Workflow Cadence

M873 may be implemented as the final targeted no-training implementation in
this branch window.

After M873:

```text
M874 must be branch synthesis before another narrow implementation.
```

This avoids turning the branch into repeated local retarget-grid iteration.

## Decision

Decision:

```text
boundary_preserving_missing_seed_pair_delta_refresh_design_admit_m873
```

Next:

```text
m873-v4-boundary-preserving-missing-seed-pair-delta-refresh-implementation
```
