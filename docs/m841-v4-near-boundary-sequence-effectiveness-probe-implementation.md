# M841 V4 Near-Boundary Sequence-Effectiveness Probe Implementation

## Purpose

M841 implements the M840 no-training short-horizon sequence-effectiveness probe.

The implementation question is:

```text
Can bounded short-horizon action-sequence overrides move terminal margin on the
M832 near-boundary pair set?
```

M841 does not train or promote anything:

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
src/autodrift/v4_near_boundary_sequence_effectiveness_probe.py
tests/test_v4_near_boundary_sequence_effectiveness_probe.py
```

The probe extends M838 from one-step override to short-horizon bounded deltas:

```text
action_t = clip(policy_action_t + direction_unit * epsilon)
```

for `hold_steps`, then normal frozen policy control resumes.

Hold steps:

```text
[2, 4, 6]
```

Directions:

```text
pair_delta_positive
pair_delta_negative
steer_positive
steer_negative
throttle_positive
throttle_negative
brake_positive
brake_negative
```

Per-step override grid:

```text
epsilon_l2_grid: [0.014, 0.025, 0.05, 0.075]
```

Direct sequence override evidence remains controllability-only. It is not
learned policy self-ID proof.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_near_boundary_sequence_effectiveness_probe \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --near-boundary-pairs runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv \
  --accepted-boundary-rows runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m841_v4_near_boundary_sequence_effectiveness_probe \
  --device cpu
```

## Artifacts

```text
runs/m841_v4_near_boundary_sequence_effectiveness_probe/summary.json
runs/m841_v4_near_boundary_sequence_effectiveness_probe/sequence_effectiveness_rows.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/accepted_sequence_effective_rows.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/best_sequence_by_pair.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/direction_hold_summary.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/diversity_summary.json
runs/m841_v4_near_boundary_sequence_effectiveness_probe/rejected_rows.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/gate_summary.csv
```

## Result

M841 completed successfully and preserved frozen parameters:

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
raw_pair_rows: 60
selected_pair_rows: 60
unique_snapshot_rows: 16
sequence_effectiveness_rows: 5760
rejected_rows: 0
```

Accepted rows:

```text
accepted_primary_sequence_effective_rows: 73
accepted_directional_degradation_rows: 65
accepted_directional_improvement_rows: 8
success_flip_rows: 59
collision_flip_rows: 59
```

Largest observed terminal-margin movement:

```text
max_abs_margin_delta:         0.015836925320356077
max_degradation_margin_delta: 0.015836925320356077
max_improvement_margin_delta: 0.014276799059869116
margin_delta_threshold:       0.01
```

Result class:

```text
v4_near_boundary_sequence_effectiveness_sparse_diagnostic
```

## Direction/Hold Summary

The effect appears only for longer holds:

```text
hold_steps=2: 0 accepted rows
hold_steps=4: accepted rows appear
hold_steps=6: strongest accepted rows
```

Strongest groups:

```text
throttle_positive hold=6:
  accepted_rows: 16
  max_abs_margin_delta: 0.015836925320356077

throttle_negative hold=6:
  accepted_rows: 16
  max_abs_margin_delta: 0.014276799059869116

pair_delta_negative hold=6:
  accepted_rows: 8
  max_abs_margin_delta: 0.009483282306206542

steer_positive hold=6:
  accepted_rows: 8
  max_abs_margin_delta: 0.004930068676409105
```

The primary gate count passes:

```text
primary_sequence_effective_rows: 73 >= 40
```

but the overall classification remains sparse because accepted rows are
source-concentrated:

```text
accepted unique_left_source_group_count: 4
required min_left_sources: 8
accepted unique_left_fault_family_count: 4
required min_fault_families: 5
accepted max_left_source_group_dominance: 0.5616
required max_source_dominance: 0.30
```

## Interpretation

M841 resolves the M838 ambiguity:

```text
The M832 states are not completely action-insensitive; they are weak for one
step but sensitive to sustained short-horizon action deltas.
```

This is important because it says the branch should not conclude that the data
route is dead. The useful control variable is sequence-level maneuver intent,
not one-step action drift.

However, M841 is not promotion-grade and not self-ID proof:

```text
direct sequence overrides are not learned policy behavior
accepted rows are source-concentrated
M832 pair set is still sparse
no PPO was run
no checkpoint was promoted
```

The next decision should be made by branch synthesis, not another narrow
implementation. The likely options are:

```text
1. build a source-diverse sequence-effective corpus;
2. design an outcome-coupled sequence objective using M841 positives as seed
   evidence;
3. pivot to fresh action-leverage boundary mining if the concentration is too
   severe.
```

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_near_boundary_sequence_effectiveness_probe.py
```

Result:

```text
3 passed
```

## Decision

Decision:

```text
v4_near_boundary_sequence_effectiveness_sparse_diagnostic
```

Next:

```text
m842-v4-low-margin-new-data-route-third-branch-synthesis
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, outcome-coupled objective training, and threshold relaxation remain
blocked until synthesis selects the next branch.
