# M843 V4 Source-Diverse Sequence-Effective Corpus Design

## Purpose

M843 designs the next no-training data route after M842 synthesized M832-M841.

The design question is:

```text
Can M841's sparse-positive sequence-effectiveness signal be expanded into a
source-diverse corpus before objective design or PPO?
```

M843 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Motivation

M841 showed that sequence-level controllability exists:

```text
accepted_primary_sequence_effective_rows: 73
accepted_directional_degradation_rows: 65
accepted_directional_improvement_rows: 8
success_flip_rows: 59
collision_flip_rows: 59
max_abs_margin_delta: 0.0158369
```

But the evidence is too concentrated:

```text
unique_left_source_group_count: 4 < 8
unique_left_fault_family_count: 4 < 5
max_left_source_group_dominance: 0.5616 > 0.30
```

So the next step should not be PPO or outcome objective training. It should be
a broader source-diverse corpus refresh that uses the M841 sequence-effective
probe as a filter.

## Actor Contract

The actor contract remains P0 human-view. The corpus refresh may use simulator
metadata for mining and labeling, but deployable actor input must not change:

```text
no hidden parameters as actor input
no fault labels as actor input
no oracle feasibility as actor input
no TTC or reference-path errors as actor input
no slip or tire-force actor channels
no controller mode
```

Direct sequence override rows are diagnostics and future training/evaluation
surface candidates. They are not learned self-ID proof.

## Data Sources

M844 should use:

```text
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/accepted_sequence_effective_rows.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/direction_hold_summary.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

M844 should not require new actor checkpoints or PPO outputs.

## Corpus Construction

M844 should build a broader sequence-effective corpus in three stages.

### Stage A: Source-Diverse Candidate Selection

Select candidate source snapshots from M825/M832 with hard balance targets:

```text
seeds
source_group_id
fault_family
fault_family_pair
warmup_mode
onset_bucket
fidelity_class
boundary_axis
margin_band
```

Use M841 accepted rows as seed evidence, but do not only replay their source
groups. The purpose is to escape M841's source concentration.

Candidate limits should prevent one source family from dominating:

```text
max_candidates_per_left_seed: 64
max_candidates_per_left_source_group: 24
max_candidates_per_left_fault_family: 96
max_candidates_per_fault_pair: 48
max_candidates_per_warmup_pair: 96
```

### Stage B: Near-Boundary Bracketing Or Reuse

For sources already represented in M832 accepted boundary rows, reuse the
existing near-boundary relocation.

For underrepresented sources, M844 may run the M832 boundary bracketing logic
again, but only as no-training data construction:

```text
boundary_margin_threshold: 0.05
strict_margin_threshold: 0.02
ultra_strict_margin_threshold: 0.005
boundary_axes:
  obstacle_lateral_offset
  obstacle_timing
  obstacle_half_width
```

If bracketing fails, keep rejected rows with the rejection reason. Do not relax
thresholds after seeing results.

### Stage C: Sequence-Effectiveness Scan

Replay bounded sequence overrides using the M841 semantics:

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

`hold_steps=2` can be omitted from the primary scan because M841 found zero
accepted rows there. It may remain as a small diagnostic sample if runtime is
acceptable.

For pair-delta directions, use matched right-source first action when a
source-diverse pair exists. For unpaired sources, component directions are
sufficient and pair-delta rows should be marked `pair_delta_unavailable`.

## Accepted Row Classes

Primary sequence-effective rows:

```text
normal_collision == false
normal_margin <= 0.05
effective_delta_l2_mean >= 0.014
abs_margin_delta >= 0.01
or success_flip == true
or collision_flip == true
```

Separate:

```text
directional_degradation
directional_improvement
outcome_flip
mitigation_sequence
```

Mitigation rows should be retained separately if both normal and sequence rows
collide but finite margin worsens or improves by:

```text
abs_margin_delta >= 0.02
```

Mitigation rows are diagnostics, not primary self-ID proof.

## Source-Diversity Gates

Strong corpus gate:

```text
accepted_primary_sequence_effective_rows >= 120
unique_left_source_group_count >= 10
unique_left_seed_count >= 4
unique_left_fault_family_count >= 5
unique_fault_family_pair_count >= 8
unique_warmup_pair_count >= 3
unique_onset_pair_count >= 5
unique_hold_steps_count >= 2
unique_direction_family_count >= 3
max_left_source_group_dominance <= 0.30
max_left_seed_dominance <= 0.35
max_direction_family_dominance <= 0.55
```

Sparse-positive gate:

```text
40 <= accepted_primary_sequence_effective_rows < 120
and unique_left_source_group_count >= 6
and unique_fault_family_pair_count >= 5
```

All-weak gate:

```text
accepted_primary_sequence_effective_rows < 40
or max_abs_margin_delta < 0.01
and no success/collision flips
```

## Split Discipline

M844 should produce source-aware splits for later objective design:

```text
train_public
eval_public
source_holdout_public
```

The source holdout must split by source group or seed, not by row, so later
objectives cannot simply memorize M841-style source patterns.

Private holdout remains promotion-only and should not be used for this corpus
refresh.

## Required M844 Artifacts

M844 should write:

```text
src/autodrift/v4_source_diverse_sequence_effective_corpus.py
tests/test_v4_source_diverse_sequence_effective_corpus.py
runs/m844_v4_source_diverse_sequence_effective_corpus/summary.json
runs/m844_v4_source_diverse_sequence_effective_corpus/candidate_source_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/boundary_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/sequence_effective_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/accepted_sequence_effective_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/train_public_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/eval_public_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/source_holdout_public_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/diversity_summary.json
runs/m844_v4_source_diverse_sequence_effective_corpus/rejected_rows.csv
docs/m844-v4-source-diverse-sequence-effective-corpus-implementation.md
```

The summary must include:

```text
result_class
candidate_source_rows
boundary_rows
sequence_effective_rows
accepted_primary_sequence_effective_rows
accepted_directional_degradation_rows
accepted_directional_improvement_rows
train_public_rows
eval_public_rows
source_holdout_public_rows
unique_left_source_group_count
unique_left_seed_count
unique_left_fault_family_count
unique_fault_family_pair_count
max_left_source_group_dominance
actor_backbone_changed
residual_head_changed
training_started
optimizer_started
ppo_used
promoted
checkpoint_promoted
```

## Recommended M844 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_source_diverse_sequence_effective_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --accepted-boundary-rows runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv \
  --seed-sequence-positive-rows runs/m841_v4_near_boundary_sequence_effectiveness_probe/accepted_sequence_effective_rows.csv \
  --run-dir runs/m844_v4_source_diverse_sequence_effective_corpus \
  --device cpu
```

## Decision Logic

If M844 reaches the strong corpus gate:

```text
audit -> outcome-coupled sequence objective design
```

If M844 reaches only sparse-positive:

```text
audit -> decide whether to expand source generation or design a restricted
objective sanity probe
```

If M844 is all-weak:

```text
audit -> pivot to fresh action-leverage boundary mining or richer scenario
distribution
```

No PPO or checkpoint promotion is admitted directly by M844.

## Decision

Decision:

```text
source_diverse_sequence_effective_corpus_design_admit_m844
```

Next:

```text
m844-v4-source-diverse-sequence-effective-corpus-implementation
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and outcome-coupled objective training remain blocked.
