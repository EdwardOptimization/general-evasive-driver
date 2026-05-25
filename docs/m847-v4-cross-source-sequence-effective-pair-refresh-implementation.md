# M847 V4 Cross-Source Sequence-Effective Pair Refresh Implementation

## Purpose

M847 implements the M846 no-training real cross-source pair refresh.

The implementation question is:

```text
Can M844's source-diverse boundary surface produce real pair-delta
sequence-effectiveness rows?
```

M847 does not train or promote anything:

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
src/autodrift/v4_cross_source_sequence_effective_pair_refresh.py
tests/test_v4_cross_source_sequence_effective_pair_refresh.py
```

The runner builds ordered cross-source pairs from M844 boundary rows:

```text
left_source_group_id != right_source_group_id
first_action_l2 >= 0.014
obstacle_geometry_distance <= 0.10
left/right normal margins <= 0.05
```

It then reuses the M841 sequence replay semantics with mandatory pair-delta
directions:

```text
directions:
  pair_delta_positive
  pair_delta_negative
  steer_positive
  steer_negative
  throttle_positive
  throttle_negative
  brake_positive
  brake_negative

hold_steps_grid: [4, 6]
epsilon_l2_grid: [0.025, 0.05, 0.075]
```

An implementation bug was caught in the first run: `reconstructed_pair_rows`
was initially counting unique reconstructed snapshots, not replayable
left/right pairs. The final implementation counts pairs with both snapshots
available and writes the unique snapshots separately as
`reconstructed_snapshot_rows.csv`.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_cross_source_sequence_effective_pair_refresh \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --boundary-rows runs/m844_v4_source_diverse_sequence_effective_corpus/boundary_rows.csv \
  --reconstructed-snapshot-rows runs/m844_v4_source_diverse_sequence_effective_corpus/reconstructed_snapshot_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m847_v4_cross_source_sequence_effective_pair_refresh \
  --device cpu
```

## Artifacts

```text
runs/m847_v4_cross_source_sequence_effective_pair_refresh/summary.json
runs/m847_v4_cross_source_sequence_effective_pair_refresh/pair_candidate_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/balanced_pair_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/reconstructed_pair_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/reconstructed_snapshot_rows.csv
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

## Result

M847 completed successfully and preserved frozen parameters:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Pair construction:

```text
boundary_source_rows: 39
pair_candidate_rows: 208
paired_candidate_rows: 76
reconstructed_pair_rows: 76
reconstructed_snapshot_rows: 18
```

Sequence replay:

```text
sequence_effective_rows: 3648
pair_delta_sequence_rows: 912
accepted_primary_sequence_effective_rows: 145
accepted_pair_delta_sequence_effective_rows: 17
accepted_directional_degradation_rows: 125
accepted_directional_improvement_rows: 20
success_flip_rows: 115
collision_flip_rows: 115
```

Source-aware splits:

```text
train_public_rows: 79
eval_public_rows: 52
source_holdout_public_rows: 14
```

Result class:

```text
v4_cross_source_sequence_effective_pair_refresh_sparse_pair_positive
```

## Gate Summary

Passed:

```text
paired_candidate_rows: 76 >= 40
pair_delta_sequence_rows: 912 > 0
primary_sequence_effective_rows: 145 >= 120
actor/residual checksums unchanged
PPO blocked
```

Still failed:

```text
accepted_pair_delta_rows: 17 < 30
unique_left_source_group_count: 9 < 10
unique_left_seed_count: 3 < 4
unique_left_fault_family_count: 4 < 5
max_left_source_group_dominance: 0.3034 > 0.30
max_left_seed_dominance: 0.5517 > 0.35
max_direction_family_dominance: 0.6690 > 0.55
```

## Pair-Delta Audit

M847 fixes the structural gap from M844:

```text
M844 accepted_pair_delta_rows: 0
M847 accepted_pair_delta_rows: 17
```

But the accepted pair-delta subset is narrow:

```text
pair_delta_negative: 12
pair_delta_positive: 5
hold_steps=6: 9
hold_steps=4: 8
left_source_group_id 41: 12 / 17
left_fault_family global_mu_drop: 13 / 17
```

So M847 supports continuing with audit and refinement, not objective training.

## Interpretation

M847 is a positive data-route result:

```text
real cross-source pairing works;
pair-delta sequence evidence exists;
the pair-delta signal is still too concentrated;
component sequence effects remain stronger than pair-delta effects.
```

The next audit should decide whether to:

```text
1. refine the current pair-delta corpus with source/fault balancing;
2. expand boundary bracketing for underrepresented sources;
3. design a restricted pair-delta objective sanity only after a stronger audit;
4. synthesize if this branch is becoming another narrow corpus loop.
```

## Tests

Focused tests:

```text
python -m compileall -q src/autodrift/v4_cross_source_sequence_effective_pair_refresh.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_cross_source_sequence_effective_pair_refresh.py
```

Result:

```text
3 passed
```

## Decision

Decision:

```text
v4_cross_source_sequence_effective_pair_refresh_sparse_pair_positive
```

Next:

```text
m848-v4-cross-source-sequence-effective-pair-refresh-audit
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and outcome-coupled objective training remain blocked.
