# M846 V4 Cross-Source Sequence-Effective Pair Refresh Design

## Purpose

M846 designs the next no-training data route after M845 audited M844 as useful
but still source-limited.

The design question is:

```text
Can we build real cross-source near-boundary pairs so pair-delta sequence
directions can be tested, instead of only self-pair component directions?
```

M846 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Motivation

M844 improved M841 source coverage:

```text
M841 accepted unique_left_source_group_count: 4
M844 accepted unique_left_source_group_count: 10

M841 max_left_source_group_dominance: 0.5616
M844 max_left_source_group_dominance: 0.2807
```

But M844 remains below strong corpus quality:

```text
accepted_primary_sequence_effective_rows: 57 < 120
unique_left_seed_count: 3 < 4
unique_left_fault_family_count: 4 < 5
unique_fault_family_pair_count: 4 < 8
```

The main structural gap is:

```text
pair_delta_positive rows: 0
pair_delta_negative rows: 0
```

That happened because M844 used self-pair boundary states to broaden source
coverage. The next implementation should use real cross-source pairs.

## Actor Contract

The actor remains P0 human-view. The implementation may use simulator metadata
for corpus construction and labeling, but deployed actor input must not change:

```text
no hidden parameters as actor input
no fault labels as actor input
no oracle feasibility or controller mode
no TTC, reference-path errors, or required-clearance answers
no slip, tire force, or friction-margin channels
```

Pair-delta sequence rows are diagnostics and possible future training/eval
surfaces. They are not learned self-ID proof by themselves.

## Data Sources

M847 should use:

```text
runs/m844_v4_source_diverse_sequence_effective_corpus/boundary_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/reconstructed_snapshot_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/accepted_sequence_effective_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/accepted_sequence_effective_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

M847 should prefer the already reconstructed M844 snapshots when possible. If a
candidate pair needs a missing snapshot, it may reconstruct it using the same
deterministic replay code path, but must report reconstruction failures.

## Pair Construction

M847 should build pairs from near-boundary rows, not from already accepted
sequence rows only.

### Stage A: Boundary Pool

Start from:

```text
M844 boundary_rows: 39
M844 reconstructed_snapshot_rows: 20
```

Keep metadata needed for pairing:

```text
source_group_id
seed
snapshot_uid
step
warmup_mode
preferred_fault_family
wrong_fault_family
fault_family_pair
fault_onset_bucket
boundary_axis
parameter_value
normal_margin
first_action
ego response summary
obstacle geometry summary
```

Rows with missing replay snapshots should be marked, not silently dropped.

### Stage B: Cross-Source Pair Candidates

Create ordered left/right pairs with these hard requirements:

```text
left_source_group_id != right_source_group_id
left_snapshot_uid != right_snapshot_uid
left_normal_margin <= 0.05
right_normal_margin <= 0.05
first_action_l2(left, right) >= 0.014
```

At least one of these should hold:

```text
left_preferred_fault_family != right_preferred_fault_family
left_fault_family_pair != right_fault_family_pair
left_seed != right_seed
```

Use soft ranking terms, not hard shortcut labels, for:

```text
ego_response_distance
obstacle_geometry_distance
normal_margin_gap_abs
source_group rarity
fault_family rarity
seed rarity
```

The ranking should prefer:

```text
small geometry distance
small ego-response distance
low normal margin on both sides
larger first-action divergence
underrepresented seeds and fault families
```

### Stage C: Pair Balance

Apply source-aware caps:

```text
max_pairs_per_left_source_group: 12
max_pairs_per_right_source_group: 12
max_pairs_per_left_seed: 32
max_pairs_per_fault_family_pair: 24
max_pairs_per_left_fault_family: 40
```

Target pair surface:

```text
paired_candidate_rows >= 80
unique_left_source_group_count >= 10
unique_left_seed_count >= 4
unique_left_fault_family_count >= 5
unique_fault_family_pair_count >= 6
```

If fewer than `40` paired candidates survive, M847 should classify the result as
`cross_source_pair_construction_failed` and route to expanded boundary
bracketing, not objective design.

## Sequence Scan

M847 should replay bounded sequence overrides using the M841/M844 semantics:

```text
hold_steps_grid: [4, 6]
epsilon_l2_grid: [0.025, 0.05, 0.075]
directions:
  pair_delta_positive
  pair_delta_negative
  steer_positive
  steer_negative
  throttle_positive
  throttle_negative
  brake_positive
  brake_negative
```

Pair-delta directions are mandatory for the paired rows:

```text
pair_delta_positive: move left action sequence toward right first-action delta
pair_delta_negative: move left action sequence away from right first-action delta
```

Component directions remain controls. They answer whether the state is
sequence-controllable even if pair-delta is weak.

## Accepted Row Classes

Primary pair-delta sequence-effective rows:

```text
normal_collision == false
normal_margin <= 0.05
direction_family == pair_delta
effective_delta_l2_mean >= 0.014
abs_margin_delta >= 0.01
or success_flip == true
or collision_flip == true
```

Primary component sequence-effective rows use the same gate but with component
directions.

Keep separate classes:

```text
pair_delta_degradation
pair_delta_improvement
component_degradation
component_improvement
outcome_flip
mitigation_sequence
```

Mitigation rows should be retained separately if both normal and sequence rows
collide but finite margin moves by:

```text
abs_margin_delta >= 0.02
```

## Gates And Result Classes

Strong paired corpus:

```text
accepted_primary_sequence_effective_rows >= 120
accepted_pair_delta_sequence_effective_rows >= 30
unique_left_source_group_count >= 10
unique_left_seed_count >= 4
unique_left_fault_family_count >= 5
unique_fault_family_pair_count >= 8
unique_hold_steps_count >= 2
unique_direction_family_count >= 3
max_left_source_group_dominance <= 0.30
max_left_seed_dominance <= 0.35
max_direction_family_dominance <= 0.55
```

Sparse pair-positive:

```text
40 <= accepted_primary_sequence_effective_rows < 120
accepted_pair_delta_sequence_effective_rows >= 10
unique_left_source_group_count >= 6
unique_fault_family_pair_count >= 4
```

Component-only positive:

```text
accepted_primary_sequence_effective_rows >= 40
accepted_pair_delta_sequence_effective_rows < 10
```

All-weak:

```text
accepted_primary_sequence_effective_rows < 40
and max_abs_margin_delta < 0.01
and no success/collision flips
```

Pair-construction failed:

```text
paired_candidate_rows < 40
or reconstructed_pair_rows < 20
or pair_delta_sequence_rows == 0
```

## Split Discipline

M847 should write:

```text
train_public_rows.csv
eval_public_rows.csv
source_holdout_public_rows.csv
```

The split must be source-aware:

```text
source_holdout split by source_group_id or seed
no row-level random split
no same pair_id split across train/eval/holdout
```

Private holdout remains promotion-only and should not be used in M847.

## Required M847 Artifacts

M847 should write:

```text
src/autodrift/v4_cross_source_sequence_effective_pair_refresh.py
tests/test_v4_cross_source_sequence_effective_pair_refresh.py
runs/m847_v4_cross_source_sequence_effective_pair_refresh/summary.json
runs/m847_v4_cross_source_sequence_effective_pair_refresh/pair_candidate_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/balanced_pair_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/reconstructed_pair_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/sequence_effective_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/accepted_sequence_effective_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/accepted_pair_delta_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/train_public_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/eval_public_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/source_holdout_public_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/diversity_summary.json
runs/m847_v4_cross_source_sequence_effective_pair_refresh/gate_summary.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/rejected_rows.csv
```

## Interpretation Rules

If M847 returns a strong paired corpus:

```text
audit first, then design outcome-coupled sequence objective sanity
```

If M847 returns sparse pair-positive:

```text
audit first, then either expand boundary bracketing or restrict objective
sanity to pair-delta rows with source-heldout guard
```

If M847 returns component-only positive:

```text
do not train; audit whether pair construction or first-action delta matching is
the limiting factor
```

If M847 returns pair-construction failed:

```text
design expanded boundary bracketing over underrepresented source/fault families
```

If M847 returns all-weak:

```text
synthesize before further narrow continuation
```

## Decision

Decision:

```text
cross_source_sequence_effective_pair_refresh_design_admit_m847
```

Next:

```text
m847-v4-cross-source-sequence-effective-pair-refresh-implementation
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and outcome-coupled objective training remain blocked.
