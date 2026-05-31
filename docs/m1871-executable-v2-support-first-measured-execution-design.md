# M1871 Executable V2 Support-First Measured Execution Design

- status: completed
- decision: `support_first_measured_execution_design_requires_runner_adapter`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- parent audit: `docs/m1870-executable-v2-support-first-reset-validation-result-audit.md`
- reset payload: `runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json`
- reset result: `runs/m1869_executable_v2_support_first_reset_validation_preflight/summary.json`
- no rollout: true
- policy action executed: false
- training/replay/PPO: false

## Purpose

M1871 decides whether the reset-validated support-first executable-v2 payload
can be sent directly to an existing measured execution runner, or whether it
needs a measured-runner adapter before any policy action is executed.

## Parent Evidence

M1869 reset validation reports:

```text
result_class: executable_v2_reset_feasibility_preflight_pass
attempted_spec_count: 180
reset_success_count: 180
sampling_failure_count: 0
profile_count: 8
role_surface_count: 8
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
metadata_join_incomplete_count: 0
guardrail_violation_count: 0
```

The known role-surface imbalance remains:

```text
drift_required_recovery::post_friction_step: 24
drift_required_recovery::steady_surface: 24
stable_aeb::post_friction_step: 24
stable_aeb::steady_surface: 24
stable_aes_only::post_friction_step: 24
stable_aes_only::steady_surface: 24
unavoidable_mitigation::post_friction_step: 12
unavoidable_mitigation::steady_surface: 24
```

This imbalance does not block diagnostic measured execution design, but it
blocks aggregate controller-family ranking.

## Runner Compatibility Audit

The existing `metric_specific_bounded_panel_measured_execution` runner consumes
two artifacts:

```text
bounded_panel_specs.json
bounded_panel_matrix.csv
```

Its workload matrix already contains controller-family `profile_name` rows and
bounded-panel fields such as:

```text
bounded_panel_workload_id
scenario_workload_id
bounded_panel_spec_id
role_panel_id
scenario_family
profile_name
evaluation_role
primary_metric_family
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
```

It then calls the shared `run_workload_cell()` helper, which requires:

```text
executable_spec["env_config"]
workload_row["task_source_id"]
workload_row["profile_name"]
profile_row["config_path"]
profile_row["checkpoint_path"]
```

The support-first reset payload is not in that format. It contains
`executable_v2_panel_specs`, with fields such as:

```text
v2_panel_spec_id
support_first_materialized_v2_panel_spec_id
v2_role_surface_id
role_panel_id
surface_variant
source_family_id
source_role_semantics
profile_group
profile_name
profile_config_path
env_config
```

The critical incompatibility is semantic: in the support-first payload,
`profile_name` identifies a scenario/source profile such as
`drift_required_recovery_post_friction_step_grid_v0`. It is not one of the
controller-family profiles to evaluate, such as current-response, finite-window,
or online-GRU profiles loaded from the controller-family profile artifacts.

Directly reusing the existing runner would therefore risk treating a scenario
source label as a controller policy profile. That would make measured execution
invalid even if the code happened to run.

## Design Decision

Do not run measured execution directly from M1871.

Route to a support-first measured-runner adapter design:

```text
m1872-executable-v2-support-first-measured-runner-adapter-design
```

The adapter design must define a new workload layer that separates:

```text
scenario_profile_name: support-first source/profile metadata from the v2 spec
controller_profile_name: actual controller-family policy profile to execute
```

Only `controller_profile_name` may be used to load controller configs and
checkpoints. The support-first `profile_name` must be preserved as metadata,
not as a policy selector.

## Adapter Contract To Design In M1872

The adapter should produce measured workload rows from:

```text
180 reset-validated support-first executable-v2 specs
selected controller-family profiles
```

M1872 must decide the exact profile set and execution budget before any rollout.
The natural full diagnostic matrix is:

```text
180 support-first specs x 12 controller-family profiles = 2160 episodes
```

If a smaller smoke is selected, M1872 must pre-register the sampling rule,
preserve all four roles, both surface variants where available, and explicitly
state that no ranking or paper-level claim is supported.

Required workload semantics:

```text
workload_id
support_first_workload_id
v2_panel_spec_id
task_source_id
role_panel_id
v2_role_surface_id
surface_variant
scenario_profile_name
controller_profile_name
profile_name  # alias only for controller_profile_name in shared runner calls
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
sampled_obstacle_label / v2_task_label as metadata only
diagnostic_only_no_ranking_claim
controller_family_ranking_claim_made=false
```

Required output aggregates:

```text
profile_aggregate
role_panel_aggregate
role_surface_aggregate
surface_variant_aggregate
scenario_profile_aggregate
controller_profile_role_aggregate
controller_profile_role_surface_aggregate
hidden_dynamics_bucket_aggregate
sampled_obstacle_label_aggregate
outcome_aggregate
termination_reason_aggregate
failure_rows
summary
```

The summary must preserve the known imbalance and report it as a diagnostic
field rather than hiding it behind aggregate success.

## Pass Criteria For A Later Execution

A later measured execution should pass only if:

- every scheduled workload row writes either one episode row or one failure row;
- selected rollout metrics are finite where applicable;
- controller profile count matches the pre-registered target;
- support-first spec count matches the pre-registered target;
- role-wise and role-surface aggregates are written;
- the unavoidable post-friction shortage is visible in role-surface counts;
- labels remain metadata only and do not enter actor input;
- ranking remains blocked by default;
- no training, replay, PPO, promotion, private holdout, actor-input change,
  reward change, dynamics change, termination change, profile-specific tuning,
  controller-family ranking claim, paper-level claim, or level3 self-ID claim
  occurs.

## Claim Boundary

Supported by M1871:

```text
the reset-validated support-first payload needs a measured-runner adapter
the existing bounded-panel runner is a reusable reference, not a direct input match
scenario-profile metadata must be separated from controller policy profiles
role-wise diagnostic measured execution remains admissible after adapter design
```

Not supported by M1871:

```text
measured rollout success
controller-family ranking
paper-level evidence
current-response versus finite-window versus GRU comparison
level3 self-identification evidence
```

## Guardrails

- environment reset started in M1871: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Decision

M1871 passes as a design milestone and routes to M1872 support-first measured
runner adapter design. Direct measured execution remains blocked until that
adapter contract is explicit.
