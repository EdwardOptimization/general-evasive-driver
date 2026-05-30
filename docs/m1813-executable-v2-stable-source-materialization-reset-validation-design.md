# M1813 Executable V2 Stable Source Materialization Reset Validation Design

- status: completed
- decision: `stable_source_reset_validation_design_admit_adapter_implementation`
- source audit: `docs/m1812-executable-v2-stable-source-materialization-result-audit.md`
- reset run: `false`
- rollout started: `false`
- measured rollout started: `false`
- training/replay/PPO: `false`

## Problem

M1811 materialized three stable source specs and a `36`-row profile matrix, but
the existing M1792 reset adapter consumes a different artifact shape:

```text
payload key: executable_v2_panel_specs
per-profile v2_panel_spec_id rows
v2_primary_metric
v2_admissibility_gate
reset_ready_spec
env_config
profile_name
profile_config_path
```

M1811 writes:

```text
stable_source_materialization_specs.json
stable_source_materialization_matrix.csv
```

Those artifacts are complete materialization evidence, but they are not yet a
reset-adapter input. Therefore M1813 designs a conversion adapter before any
reset run.

## Target Reset-Validation Scope

Validate exactly the three materialized stable sources across the `12` existing
profile controls:

| materialized spec | target | label | profile rows |
| --- | --- | --- | ---: |
| `m1811-stable-bp-000` | `m1771-bp1-00` | `aes_feasible` | 12 |
| `m1811-stable-bp-001` | `m1771-bp1-02` | `aes_feasible` | 12 |
| `m1811-stable-bp-002` | `m1771-bp1-05` | `aeb_feasible` | 12 |

Expected reset-validation executable row count:

```text
3 materialized specs * 12 profiles = 36 executable_v2_panel_specs
```

## Conversion Contract

The adapter should read:

```text
runs/m1811_executable_v2_stable_source_materialization/stable_source_materialization_specs.json
runs/m1811_executable_v2_stable_source_materialization/stable_source_materialization_matrix.csv
```

and write:

```text
summary.json
targeted_reset_executable_v2_panel_specs.json
targeted_reset_executable_v2_panel_specs.csv
targeted_reset_validation_matrix.csv
targeted_reset_validation_claim_boundary.csv
```

The JSON payload must use:

```text
executable_v2_panel_specs
```

so the M1792 reset adapter can consume it without changing reset semantics.

## Required Row Fields

Each converted row must include at least:

```text
v2_panel_spec_id
source_v1_bounded_panel_spec_id
source_v1_role_panel_id
source_scenario_spec_id
v2_role_surface_id
role_panel_id
profile_name
profile_config_path
checkpoint_path
v2_task_label
allowed_labels_metadata_only
labels_enter_actor_input
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
v2_primary_metric
v2_primary_metric_direction
v2_admissibility_gate
reset_ready_spec
diagnostic_only_no_ranking_claim
v2_ranking_admissible_by_default
reset_validation_required
materialized_source_scenario_spec_id
materialized_bounded_panel_spec_id
target_bounded_panel_spec_id
stable_materialization_key
env_config
```

Stable surface v2 fields:

```text
v2_role_surface_id: stable_avoidance_aes
v2_primary_metric: admissible_obstacle_pass_rate
v2_primary_metric_direction: higher_is_better
v2_admissibility_gate: collision_rate_low_and_off_track_rate_low
reset_ready_spec: true
diagnostic_only_no_ranking_claim: true
v2_ranking_admissible_by_default: false
```

## Expected Adapter Counts

The implementation should target:

| field | expected |
| --- | ---: |
| `input_materialization_spec_count` | 3 |
| `input_materialization_matrix_row_count` | 36 |
| `targeted_reset_executable_spec_count` | 36 |
| `profile_control_count` | 12 |
| `role_surface_count` | 1 |
| `reset_ready_spec_count` | 36 |
| `reset_validation_required_count` | 36 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `guardrail_violation_count` | 0 |

## Pass Criteria for Later Reset Execution

The adapter implementation is not reset validation. After conversion passes,
a later execution design should run:

```text
python -m autodrift.executable_v2_reset_feasibility_preflight \
  --executable-v2-panel-specs <targeted_reset_executable_v2_panel_specs.json> \
  --target-spec-count 36 \
  --target-profile-count 12 \
  --target-role-surface-count 1
```

The reset-validation run should pass only if:

- all `36` rows reset successfully;
- sampled obstacle labels match the target label distribution;
- labels do not enter actor input;
- ranking remains blocked by default;
- no policy action, measured rollout, training, replay, PPO, or promotion
  occurs.

## Route Decision

Route to:

```text
m1814-executable-v2-stable-source-reset-validation-adapter-implementation
```

M1814 should implement the no-reset conversion adapter and focused tests. It
must not run reset. A later execution-design milestone can then call the
existing M1792 reset adapter on the converted payload.

## Guardrails

- environment reset started: `false`
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

- targeted reset-validation design;
- conversion adapter is required before reset execution;
- expected converted payload counts and claim boundary.

Unsupported:

- conversion adapter implementation result;
- targeted reset validation result;
- repaired reset feasibility pass;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
