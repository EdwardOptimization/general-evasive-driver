# M2259 Paper-Route Current-Sim Midcourse Corridor-Containment Config Materialization

- status: completed
- decision: `current_sim_midcourse_corridor_containment_config_materialization_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2259-paper-route-current-sim-midcourse-corridor-containment-config-materialization.json`
- command: `PYTHONPATH=src python -m autodrift.paper_route_current_sim_midcourse_corridor_containment_config_materialization --output-dir runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs --next-blocker m2260-paper-route-current-sim-midcourse-corridor-containment-config-materialization-result-audit`
- summary: `runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/summary.json`

## Implementation

M2259 materializes the M2258 targeted containment repair as a matched
profile/seed config panel. It does not run reset, rollout, measured execution,
training, replay, PPO, private holdout, ranking, promotion, or policy actions.

Target shared reward values:

```text
track_cost_scale: 3.0
heading_cost_scale: 0.30
road_margin_cost_scale: 2.6
road_margin_warning_fraction: 0.50
off_track_penalty: 8.0
termination_penalty: 8.0
dense_clearance_margin_reward_scale: 0.5
dense_clearance_margin_reward_window: 10.0
clearance_margin_reward_scale: 1.0
clearance_margin_reward_clip: 0.25
collision_penalty: 25.0
```

Unchanged guardrails:

```text
track_width: 8.5
actor observation contract: P0_human_view_no_wheel_no_oracle
wheel_observation_mode: none
obstacle_relative_velocity_mode: zero
include_privileged_params: false
profile_specific_tuning: false
ranking_admissible: false
winner_selected: false
```

## Tests

Focused checks passed:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_midcourse_corridor_containment_config_materialization.py

python -m compileall -q src tests
git diff --check
```

Result:

```text
2 passed
```

## Materialization Result

```text
result_class: current_sim_midcourse_corridor_containment_config_materialization_pass
materialized_config_count: 15
training_matrix_row_count: 15
profile_set_matched: true
seed_set_matched: true
budget_signature_count: 1
contract_violation_count: 0
target_value_mismatch_count: 0
track_width_widened_count: 0
guardrail_violation_count: 0
```

Artifacts:

```text
runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/summary.json
runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/training_matrix.csv
runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/claim_boundary.csv
runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/configs/
```

## Claim Boundary

Allowed claim:

```text
The project now has a matched 15-config targeted midcourse
corridor-containment repair panel preserving the actor contract and road
geometry.
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

Pre-register and run a materialization result audit:

```text
m2260-paper-route-current-sim-midcourse-corridor-containment-config-materialization-result-audit
```

M2260 should decide whether the clean config panel admits a training execution
design. It should not train in the audit milestone.
