# M849 V4 Pair-Delta-Focused Source-Balanced Mining Design

## Purpose

M849 designs the next no-training data route after M848 audited M847 as real
pair-delta positive but source-concentrated.

The design question is:

```text
Can we mine pair-delta outcomes first, then balance accepted pair-delta rows by
source/fault/seed, instead of letting component-axis rows dominate the corpus?
```

M849 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Motivation

M847 found the first real pair-delta positives:

```text
pair_delta_sequence_rows: 912
accepted_pair_delta_rows: 17
accepted_primary_sequence_effective_rows: 145
```

But the pair-delta subset is narrow:

```text
pair-delta unique_left_source_group_count: 3
pair-delta unique_left_seed_count: 2
pair-delta unique_left_fault_family_count: 2
pair-delta max_left_source_group_dominance: 0.7059
```

The full accepted set is component-heavy:

```text
throttle_axis: 97
steer_axis:    21
pair_delta:    17
brake_axis:    10
```

So M850 should not simply rerun M847 or design an objective over the component
heavy accepted corpus. It should mine pair-delta first.

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

Pair-delta sequence rows are still direct intervention diagnostics. They are
not learned self-ID proof.

## Data Sources

M850 should use:

```text
runs/m847_v4_cross_source_sequence_effective_pair_refresh/pair_candidate_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/accepted_pair_delta_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/accepted_sequence_effective_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/boundary_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

M850 should start from `pair_candidate_rows.csv`, not only from M847's balanced
rows, because M847 accepted pair-delta rows were source-concentrated after the
first balancing pass.

## Mining Stages

### Stage A: Pair-Delta Candidate Replay

Replay pair-delta directions for the broader candidate surface:

```text
directions:
  pair_delta_positive
  pair_delta_negative

hold_steps_grid: [4, 6]
epsilon_l2_grid: [0.025, 0.05, 0.075]
```

Primary M850 should not scan component directions at this stage. This prevents
component-axis rows from satisfying pair-delta gates.

Candidate limits:

```text
max_pair_candidates: 208
max_replay_pairs: 160
max_pairs_per_left_source_group: 24
max_pairs_per_right_source_group: 24
max_pairs_per_left_seed: 64
max_pairs_per_fault_family_pair: 32
```

M850 may optionally increase `max_obstacle_distance` to `0.20` only if it
regenerates candidates from M844 boundary rows. This must be reported as a
separate candidate source, not silently mixed with M847 candidates.

### Stage B: Pair-Delta Acceptance

Accepted pair-delta rows:

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

Keep degradation and improvement separate:

```text
pair_delta_degradation
pair_delta_improvement
pair_delta_outcome_flip
```

### Stage C: Source-Balanced Selection

After pair-delta acceptance, select a balanced public corpus:

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
```

### Stage D: Component Controls

Component directions may be replayed only as controls after a balanced
pair-delta subset exists:

```text
component_control_rows.csv
```

The component-control rows must not satisfy M850 primary gates. They answer:

```text
Is pair-delta evidence genuinely present, or is the state simply throttle/steer
sequence controllable?
```

## Gates

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
max_left_seed_dominance <= 0.35
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

## Split Discipline

M850 should write source-aware splits over the balanced pair-delta rows:

```text
train_public_rows.csv
eval_public_rows.csv
source_holdout_public_rows.csv
```

The split must be by source group or seed, not row-level random split.

Private holdout remains promotion-only.

## Required M850 Artifacts

M850 should write:

```text
src/autodrift/v4_pair_delta_focused_source_balanced_mining.py
tests/test_v4_pair_delta_focused_source_balanced_mining.py
runs/m850_v4_pair_delta_focused_source_balanced_mining/summary.json
runs/m850_v4_pair_delta_focused_source_balanced_mining/pair_delta_sequence_rows.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/accepted_pair_delta_rows.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/balanced_pair_delta_rows.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/component_control_rows.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/train_public_rows.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/eval_public_rows.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/source_holdout_public_rows.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/diversity_summary.json
runs/m850_v4_pair_delta_focused_source_balanced_mining/gate_summary.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/rejected_rows.csv
```

## Interpretation Rules

If M850 returns a strong pair-delta corpus:

```text
audit first, then design objective sanity without PPO
```

If M850 returns sparse pair-delta positive:

```text
audit first, then decide between restricted objective sanity and expanded
boundary bracketing
```

If M850 remains source-limited:

```text
design expanded boundary bracketing for underrepresented sources
```

If M850 is all-weak:

```text
synthesize before continuing this branch
```

## Decision

Decision:

```text
pair_delta_focused_source_balanced_mining_design_admit_m850
```

Next:

```text
m850-v4-pair-delta-focused-source-balanced-mining-implementation
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and outcome-coupled objective training remain blocked.
