# M873 V4 Boundary-Preserving Missing-Seed Pair-Delta Refresh Implementation

## Purpose

M873 implements the M872 no-training boundary-preserving refresh.

The implementation question is:

```text
If we first force missing-seed retargets back into the accepted normal-branch
margin window, can we recover source-diverse pair-delta outcome evidence?
```

M873 is no-training:

```text
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_boundary_preserving_missing_seed_pair_delta_refresh \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --target-weak-seed-rows runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/target_weak_seed_rows.csv \
  --combined-boundary-rows runs/m864_v4_generated_boundary_refinement/combined_generated_boundary_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --existing-accepted-pair-delta-rows runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/accepted_pair_delta_rows.csv \
  --run-dir runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh \
  --device cpu
```

## Implementation

M873 adds:

```text
src/autodrift/v4_boundary_preserving_missing_seed_pair_delta_refresh.py
tests/test_v4_boundary_preserving_missing_seed_pair_delta_refresh.py
```

The runner separates the two evidence stages:

```text
Stage A:
  normal-only boundary search over missing seeds.

Stage B:
  pair-delta sequence replay only on accepted normal-window candidates.
```

Stage A includes the original target point and bounded retarget axes:

```text
obstacle_lateral_offset
obstacle_timing
obstacle_half_width
```

Only rows satisfying the accepted normal-branch contract enter Stage B:

```text
normal_success == true
normal_collision == false
0.0 <= normal_margin <= 0.03
```

## Result

M873 completed cleanly:

```text
result_class: v4_boundary_preserving_missing_seed_pair_delta_refresh_pass
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Stage A fixed the M870 normal-window miss:

```text
normal_boundary_trace_rows: 304
normal_boundary_candidate_rows: 48
normal_boundary_unique_left_seed_count: 3
normal_boundary_unique_retarget_axis_count: 3
normal_boundary_max_left_seed_dominance: 0.5
```

Trace classification:

```text
accepted_window: 48
wide_safe: 112
collision_or_negative: 144
```

By seed:

```text
78048 accepted_window: 15
78055 accepted_window: 24
78057 accepted_window: 9
```

Stage B found new pair-delta outcome evidence:

```text
pair_delta_candidate_rows: 48
pair_delta_sequence_rows: 864
new_accepted_pair_delta_rows: 39
new_accepted_unique_left_seed_count: 2
new accepted seeds:
  78057: 30
  78048: 9
```

The combined balanced corpus now passes the registered coverage gates:

```text
accepted_pair_delta_rows: 273
balanced_pair_delta_rows: 56
balanced_unique_left_seed_count: 4
balanced_unique_left_source_group_count: 11
balanced_unique_left_fault_family_count: 8
balanced_unique_fault_family_pair_count: 27
balanced_unique_direction_count: 2
balanced_unique_axis_pair_count: 2
balanced_max_left_seed_dominance: 0.35714285714285715
balanced_max_direction_dominance: 0.5178571428571429
balanced_max_axis_pair_dominance: 0.6607142857142857
```

## Important Caveat

M873 passes the registered M872/M873 gates, but the result is not a promotion
claim.

The new accepted rows cover two of the three missing seeds:

```text
new_accepted_unique_left_seed_count: 2
missing-seed accepted rows:
  78048: 9
  78057: 30
  78055: 0
```

The balanced combined corpus reaches four left seeds because it includes
existing accepted evidence from M867/M870:

```text
balanced seeds:
  78058: 20
  78050: 20
  78048: 8
  78057: 8
```

So the supported claim is:

```text
boundary-preserving refresh converts M870's normal-window miss into real
additional pair-delta evidence and a source-diverse combined corpus.
```

The unsupported claim is:

```text
all three missing seeds now produce new accepted pair-delta rows.
```

## Gate Summary

```text
actor_checksum_unchanged: pass
residual_head_checksum_unchanged: pass
normal_boundary_candidate_rows: pass
normal_boundary_seed_diversity: pass
new_accepted_pair_delta_rows: pass
balanced_left_seed_diversity: pass
ppo_blocked: pass
```

## Interpretation

Supported claims:

```text
M873 fixes the exact M870 failure mode by adding an accepted normal-boundary
search before pair-delta replay.
Accepted normal-window rows can be found for all three missing seeds.
New accepted pair-delta rows can be produced from two missing seeds.
The combined accepted corpus is now materially more source-diverse than M867.
```

Unsupported claims:

```text
M873 admits objective training without audit or synthesis.
M873 proves learned self-identification.
M873 promotes a driver checkpoint.
M873 fully solves the missing-seed coverage gap.
Component controls count as primary evidence.
```

Failure taxonomy:

```text
scenario_sampling_failure:
  reduced but not eliminated; one missing seed has normal-boundary candidates
  but zero new accepted pair-delta rows.

metric_artifact:
  controlled by separating normal-boundary candidates from pair-delta evidence.

contract_violation:
  not observed.
```

## Decision

M873 is a positive no-training implementation result, but the branch must now
synthesize before any additional narrow implementation or objective design.

Decision:

```text
v4_boundary_preserving_missing_seed_pair_delta_refresh_pass
```

Next:

```text
m874-v4-pair-delta-boundary-expansion-second-branch-synthesis
```
