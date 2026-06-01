# M2280 Paper-Route Current-Sim Obstacle Lateral-Offset Instrumentation Implementation

- status: completed
- result class: `current_sim_scenario_task_family_config_materialization_pass`
- manifest: `experiments/manifests/m2280-paper-route-current-sim-obstacle-lateral-offset-instrumentation-implementation.json`
- implementation:
  - `src/autodrift/env.py`
  - `src/autodrift/paper_route_current_sim_scenario_task_family_config_materialization.py`
- tests:
  - `tests/test_obstacle_lateral_offset_instrumentation.py`
  - `tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py`
- refreshed config artifact: `configs/paper_route_current_sim_scenario_task_family_v0.json`
- run artifact: `runs/m2280_paper_route_current_sim_obstacle_lateral_offset_instrumentation/summary.json`
- reset-only tests in M2280: `true`
- policy actions executed in M2280: `false`
- measured rollout/training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2280 adds:

```python
ObstacleTaskConfig.lateral_offset_range: tuple[float, float] = (0.0, 0.0)
```

and places the emergency obstacle at reset as:

```text
position + frame.tangent * obstacle_distance
         + normal_left * sampled_lateral_offset
```

The default `(0.0, 0.0)` preserves centerline behavior. Positive offsets move
the obstacle to frame-left; negative offsets move it to frame-right.

The materializer now writes:

```text
env_config["obstacle"]["lateral_offset_range"] = (offset, offset)
env_config_supported: true
execution_blocked_by_unsupported_capability: false
```

for left/right scenario specs.

## Reset-Only Verification

Focused tests:

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q \
  tests/test_obstacle_lateral_offset_instrumentation.py \
  tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py
```

Result:

```text
6 passed
```

The tests verify:

```text
default lateral_offset_range == (0.0, 0.0)
default reset reports near-zero obstacle_lateral_offset
build_env_config accepts obstacle.lateral_offset_range
fixed positive offset reports positive obstacle_lateral_offset
fixed negative offset reports negative obstacle_lateral_offset
P0 observation shape remains 72
materializer reports no lateral-offset unsupported rows
```

## Materialization Refresh

Command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_config_materialization \
  --config-output configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2280_paper_route_current_sim_obstacle_lateral_offset_instrumentation \
  --next-blocker m2281-paper-route-current-sim-obstacle-lateral-offset-instrumentation-result-audit
```

Result:

```text
result_class: current_sim_scenario_task_family_config_materialization_pass
scenario_family_count: 6
scenario_spec_count: 72
min_specs_per_role: 12
metadata_missing_required_field_count: 0
duplicate_scenario_spec_id_count: 0
labels_enter_actor_input_count: 0
actor_contract_violation_count: 0
ranking_admissible_count: 0
guardrail_violation_count: 0
unsupported_capability_count: 6
unsupported_execution_blocker_count: 0
execution_admissible_without_instrumentation: true
primary_route: scenario_task_family_result_audit_route_to_reset_validation_design
passes_public_materialization_gates: true
```

The `6` remaining unsupported capability rows are future nonblocking items:

```text
single_wheel_blowout_or_puncture
wheel_specific_grip_loss
half_shaft_or_single_side_drive_torque_loss
brake_side_imbalance
steering_deadzone_or_partial_actuator_fault
sensor_dropout_or_bias
```

They are not current-sim execution blockers.

## Actor Contract

No actor-input dimension or privileged-input path changed:

```text
history_length: 1
action_history_mode: full
include_privileged_params: false
obstacle_relative_velocity_mode: zero
wheel_observation_mode: none
P0 observation shape: 72
labels_enter_actor_input_count: 0
actor_contract_violation_count: 0
```

## Claim Boundary

Supported:

```text
obstacle lateral-offset instrumentation is implemented
centerline default compatibility is tested
left/right reset placement is test-covered
M2277 materializer execution blockers are cleared
```

Unsupported:

```text
role-family reset validation result
rollout or measured execution result
training result
controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level evidence
level3 self-identification
```

## Decision

Route to M2281 result audit. The likely next route is scenario task-family
reset-validation design, not rollout/training/ranking yet.
