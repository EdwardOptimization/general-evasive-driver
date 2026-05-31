# M1872 Executable V2 Support-First Measured Runner Adapter Design

- status: completed
- decision: `support_first_measured_runner_adapter_design_admit_implementation`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- parent design: `docs/m1871-executable-v2-support-first-measured-execution-design.md`
- reset payload: `runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json`
- controller profile source: `runs/m1674_controller_family_one_seed_public_pilot`
- no materialization execution: true
- no rollout: true
- policy action executed: false
- training/replay/PPO: false

## Purpose

M1872 defines the adapter contract needed before support-first executable-v2
scenarios can be measured with controller-family profiles. It does not
materialize the project matrix and does not execute policy actions.

## Design Input Facts

The support-first payload contains:

```text
reset-validated executable-v2 specs: 180
role panels: 4
role surfaces: 8
profile/source groups: 8
reset success: 180/180
sampling failures: 0
label leakage count: 0
ranking admissible by default: 0
```

Controller-family public pilot artifacts are available for the canonical 12
profiles under:

```text
runs/m1674_controller_family_one_seed_public_pilot/configs/*_seed167400.json
runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
```

The 12 profiles are:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L2_window_50
L2_window_50_current_tiled
L2_window_100
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

## Execution Budget Choice

Use the full public diagnostic matrix for the adapter target:

```text
180 support-first specs x 12 controller-family profiles = 2160 workload cells
```

Rationale:

- it preserves fair current-response / finite-window / GRU comparison coverage;
- it avoids profile-specific sampling or tuning;
- it keeps all support-first roles and surface variants represented;
- it is still small enough for resumable public measured execution;
- it makes the known support-first imbalance visible instead of sampling around
  it.

The full matrix remains diagnostic. It is not a private holdout, promotion
gate, controller ranking result, paper-level result, or level3 self-ID result.

## Adapter Input Schema

The adapter implementation should read:

```text
--executable-v2-panel-specs \
  runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json
--m1674-run-dir \
  runs/m1674_controller_family_one_seed_public_pilot
--output-dir \
  runs/m1874_executable_v2_support_first_measured_runner_adapter_preflight
```

The support-first input key is:

```text
executable_v2_panel_specs
```

Each spec must have:

```text
v2_panel_spec_id
env_config
role_panel_id
v2_role_surface_id
surface_variant
profile_name
profile_group
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
v2_task_label
labels_enter_actor_input=false
v2_ranking_admissible_by_default=false
diagnostic_only_no_ranking_claim=true
```

## Normalized Spec Output

The adapter should write:

```text
support_first_measured_executable_specs.json
support_first_measured_executable_specs.csv
support_first_measured_workload_matrix.csv
support_first_role_surface_counts.csv
controller_profile_artifact_rows.csv
summary.json
```

The normalized JSON should use a runner-friendly key:

```text
support_first_measured_executable_specs
```

Each normalized spec row should include:

```text
task_source_id = v2_panel_spec_id
support_first_v2_panel_spec_id = v2_panel_spec_id
support_first_materialized_v2_panel_spec_id
source_scenario_spec_id
role_panel_id
v2_role_surface_id
surface_variant
scenario_profile_name = original support-first profile_name
scenario_profile_group = original profile_group
task_family = role_panel_id
source_edge = surface_variant
window_tag = hidden_dynamics_bucket
executable_source_family = source_family_id or surface_variant
env_template_family = source_family_id or surface_variant
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
sampled_obstacle_label = v2_task_label
allowed_labels_metadata_only
diagnostic_only_no_ranking_claim
labels_enter_actor_input
v2_ranking_admissible_by_default
env_config
```

## Workload Matrix Output

For each normalized spec and each controller profile, write one workload row:

```text
workload_id = task_source_id::controller_profile_name
support_first_workload_id = workload_id
task_source_id
support_first_v2_panel_spec_id
controller_profile_name
profile_name = controller_profile_name
scenario_profile_name
scenario_profile_group
profile_config_path
checkpoint_path
config_exists
checkpoint_exists
task_family
source_edge
window_tag
executable_source_family
env_template_family
role_panel_id
v2_role_surface_id
surface_variant
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
sampled_obstacle_label
allowed_labels_metadata_only
strata
environment_rollout_scheduled=false
training_scheduled=false
profile_specific_tuning=false
controller_family_ranking_claim_made=false
paper_level_claim_made=false
level3_self_id_claim_made=false
```

`profile_name` is kept only for compatibility with shared rollout helpers, and
must equal `controller_profile_name`. The original support-first `profile_name`
must only appear as `scenario_profile_name`.

## Strata

The adapter should emit semicolon-separated strata that include at least:

```text
support_first_executable_v2
role_panel_<role_panel_id>
role_surface_<v2_role_surface_id>
surface_variant_<surface_variant>
scenario_profile_<scenario_profile_name>
hidden_dynamics_<hidden_dynamics_bucket>
road_boundary_<road_boundary_bucket>
obstacle_timing_<obstacle_timing_bucket>
obstacle_lateral_<obstacle_lateral_bucket>
controller_profile_<controller_profile_name>
```

## Preflight Pass Criteria

The no-rollout adapter preflight should pass only if:

- normalized spec count is `180`;
- workload cell count is `2160`;
- controller profile count is `12`;
- all 12 controller profile configs and checkpoints exist;
- role panel count is `4`;
- role surface count is `8`;
- role-surface counts preserve the known imbalance;
- `profile_name == controller_profile_name` in every workload row;
- `scenario_profile_name` is non-empty in every workload row;
- no workload row uses scenario-profile metadata as a controller policy profile;
- `labels_enter_actor_input` is false for every normalized spec;
- `v2_ranking_admissible_by_default` is false for every normalized spec;
- guardrail violation count is `0`;
- no environment reset, policy action, measured rollout, training, replay, PPO,
  promotion, private holdout, actor input change, reward change, dynamics
  change, termination change, profile-specific tuning, controller ranking,
  paper-level claim, or level3 self-ID claim occurs.

## Later Measured Runner Requirements

After adapter preflight passes, a later measured runner may reuse
`run_workload_cell()` from `controller_family_full_rollout_execution`, but it
must preserve support-first metadata in episode rows and aggregate by:

```text
controller_profile_name
role_panel_id
v2_role_surface_id
surface_variant
scenario_profile_name
hidden_dynamics_bucket
sampled_obstacle_label
outcome_bucket
termination_reason
controller_profile_name + role_panel_id
controller_profile_name + v2_role_surface_id
```

The first measured rollout should remain public diagnostic execution. It may
audit task quality and outcome modes, but it may not rank controller families
or claim finite-window/GRU/self-ID evidence until a later result audit.

## Next Implementation

M1873 should implement a no-rollout adapter module and focused tests. It should
not run the 2160-row project materialization yet.

Expected implementation surface:

```text
src/autodrift/executable_v2_support_first_measured_runner_adapter.py
tests/test_executable_v2_support_first_measured_runner_adapter.py
```

M1874 can then run the adapter preflight over the real M1866/M1674 artifacts.

## Guardrails

- environment reset started in M1872: `false`
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

## Claim Boundary

Supported:

```text
support-first measured runner adapter schema is defined
full public diagnostic workload budget is fixed at 2160 cells
scenario-profile metadata and controller policy profile identity are separated
adapter implementation is admissible
```

Unsupported:

```text
adapter execution result
measured rollout result
controller-family ranking
paper-level benchmark evidence
current-response / finite-window / GRU comparison result
level3 self-identification evidence
```

## Decision

Admit M1873 no-rollout adapter implementation with focused tests. The real
2160-row matrix materialization and any measured rollout remain blocked.
