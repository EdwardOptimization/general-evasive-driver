# M2278 Paper-Route Current-Sim Scenario Task-Family Config Materialization Result Audit

- status: completed
- decision: `current_sim_scenario_task_family_materialization_audit_route_to_obstacle_lateral_offset_instrumentation_design`
- manifest: `experiments/manifests/m2278-paper-route-current-sim-scenario-task-family-config-materialization-result-audit.json`
- parent result: `runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/summary.json`

## Audit Result

M2277 is complete and guardrail clean:

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

The generated pack is a valid no-reset materialization artifact. It preserves
the corrected role mapping:

```text
aeb_feasible -> R0_stable_avoidable
aes_feasible -> R1_aeb_infeasible_stable_aes
```

and it keeps role labels, hidden dynamics, and scenario-family labels out of the
deployable actor input.

## Execution Blocker

M2277 is not reset/rollout admissible yet:

```text
execution_admissible_without_instrumentation: false
unsupported_execution_blocker_count: 38
primary_route: scenario_task_family_result_audit_route_to_instrumentation_repair
```

The blocker is specific:

```text
capability: emergency_obstacle_lateral_offset
affected rows: 38
left_offset specs: 19
right_offset specs: 19
```

The current emergency obstacle task places the obstacle on the path centerline.
The v0 pack now contains desired left/right lateral-offset specs, but executing
them with the current simulator would silently approximate the task as
centerline. That would invalidate the task-quality branch.

## Nonblocking Unsupported Rows

The future fault rows are correctly recorded as unsupported current-sim
capabilities, but they do not block the v0 current-sim instrumentation route:

```text
single_wheel_blowout_or_puncture
wheel_specific_grip_loss
half_shaft_or_single_side_drive_torque_loss
brake_side_imbalance
steering_deadzone_or_partial_actuator_fault
sensor_dropout_or_bias
```

These remain future higher-fidelity or explicit model-extension items. They are
not current-sim coverage.

## Decision

Route to obstacle lateral-offset instrumentation design before any reset,
rollout, measured execution, training, or ranking:

```text
m2279-paper-route-current-sim-obstacle-lateral-offset-instrumentation-design
```
M2279 should design a backward-compatible `obstacle.lateral_offset_range` field
with default `(0.0, 0.0)`, update scenario reset placement and metadata without
changing actor inputs, and define tests proving centerline default behavior is
unchanged.

## Blocked Routes

Blocked:

```text
reset validation from M2277 configs
rollout or measured execution from M2277 configs
training on role-family configs
controller-family ranking
winner selection
finite-window-vs-GRU verdict
paper-level result
level3 self-identification
high-fidelity validation as a replacement for fixing current-sim metadata
```

## Next

Pre-register:

```text
m2279-paper-route-current-sim-obstacle-lateral-offset-instrumentation-design
```
