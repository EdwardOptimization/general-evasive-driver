# M844 V4 Source-Diverse Sequence-Effective Corpus Implementation

## Purpose

M844 implements the M843 no-training source-diverse sequence-effective corpus
refresh.

The implementation question is:

```text
Can we broaden M841's sparse-positive sequence-effectiveness signal beyond the
four dominant source groups?
```

M844 does not train or promote anything:

```text
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Implementation

Added:

```text
src/autodrift/v4_source_diverse_sequence_effective_corpus.py
tests/test_v4_source_diverse_sequence_effective_corpus.py
```

The first M844 implementation reuses M832 accepted boundary rows as a broader
source surface:

```text
runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv
```

It builds self-pair rows from each accepted boundary row. That intentionally
makes pair-delta unavailable, but preserves component sequence directions and
expands coverage from the M841 accepted subset.

The scan uses:

```text
directions:
  steer_positive
  steer_negative
  throttle_positive
  throttle_negative
  brake_positive
  brake_negative

hold_steps_grid: [4, 6]
epsilon_l2_grid: [0.025, 0.05, 0.075]
```

This remains a direct sequence controllability diagnostic, not learned self-ID
proof.

## Command

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

## Artifacts

```text
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
runs/m844_v4_source_diverse_sequence_effective_corpus/gate_summary.csv
```

## Result

M844 completed successfully and preserved frozen parameters:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Run size:

```text
source_rows_count: 64
candidate_plan_rows_count: 512
seed_sequence_positive_rows_count: 73
candidate_source_rows: 39
boundary_rows: 39
reconstructed_snapshot_rows: 20
sequence_effective_rows: 1404
```

Accepted rows:

```text
accepted_primary_sequence_effective_rows: 57
accepted_directional_degradation_rows: 53
accepted_directional_improvement_rows: 4
success_flip_rows: 50
collision_flip_rows: 50
```

Source-aware splits:

```text
train_public_rows: 41
eval_public_rows: 11
source_holdout_public_rows: 5
```

Largest observed margin movement:

```text
max_abs_margin_delta:         0.015901665717227287
max_degradation_margin_delta: 0.015901665717227287
max_improvement_margin_delta: 0.01434756739876053
```

Result class:

```text
v4_source_diverse_sequence_effective_corpus_source_limited
```

## Diversity Audit

M844 improves source diversity over M841:

```text
M841 accepted unique_left_source_group_count: 4
M844 accepted unique_left_source_group_count: 10
```

But it remains below strong corpus requirements:

```text
accepted_primary_sequence_effective_rows: 57 < 120
unique_left_seed_count: 3 < 4
unique_left_fault_family_count: 4 < 5
unique_fault_family_pair_count: 4 < 8
max_left_seed_dominance: 0.4211 > 0.35
```

The source-group dominance target did pass:

```text
max_left_source_group_dominance: 0.2807 <= 0.30
```

This is an improvement, but not yet a strong corpus.

## Direction/Hold Summary

The strongest effects remain throttle-dominated:

```text
throttle_positive hold=6:
  accepted_rows: 11
  max_abs_margin_delta: 0.015901665717227287

throttle_negative hold=6:
  accepted_rows: 9
  max_abs_margin_delta: 0.01434756739876053

steer_negative hold=6:
  accepted_rows: 8
  max_abs_margin_delta: 0.010797898640881876
```

Pair-delta rows were unavailable in this self-pair implementation:

```text
pair_delta_positive rows: 0
pair_delta_negative rows: 0
```

That is expected for this first source-diverse refresh, but the audit should
decide whether the next refresh needs real cross-source pairing.

## Interpretation

M844 is useful but not sufficient:

```text
source coverage improved;
sequence controllability remains real;
fault/seed diversity is still too weak for objective training;
pair-delta evidence was not tested in this source-diverse refresh.
```

The result supports continuing data construction, not PPO.

The likely next choices are:

```text
1. expand boundary bracketing beyond the 39 existing accepted boundary rows;
2. build real cross-source sequence-effective pairs instead of self-pairs;
3. combine both before outcome-coupled objective design.
```

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_source_diverse_sequence_effective_corpus.py
```

Result:

```text
3 passed
```

## Decision

Decision:

```text
v4_source_diverse_sequence_effective_corpus_source_limited
```

Next:

```text
m845-v4-source-diverse-sequence-effective-corpus-audit
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and outcome-coupled objective training remain blocked.
