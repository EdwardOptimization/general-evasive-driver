# M854 V4 Pair-Delta Boundary Expansion Implementation

## Purpose

M854 implements the M853 no-training boundary expansion over sources that were
absent or weak in M850 balanced pair-delta rows.

The implementation question is:

```text
Can underrepresented M825 source/fault/seed families produce a broader
successful non-collision low-margin boundary surface before another pair-delta
mining pass?
```

M854 is not a training milestone:

```text
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
no pair-delta sequence replay
```

## Implementation

Added:

```text
src/autodrift/v4_pair_delta_boundary_expansion.py
tests/test_v4_pair_delta_boundary_expansion.py
```

The runner selects source-group targets from M825 while excluding the M850
balanced active left source groups by default. It then reconstructs one snapshot
per selected source group and reuses the existing adaptive bracketing semantics
over:

```text
obstacle_lateral_offset
obstacle_timing
obstacle_half_width
```

Accepted boundary rows require:

```text
success == true
collision == false
0.0 <= min_clearance_margin <= 0.05
```

The pairability projection is a cheap data-quality diagnostic only. It uses
first-action L2 and obstacle-geometry distance. It does not execute pair-delta
sequence replay.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_pair_delta_boundary_expansion \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --existing-boundary-rows runs/m844_v4_source_diverse_sequence_effective_corpus/boundary_rows.csv \
  --balanced-pair-delta-rows runs/m850_v4_pair_delta_focused_source_balanced_mining/balanced_pair_delta_rows.csv \
  --run-dir runs/m854_v4_pair_delta_boundary_expansion \
  --device cpu
```

## Artifacts

```text
runs/m854_v4_pair_delta_boundary_expansion/summary.json
runs/m854_v4_pair_delta_boundary_expansion/target_source_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/reconstructed_snapshot_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/expanded_boundary_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/accepted_boundary_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/pairability_projection_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/boundary_diversity_summary.json
runs/m854_v4_pair_delta_boundary_expansion/gate_summary.csv
runs/m854_v4_pair_delta_boundary_expansion/rejected_rows.csv
```

## Result

M854 completed and preserved frozen parameters:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
pair_delta_sequence_replay_used: false
promoted: false
checkpoint_promoted: false
```

Target selection was broad:

```text
target_source_rows: 61
target_unique_source_group_count: 61
target_unique_seed_count: 12
target_unique_fault_family_count: 9
reconstructed_snapshot_rows: 61
snapshot_rejection_rows: 0
```

Boundary expansion was limited:

```text
expanded_boundary_rows: 73
accepted_boundary_rows: 32
new_underrepresented_boundary_rows: 32
unique_source_group_count: 17
unique_seed_count: 4
unique_fault_family_count: 7
unique_boundary_axis_count: 3
max_source_group_dominance: 0.09375
max_seed_dominance: 0.4375
```

Pairability projection was near but below sparse gate:

```text
pairability_projection_rows: 77
diagnostic_pairability_projection_rows: 125
projected_pairable_source_groups: 13
```

Result class:

```text
v4_pair_delta_boundary_expansion_source_limited
```

## Gate Summary

Passed:

```text
actor checksum unchanged
residual-head checksum unchanged
target_source_rows: 61 >= 48
pair_delta_sequence_replay_blocked: true
ppo_blocked: true
```

Failed strong gates:

```text
accepted_boundary_rows: 32 < 80
new_underrepresented_boundary_rows: 32 < 40
unique_source_group_count: 17 < 32
pairability_projection_rows: 77 < 160
```

Failed sparse gates:

```text
accepted_boundary_rows: 32 < 50
unique_source_group_count: 17 < 20
unique_seed_count: 4 < 6
pairability_projection_rows: 77 < 80
```

## Boundary Audit

The important detail is not just the row count. M854 targeted:

```text
boundary_new_to_m844 targets: 44
existing_boundary_recovered targets: 17
```

But accepted rows all came from existing M844 boundary sources:

```text
existing_boundary_recovered accepted rows: 32
boundary_new_to_m844 accepted rows: 0
```

All rejected rows were no-bracket failures:

```text
rejected_rows: 151
rejection_reason: no_collision_safe_bracket
```

So M854 did not simply choose the wrong source pool. It selected broad
underrepresented sources, reconstructed them successfully, and then failed to
find collision/success brackets for the sources that were new to M844 under the
current axis grid.

## Interpretation

M854 is a clean source-limited implementation result:

```text
target-source coverage is broad;
snapshot reconstruction works;
actor and residual-head contracts are preserved;
pairability projection is close to sparse-useful;
new-to-M844 boundary bracketing remains the blocker.
```

This supports an audit before another implementation. The next audit should
decide whether to:

```text
1. expand the bracketing axis/range specifically for boundary_new_to_m844 rows;
2. generate new source scenarios rather than only retargeting M825 sources;
3. run a limited pair-delta miner only over the recovered existing-boundary set
   as a diagnostic, not as a source-diverse claim.
```

Objective training, PPO, residual-head mutation, actor mutation, and promotion
remain blocked.

## Tests

Focused tests:

```bash
python -m compileall -q src/autodrift/v4_pair_delta_boundary_expansion.py tests/test_v4_pair_delta_boundary_expansion.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_v4_pair_delta_boundary_expansion.py \
  tests/test_v4_near_boundary_wrong_history_pair_mining.py \
  tests/test_v4_pair_delta_focused_source_balanced_mining.py
```

Result:

```text
9 passed
```

## Decision

Decision:

```text
v4_pair_delta_boundary_expansion_source_limited
```

Next:

```text
m855-v4-pair-delta-boundary-expansion-audit
```
