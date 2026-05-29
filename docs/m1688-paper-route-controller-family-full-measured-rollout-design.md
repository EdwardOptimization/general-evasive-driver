# M1688 Paper-Route Controller-Family Full Measured Rollout Design

- status: completed
- decision: `full_rollout_design_route_to_executable_workload_materialization_preflight`
- parent audit: `docs/m1687-paper-route-controller-family-measured-routing-smoke-result-audit.md`
- parent workload protocol: `runs/m1683_controller_family_bounded_rollout_protocol_preflight/workload_matrix.csv`
- parent task specs: `runs/m1680_controller_family_bounded_task_source_generation_preflight/task_source_specs.json`

## Summary

M1688 designs the full public measured rollout path after M1686 routing smoke
passed M1687 audit.

The key finding is that the full workload is not ready for direct execution:
M1680 provides 72 source-budgeted task-source metadata specs, and M1683 expands
them to a 72 x 12 profile workload matrix, but those specs are not yet
materialized as executable simulator env configs. M1686 proved that the runner
can execute a small source-diverse hook subset, not that every M1680 metadata
spec has an unambiguous executable env mapping.

Therefore the next step must be an executable workload materialization preflight
before any 864-episode execution.

## Full Public Workload

Target workload:

```text
task specs: 72
controller profiles: 12
workload cells: 864
source strata: all_72_specs, explicit_window_subset, mapping_window_unspecified,
               task_family_T4, task_family_T5
profile controls: L1, L2 normal windows, L2 current-tiled windows,
                  L3 online GRU, L3 reset-control corrected
```

This remains public evaluation-only work. It must not use private holdout,
training, replay, PPO, promotion, actor-input changes, profile-specific tuning,
or M1615 hidden/action targets.

## Required Materialization Layer

M1689 should convert each M1680 metadata spec into one executable env spec.

Required input:

```text
runs/m1680_controller_family_bounded_task_source_generation_preflight/task_source_specs.json
runs/m1683_controller_family_bounded_rollout_protocol_preflight/workload_matrix.csv
runs/m1674_controller_family_one_seed_public_pilot/configs/*_seed167400.json
runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
```

Required output:

```text
runs/m1689_controller_family_executable_workload_materialization_preflight/executable_task_specs.json
runs/m1689_controller_family_executable_workload_materialization_preflight/executable_task_specs.csv
runs/m1689_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv
runs/m1689_controller_family_executable_workload_materialization_preflight/summary.json
```

Each executable task spec must include:

```text
task_source_id
task_family
source_edge
source_family_left
source_family_right
window_tag
generation_seed
executable_source_family
executable_seed
env_config
materialization_rule
contract_checks
```

The materialized env config must preserve:

```text
include_privileged_params = false
wheel_observation_mode = none
obstacle_relative_velocity_mode = zero
action_history_mode = full
history_length = 1 in the source spec
```

The later per-profile rollout runner may override only `history_length` to match
each profile checkpoint observation shape. It must not add actor inputs or
profile-specific tuning.

## Source-Family Mapping Policy

M1689 should use deterministic public source builders only:

- existing decisive-history executable builders for `t4_*` and `t5_*`
  source families;
- existing fresh-ambiguity/proxy source definitions for
  `capability_step_up`, `capability_step_down`, `actuator_delay_step`, and
  `curved_boundary_obstacle`;
- no hidden/action tensor targets from M1615;
- no private holdout;
- no controller-specific task tuning.

If a metadata source edge cannot be mapped deterministically to a P0-compatible
env config, M1689 must fail as a materialization blocker rather than guessing
or silently dropping rows.

## Full Rollout Execution Design

Only after M1689 passes, M1690 may execute the full public workload.

M1690 target artifacts:

```text
runs/m1690_controller_family_full_measured_rollout/summary.json
runs/m1690_controller_family_full_measured_rollout/episode_rows.csv
runs/m1690_controller_family_full_measured_rollout/profile_aggregate.csv
runs/m1690_controller_family_full_measured_rollout/spec_aggregate.csv
runs/m1690_controller_family_full_measured_rollout/stratum_aggregate.csv
runs/m1690_controller_family_full_measured_rollout/comparison_aggregate.csv
runs/m1690_controller_family_full_measured_rollout/failure_rows.csv
```

Execution target:

```text
episode_count == 864
profile_count == 12
spec_count == 72
all selected metrics finite
runner exception count == 0
guardrail violation count == 0
```

Selected metrics:

```text
success_rate
collision_rate
road_departure_rate
spin_or_unstable_rate
clearance_margin_mean
clearance_margin_p10
return_mean
steps_mean
control_smoothness
```

Comparison aggregates must include, but not interpret as final ranking:

```text
L2 normal minus matched L2 current-tiled
L3 online minus L3 reset-control
L3 online minus best L2 normal
L1 one-step versus history-capable profiles
T4 versus T5 strata
explicit-window subset versus all_72_specs
```

## Failure Handling

M1690 must stop and route to audit/repair if:

```text
any profile checkpoint/config is missing;
any executable spec violates P0/no-wheel/no-oracle contract;
any profile/spec cell raises a runner exception;
selected metrics are non-finite;
guardrail_violation_count > 0;
episode_count < 864;
profile_count < 12;
spec_count < 72.
```

Do not patch around failures by dropping specs, retuning one profile, changing
actor inputs, or switching to private holdout.

## Claim Boundary

Even if M1690 succeeds, the result remains public measured-rollout evidence
until audited. It can support a controller-family evidence discussion only after
M1691 checks artifacts, strata, controls, and failure rows.

It still cannot by itself prove:

- paper-level evidence;
- private-holdout generalization;
- level3 anticipatory self-identification;
- closed-loop history necessity.

Those require later fresh/generalization and intervention gates.

## Next Steps

The logical technical next step is executable workload materialization, but the
branch has reached workflow-synthesis cadence. Therefore M1689 must first
synthesize the M1669-M1688 controller-family task-source branch. If synthesis
continues the route, the following milestone should be executable workload
materialization preflight.

Do not execute the full 864-cell rollout until every M1680 metadata spec has an
audited executable P0-compatible env mapping.
