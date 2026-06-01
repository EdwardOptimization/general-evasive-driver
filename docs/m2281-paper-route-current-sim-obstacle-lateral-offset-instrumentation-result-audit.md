# M2281 Paper-Route Current-Sim Obstacle Lateral-Offset Instrumentation Result Audit

- status: completed
- decision: `obstacle_lateral_offset_instrumentation_audit_route_to_scenario_task_family_reset_validation_design`
- manifest: `experiments/manifests/m2281-paper-route-current-sim-obstacle-lateral-offset-instrumentation-result-audit.json`
- parent result: `runs/m2280_paper_route_current_sim_obstacle_lateral_offset_instrumentation/summary.json`

## Audit Result

M2280 is complete and guardrail clean:

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
passes_public_materialization_gates: true
```

The M2277 execution blocker is cleared:

```text
unsupported_execution_blocker_count: 0
execution_admissible_without_instrumentation: true
primary_route: scenario_task_family_result_audit_route_to_reset_validation_design
```

M2280 also ran focused reset-only instrumentation tests:

```text
6 passed
```

Those tests covered centerline default compatibility, fixed positive/negative
obstacle lateral offsets, `build_env_config` parsing, materializer support, and
P0 observation shape `72`.

## Actor Contract

M2280 did not change the deployable actor input contract:

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

The lateral-offset field is task/config metadata and reset placement state. It
does not add oracle labels, role labels, hidden dynamics, feasibility labels, or
ranking information to the actor input.

## Remaining Unsupported Capabilities

The remaining unsupported count is nonblocking for this current-sim v0 scenario
pack:

```text
unsupported_capability_count: 6
unsupported_execution_blocker_count: 0
```

The six rows are future model-extension or higher-fidelity fault items:

```text
single_wheel_blowout_or_puncture
wheel_specific_grip_loss
half_shaft_or_single_side_drive_torque_loss
brake_side_imbalance
steering_deadzone_or_partial_actuator_fault
sensor_dropout_or_bias
```

They are intentionally recorded as unsupported future capabilities, not silently
approximated execution rows.

## Decision

Route to scenario task-family reset-validation design:

```text
m2282-paper-route-current-sim-scenario-task-family-reset-validation-design
```

The next step should design a reset-only validation pass over
`configs/paper_route_current_sim_scenario_task_family_v0.json` before any
policy action, measured rollout, training, controller-family ranking, finite
window vs GRU verdict, paper-level claim, or level3 self-identification claim.

## Blocked Routes

Blocked:

```text
direct measured rollout from the refreshed config pack
policy action execution
training or PPO
controller-family ranking
winner selection
finite-window-vs-GRU verdict
paper-level result
level3 self-identification
high-fidelity validation as a replacement for reset validation
```

## Next

Pre-register:

```text
m2282-paper-route-current-sim-scenario-task-family-reset-validation-design
```
