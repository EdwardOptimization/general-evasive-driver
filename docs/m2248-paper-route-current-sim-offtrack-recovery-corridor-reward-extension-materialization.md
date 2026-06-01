# M2248 Paper-Route Current-Sim Offtrack/Recovery/Corridor Reward Extension Materialization

- status: completed
- decision: `current_sim_offtrack_recovery_corridor_reward_extension_materialization_pass_route_to_training_execution_design`
- manifest: `experiments/manifests/m2248-paper-route-current-sim-offtrack-recovery-corridor-reward-extension-materialization.json`
- command: `PYTHONPATH=src python -m autodrift.paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization --output-dir runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization`
- summary: `runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/summary.json`

## Implementation

M2248 added default-preserving road containment reward hooks:

```text
track_cost_scale
heading_cost_scale
road_margin_cost_scale
road_margin_warning_fraction
off_track_penalty
```

Default behavior is preserved:

```text
track_cost_scale: 2.4
heading_cost_scale: 0.25
road_margin_cost_scale: 0.0
road_margin_warning_fraction: 0.70
off_track_penalty: 0.0
```

The repaired config family explicitly enables:

```text
track_cost_scale: 2.8
road_margin_cost_scale: 1.2
road_margin_warning_fraction: 0.65
off_track_penalty: 6.0
dense_clearance_margin_reward_scale: 0.5
dense_clearance_margin_reward_window: 10.0
clearance_margin_reward_scale: 1.0
collision_penalty: 25.0
track_width: 8.5
```

`off_track_penalty` is separate from generic `termination_penalty`, so future
audits can distinguish road-departure pressure from all other terminations.

## Tests

Focused tests passed:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization.py \
  tests/test_env.py

42 passed
```

## Materialization Result

```text
result_class: current_sim_offtrack_recovery_corridor_reward_extension_materialization_pass
materialized_config_count: 15
training_matrix_row_count: 15
profile_set_matched: true
seed_set_matched: true
budget_signature_count: 1
contract_violation_count: 0
track_width_widened_count: 0
guardrail_violation_count: 0
```

Artifacts:

```text
runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/summary.json
runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/training_matrix.csv
runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/claim_boundary.csv
runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/configs/
```

## Claim Boundary

Allowed claim:

```text
The project now has default-preserving road-containment reward hooks and a
matched 15-config repaired profile/seed matrix.
```

Still blocked:

```text
training result
selected checkpoint result
selected-checkpoint outcome localization result after repair
controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
```

## Next

Pre-register execution design:

```text
m2249-paper-route-current-sim-offtrack-recovery-corridor-training-execution-design
```

M2249 should design a controlled training execution that reuses the M2241
candidate-checkpoint runner over the M2248 training matrix. It should not start
training in the design milestone.
