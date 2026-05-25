# M838 V4 Near-Boundary Action-Effectiveness Probe Implementation

## Purpose

M838 implements the M837 no-training direct first-action override probe.

The implementation question is:

```text
Can bounded first-step action changes move terminal margin on the M832
near-boundary pair set?
```

M838 does not train or promote anything:

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
src/autodrift/v4_near_boundary_action_effectiveness_probe.py
tests/test_v4_near_boundary_action_effectiveness_probe.py
```

The probe reuses the M835/M832 reconstruction path:

```text
runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv
runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
```

For each near-boundary pair, M838 relocates the left environment, computes the
normal M568/M761 first action, applies one bounded first-step override, and
then resumes normal closed-loop policy control.

Override directions:

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

Override magnitudes:

```text
epsilon_l2_grid: [0.014, 0.025, 0.05, 0.075]
```

This is a direct controllability diagnostic. It is not policy self-ID proof.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_near_boundary_action_effectiveness_probe \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --near-boundary-pairs runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv \
  --accepted-boundary-rows runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m838_v4_near_boundary_action_effectiveness_probe \
  --device cpu
```

## Artifacts

```text
runs/m838_v4_near_boundary_action_effectiveness_probe/summary.json
runs/m838_v4_near_boundary_action_effectiveness_probe/action_effectiveness_rows.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/accepted_action_effective_rows.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/best_direction_by_pair.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/direction_summary.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/diversity_summary.json
runs/m838_v4_near_boundary_action_effectiveness_probe/rejected_rows.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/gate_summary.csv
```

## Result

M838 completed successfully and preserved frozen parameters:

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
action_effectiveness_rows: 1920
rejected_rows: 0
```

Accepted rows:

```text
accepted_primary_action_effective_rows: 0
accepted_directional_degradation_rows: 0
accepted_directional_improvement_rows: 0
success_flip_rows: 0
collision_flip_rows: 0
```

Largest observed terminal-margin movement:

```text
max_abs_margin_delta: 0.002649502705148077
max_degradation_margin_delta: 0.002649502705148077
max_improvement_margin_delta: 0.002591099447261991
margin_delta_threshold: 0.01
```

Result class:

```text
v4_near_boundary_action_effectiveness_first_step_insensitive
```

## Direction Summary

No direction family reached the `0.01` margin-delta gate or produced a
success/collision flip.

Best direction maxima:

```text
throttle_positive max_abs_margin_delta:    0.002649502705148077
throttle_negative max_abs_margin_delta:    0.002591099447261991
pair_delta_negative max_abs_margin_delta:  0.0016304800420747778
pair_delta_positive max_abs_margin_delta:  0.0015691361193552744
steer_negative max_abs_margin_delta:       0.001527237539624915
steer_positive max_abs_margin_delta:       0.0013722334854635587
brake_negative max_abs_margin_delta:       0.0009930399851543203
brake_positive max_abs_margin_delta:       0.0009844319916982869
```

Every direction had:

```text
rows: 240
accepted_rows: 0
success_flip_rows: 0
collision_flip_rows: 0
severe_clip_rows: 0
max_effective_delta_l2: 0.075
```

## Interpretation

M838 rules out another narrow explanation of M835:

```text
M835 was not all-weak simply because the wrong-history counterfactual failed to
move the first action enough.
```

Here, direct overrides move the first action by up to `0.075` L2, but terminal
margin still moves by at most `0.00265`, far below the `0.01` threshold.

This means the M832 near-boundary pair set is not a good first-step
action-effectiveness surface for outcome-coupled self-ID objectives. More
hidden/response variants on this exact first-step setup are unlikely to be the
highest-leverage next action.

This does not prove the driver problem is impossible. It shows that the current
M832 pair states need either:

```text
short-horizon action-sequence effectiveness testing
or fresh boundary mining focused on states with stronger local action leverage
```

before PPO or outcome-coupled objectives.

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_near_boundary_action_effectiveness_probe.py
```

Result:

```text
4 passed
```

## Decision

Decision:

```text
v4_near_boundary_action_effectiveness_first_step_insensitive
```

Next:

```text
m839-v4-near-boundary-action-effectiveness-probe-audit
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, outcome-coupled objective training, and threshold relaxation remain
blocked until the audit decides the next branch.
