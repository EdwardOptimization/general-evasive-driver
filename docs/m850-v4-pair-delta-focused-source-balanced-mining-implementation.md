# M850 V4 Pair-Delta-Focused Source-Balanced Mining Implementation

## Purpose

M850 implements the M849 no-training pair-delta-first miner.

The implementation question is:

```text
Can scanning pair-delta outcomes first broaden M847's accepted pair-delta
evidence before objective training?
```

M850 does not train or promote anything:

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
src/autodrift/v4_pair_delta_focused_source_balanced_mining.py
tests/test_v4_pair_delta_focused_source_balanced_mining.py
```

The runner starts from M847 pair candidates, hydrates them with M844 boundary
plans, and replays only pair-delta directions first:

```text
directions:
  pair_delta_positive
  pair_delta_negative

hold_steps_grid: [4, 6]
epsilon_l2_grid: [0.025, 0.05, 0.075]
```

Component directions are replayed only as controls for balanced pair-delta
candidate pairs. They cannot satisfy the primary M850 gates.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_pair_delta_focused_source_balanced_mining \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --pair-candidate-rows runs/m847_v4_cross_source_sequence_effective_pair_refresh/pair_candidate_rows.csv \
  --boundary-rows runs/m844_v4_source_diverse_sequence_effective_corpus/boundary_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m850_v4_pair_delta_focused_source_balanced_mining \
  --device cpu
```

## Artifacts

```text
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

## Result

M850 completed successfully and preserved frozen parameters:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Pair-delta replay:

```text
pair_candidate_rows_count: 208
replay_pair_rows: 160
reconstructed_pair_rows: 160
pair_delta_sequence_rows: 1920
accepted_pair_delta_rows: 50
balanced_pair_delta_rows: 24
component_control_rows: 396
```

Compared with M847:

```text
M847 accepted_pair_delta_rows: 17
M850 accepted_pair_delta_rows: 50
```

M850 therefore improves raw pair-delta yield.

Result class:

```text
v4_pair_delta_focused_source_balanced_mining_source_limited
```

## Gate Summary

Passed:

```text
accepted_pair_delta_rows: 50 >= 30
actor/residual checksums unchanged
PPO blocked
```

Failed:

```text
balanced_pair_delta_rows: 24 < 30
balanced_unique_left_source_group_count: 3 < 8
balanced_unique_left_seed_count: 2 < 4
balanced_unique_left_fault_family_count: 3 < 5
balanced_unique_fault_family_pair_count: 6 < 10
balanced_max_left_source_group_dominance: 0.3333 > 0.30
balanced_max_left_seed_dominance: 0.6667 > 0.35
balanced_max_direction_dominance: 0.6667 > 0.60
```

## Pair-Delta Audit

Accepted pair-delta rows:

```text
pair_delta_negative: 31
pair_delta_positive: 19
hold_steps=6: 28
hold_steps=4: 22
```

But the positives remain concentrated:

```text
left_source_group_id 41: 18
left_source_group_id 47: 16
left_source_group_id 35: 13
left_source_group_id 59: 3

left_seed 78059: 32
left_seed 78053: 18
```

After balancing:

```text
balanced_pair_delta_rows: 24
source_holdout_public_rows: 0
```

The zero source-holdout count is expected from only three balanced left source
groups, but it means the corpus is not objective-ready.

## Interpretation

M850 is a useful positive-but-limited result:

```text
pair-delta evidence is real and more plentiful than M847 showed;
the current candidate surface still concentrates pair-delta positives in a few
sources and seeds;
the next blocker is data coverage, not objective design.
```

The strongest next route is likely expanded boundary bracketing over
underrepresented source/fault families, then another pair-delta-focused mining
pass.

## Tests

Focused tests:

```text
python -m compileall -q src/autodrift/v4_pair_delta_focused_source_balanced_mining.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_pair_delta_focused_source_balanced_mining.py
```

Result:

```text
3 passed
```

## Decision

Decision:

```text
v4_pair_delta_focused_source_balanced_mining_source_limited
```

Next:

```text
m851-v4-pair-delta-focused-source-balanced-mining-audit
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and outcome-coupled objective training remain blocked.
