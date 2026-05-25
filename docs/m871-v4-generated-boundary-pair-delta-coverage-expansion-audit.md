# M871 V4 Generated Boundary Pair-Delta Coverage Expansion Audit

## Purpose

M871 audits M870 before any further implementation, objective conversion, PPO,
or checkpoint promotion.

The audit question is:

```text
Did M870 fail because the coverage-expansion implementation was invalid, or
because the tested retarget grid did not preserve accepted normal-branch
boundary rows for the missing seeds?
```

M871 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Artifact Completeness

M870 produced the required implementation and run artifacts:

```text
src/autodrift/v4_generated_boundary_pair_delta_coverage_expansion.py
tests/test_v4_generated_boundary_pair_delta_coverage_expansion.py
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/summary.json
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/target_weak_seed_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/retarget_candidate_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/pair_delta_sequence_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/accepted_pair_delta_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/balanced_pair_delta_rows.csv
runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/gate_summary.csv
docs/m870-v4-generated-boundary-pair-delta-coverage-expansion-implementation.md
```

Frozen-parameter checks passed:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

So M870 is not a contract violation and not a training mutation.

## Construction Gates

The construction side worked:

```text
target_weak_seed_rows: 24
target_unique_left_seed_count: 3
retarget_candidate_rows: 96
retarget_replay_rows: 1728
pair_delta_sequence_rows: 1728
```

The missing seeds were all covered:

```text
left_seed 78048: 540 replay rows
left_seed 78055: 864 replay rows
left_seed 78057: 324 replay rows
```

This rules out a pure pair-construction failure.

## Accepted-Row Failure

M870 produced no new accepted pair-delta rows:

```text
new_accepted_pair_delta_rows: 0
accepted_pair_delta_rows: 234
balanced_pair_delta_rows: 40
balanced_unique_left_seed_count: 2
```

The accepted-row failure is explained by the normal-branch acceptance window.
Across all M870 retarget replay rows:

```text
total sequence rows: 1728
normal_ok rows: 0
action_ok rows: 1728
abs_margin_delta >= 0.01 rows: 375
normal_ok and abs_margin_delta >= 0.01 rows: 0
```

Normal margins split into:

```text
normal_margin < 0.0: 1152 rows
normal_margin > 0.03: 576 rows
0.0 <= normal_margin <= 0.03: 0 rows
```

So M870's retarget grid jumped over the accepted normal-margin window. It
created either already-colliding rows or too-safe rows, not accepted
near-boundary rows.

## Outcome Sensitivity Is Real But Non-Primary

M870 did find stronger retarget outcome sensitivity than M867 on missing seeds:

```text
left_seed 78048 max_abs_margin_delta: 0.01702356326209964
left_seed 78055 max_abs_margin_delta: 0.02197950390059522
left_seed 78057 max_abs_margin_delta: 0.015147514551133057
```

But the largest rows were not primary evidence because normal branch was already
colliding. Example:

```text
left_seed: 78055
retarget_axis: obstacle_timing
retarget_delta: -1.0
direction: pair_delta_positive
hold_steps: 10
epsilon_l2: 0.125
normal_margin: -0.05078698158278194
sequence_margin: -0.07276648548337716
normal_success: false
normal_collision: true
sequence_success: false
sequence_collision: true
```

This is a useful diagnostic, but it cannot be used as accepted pair-delta
corpus data without violating the evidence contract.

## Existing Accepted Rebalance

M870 improved the diagnostic balance of existing M867 accepted rows:

```text
M867 balanced_pair_delta_rows: 32
M870 existing_rebalanced_pair_delta_rows: 40
balanced_unique_left_source_group_count: 9
balanced_unique_left_fault_family_count: 6
balanced_unique_fault_family_pair_count: 24
balanced_unique_direction_count: 2
balanced_unique_axis_pair_count: 2
balanced_max_direction_dominance: 0.525
balanced_max_axis_pair_dominance: 0.525
```

This shows that part of M867's direction/axis dominance was a selection artifact.
It does not fix the main blocker because left-seed coverage remains:

```text
balanced_unique_left_seed_count: 2 < 3
balanced_max_left_seed_dominance: 0.5 > 0.45
```

## Interpretation

Supported claims:

```text
M870 is a clean no-training implementation.
Missing accepted seeds were targeted and replayed.
Existing accepted rows can be rebalanced for better direction/axis coverage.
The tested retarget grid does not produce accepted normal-window rows for
missing seeds.
Objective training and PPO remain blocked.
```

Unsupported claims:

```text
M870 is objective-ready.
M870 admits a pair-delta objective corpus.
M870 proves source-diverse self-ID pair-delta evidence.
High margin deltas on already-colliding normal rows can count as primary
evidence.
Lowering accepted-row thresholds is justified.
```

Failure taxonomy:

```text
scenario_sampling_failure:
  the tested retarget grid missed the accepted normal-margin window for all
  retarget rows.

metric_artifact:
  the largest abs_margin_delta rows come from already-colliding normal branches
  and cannot be treated as primary pair-delta evidence.

contract_violation:
  not observed.
```

## Decision

M871 rejects objective conversion from M870.

Decision:

```text
route_to_boundary_preserving_missing_seed_pair_delta_refresh_design
```

Next:

```text
m872-v4-boundary-preserving-missing-seed-pair-delta-refresh-design
```

The next design should not lower thresholds or train. It should first search or
refine retarget parameters so the normal branch is explicitly bracketed inside:

```text
normal_success == true
normal_collision == false
0.0 <= normal_margin <= 0.03
```

Only after that should it replay pair-delta sequence directions on the missing
seeds.
