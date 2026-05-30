# M1690 Paper-Route Controller-Family Executable Workload Materialization Preflight

- status: completed
- result class: `controller_family_executable_workload_materialization_preflight_pass`
- artifact: `runs/m1690_controller_family_executable_workload_materialization_preflight/summary.json`
- executable specs: `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json`
- executable specs CSV: `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.csv`
- workload matrix: `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv`

## Scope

M1690 materializes the 72 M1680 source-budgeted metadata specs into executable
P0-compatible task specs and expands them into the 12-profile workload matrix.

This is a no-rollout infrastructure preflight. It does not start environment
rollout, train, replay, run PPO, use private holdout, promote, change actor
inputs, or claim controller-family ranking or level3 self-identification.

## Result

- executable spec count: `72`
- target executable spec count: `72`
- workload cell count: `864`
- target workload cell count: `864`
- reference workload cell count: `864`
- profile count: `12`
- task family counts: `T4=36`, `T5=36`
- unmappable spec count: `0`
- contract violation count: `0`
- forbidden key violation count: `0`
- missing profile artifact count: `0`
- guardrail violation count: `0`
- passes public smoke gates: `true`

## Materialization Policy

Each metadata spec chooses a deterministic executable endpoint from its
`source_family_left` / `source_family_right` pair, preferring an endpoint whose
known task family matches the metadata `task_family`.

Directly executable source families use their own env template. Proxy families
map to existing public env templates:

- `capability_step_down` / `capability_step_up` ->
  `t4_capability_step_temporal`
- `actuator_delay_step` -> `t4_actuator_delay_response`
- `curved_boundary_obstacle` -> `t5_boundary_axis_retarget`
- `brake_fade_or_loss_proxy` / `drive_loss_proxy` / `grip_loss_proxy` ->
  `t5_near_boundary_warmup`
- `late_reveal_boundary` -> `t5_high_speed_close_obstacle`

All materialized env configs preserve:

- `history_length == 1` at source-spec level
- `action_history_mode == full`
- `include_privileged_params == false`
- `wheel_observation_mode == none`
- `obstacle_relative_velocity_mode == zero`

The later rollout runner may override only `history_length` per profile to
match checkpoint observation shape. It must not add actor inputs or tune a
profile-specific task.

## Supported Claims

- The M1680/M1683 public workload can now be represented as executable
  P0-compatible task specs and an 864-cell public workload matrix.
- Full rollout execution is no longer blocked by metadata-only specs, subject to
  audit.

## Unsupported Claims

- controller-family ranking
- full rollout execution result
- finite-window history necessity
- recurrent advantage
- private-holdout evidence
- paper-level evidence
- level3 anticipatory self-identification

## Next Step

M1691 should audit this materialization before any full 864-cell rollout. The
audit should check deterministic source mapping, proxy-template use, contract
checks, workload counts, and guardrails.
