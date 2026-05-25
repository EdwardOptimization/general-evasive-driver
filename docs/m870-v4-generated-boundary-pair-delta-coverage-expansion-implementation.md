# M870 V4 Generated Boundary Pair-Delta Coverage Expansion Implementation

## Purpose

M870 implements the M869 no-training accepted pair-delta coverage expansion.

The implementation question is:

```text
Can targeted retargeting and extended pair-delta replay add accepted
pair-delta rows for missing left seeds 78048, 78055, and 78057, while keeping
actor and M761 residual-head parameters frozen?
```

M870 is no-training:

```text
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_generated_boundary_pair_delta_coverage_expansion \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --m867-pair-delta-sequence-rows runs/m867_v4_generated_boundary_pair_delta_refresh/pair_delta_sequence_rows.csv \
  --m867-accepted-pair-delta-rows runs/m867_v4_generated_boundary_pair_delta_refresh/accepted_pair_delta_rows.csv \
  --m867-balanced-pair-delta-rows runs/m867_v4_generated_boundary_pair_delta_refresh/balanced_pair_delta_rows.csv \
  --combined-boundary-rows runs/m864_v4_generated_boundary_refinement/combined_generated_boundary_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m870_v4_generated_boundary_pair_delta_coverage_expansion \
  --device cpu
```

## Implementation

M870 adds:

```text
src/autodrift/v4_generated_boundary_pair_delta_coverage_expansion.py
tests/test_v4_generated_boundary_pair_delta_coverage_expansion.py
```

The runner:

```text
1. freezes the M568 actor and M761 residual head;
2. rebalances existing M867 accepted pair-delta rows with seed/direction/axis caps;
3. selects weak target rows for missing accepted seeds 78048, 78055, and 78057;
4. generates bounded obstacle lateral, timing, and half-width retargets;
5. replays pair_delta_positive and pair_delta_negative over hold steps 6, 8, 10
   and epsilon L2 0.075, 0.10, 0.125;
6. writes raw sequence rows, accepted rows, balanced rows, split rows, gate
   summaries, and diversity summaries.
```

Component controls are diagnostic-only. In this run no component controls were
needed because no new accepted pair-delta rows were produced.

## Result

The run completed cleanly:

```text
result_class: v4_generated_boundary_pair_delta_coverage_expansion_source_limited
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

Construction gates passed:

```text
target_weak_seed_rows: 24
target_unique_left_seed_count: 3
retarget_candidate_rows: 96
retarget_replay_rows: 1728
pair_delta_sequence_rows: 1728
```

Primary accepted-coverage gates did not pass:

```text
new_accepted_pair_delta_rows: 0
accepted_pair_delta_rows: 234
balanced_pair_delta_rows: 40
balanced_unique_left_seed_count: 2
balanced_unique_left_source_group_count: 9
balanced_unique_left_fault_family_count: 6
balanced_unique_fault_family_pair_count: 24
balanced_unique_direction_count: 2
balanced_unique_axis_pair_count: 2
balanced_max_left_seed_dominance: 0.5
balanced_max_direction_dominance: 0.525
balanced_max_axis_pair_dominance: 0.525
max_abs_margin_delta: 0.02197950390059522
```

The existing accepted rows rebalance better than M867's original balanced view:

```text
M867 balanced_pair_delta_rows: 32
M870 existing_rebalanced_pair_delta_rows: 40
M870 balanced direction dominance: 0.525
M870 balanced axis-pair dominance: 0.525
```

But accepted left-seed coverage remains unchanged:

```text
balanced_unique_left_seed_count: 2 < 3
```

## Missing-Seed Retarget Outcome

M870 successfully replayed all target missing seeds:

```text
left_seed 78048: 540 replay rows, max_abs_margin_delta 0.01702356326209964
left_seed 78055: 864 replay rows, max_abs_margin_delta 0.02197950390059522
left_seed 78057: 324 replay rows, max_abs_margin_delta 0.015147514551133057
```

However, none generated accepted rows:

```text
success_flip_rows: 0
collision_flip_rows: 0
new_accepted_pair_delta_rows: 0
```

The largest retarget effects came from obstacle timing moves that pushed the
normal branch into collision before the pair-delta intervention:

```text
left_seed: 78055
retarget_axis: obstacle_timing
retarget_delta: -1.0
direction: pair_delta_positive
hold_steps: 10
epsilon_l2: 0.125
normal_margin: -0.05078698158278194
sequence_margin: -0.07276648548337716
abs_margin_delta: 0.02197950390059522
normal_success: false
sequence_success: false
normal_collision: true
sequence_collision: true
```

This is real outcome sensitivity, but it is not accepted primary pair-delta
evidence because the accepted-row contract requires:

```text
normal_success == true
normal_collision == false
0.0 <= normal_margin <= boundary_margin_threshold
```

## Gate Summary

```text
actor_checksum_unchanged: pass
residual_head_checksum_unchanged: pass
target_weak_seed_rows: pass
retarget_candidate_rows: pass
balanced_left_seed_diversity: fail
balanced_pair_delta_rows: pass
ppo_blocked: pass
```

## Interpretation

Supported claims:

```text
M870 implements the M869 no-training coverage-expansion runner.
The missing seeds can be targeted and replayed cleanly.
Existing M867 accepted rows can be rebalanced to reduce direction and axis
dominance.
The source limitation is not fixed by the tested bounded retarget grid.
```

Unsupported claims:

```text
M870 is objective-ready.
M870 admits PPO.
M870 produces new accepted pair-delta rows.
M870 proves learned self-identification.
M870 justifies lowering accepted-row thresholds.
```

Failure taxonomy:

```text
scenario_sampling_failure:
  missing-seed retargets produced outcome sensitivity, but accepted rows remain
  concentrated in existing left seeds 78058 and 78050.

metric_artifact:
  high retarget max_abs_margin_delta appears on rows where the normal branch is
  already colliding, so it cannot count as primary pair-delta evidence.

contract_violation:
  not observed.
```

## Decision

M870 is a clean implementation result, but it remains source-limited.

Decision:

```text
v4_generated_boundary_pair_delta_coverage_expansion_source_limited
```

Next:

```text
m871-v4-generated-boundary-pair-delta-coverage-expansion-audit
```

M871 should audit whether the branch should continue with a broader
normal-branch boundary refresh for missing seeds, a retarget grid that brackets
accepted normal margins instead of forcing collisions, or a branch synthesis
before any further narrow implementation.
