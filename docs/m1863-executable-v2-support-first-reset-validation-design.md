# M1863 Executable V2 Support-First Reset Validation Design

- status: completed
- decision: `support_first_reset_validation_design_admit_adapter_implementation`
- branch: `paper_route_executable_v2_support_first_reset_validation`
- parent audit: `docs/m1862-executable-v2-support-first-materialization-result-audit.md`
- materialization rerun: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1861 produced a strict JSON payload with `180` support-first materialized
`executable_v2_panel_specs`. M1862 audited the materialization as clean and
admitted reset-validation design. M1863 designs the next reset-only validation
step without running reset.

The materialized rows already contain reset-relevant `env_config` values that
pin speed, mu, obstacle distance, obstacle half width, required label, and
friction-step timing. They do not yet match the existing
`executable_v2_reset_feasibility_preflight` input contract.

## Input Artifacts

```text
runs/m1861_executable_v2_support_first_materialization/support_first_materialized_executable_v2_panel_specs.json
runs/m1861_executable_v2_support_first_materialization/summary.json
docs/m1862-executable-v2-support-first-materialization-result-audit.md
```

Expected input counts:

```text
materialized_spec_count: 180
role_counts:
  drift_required_recovery: 48
  stable_aeb: 48
  stable_aes_only: 48
  unavoidable_mitigation: 36
surface_counts:
  post_friction_step: 84
  steady_surface: 96
profile_count: 8
speed_count: 5
mu_count: 6
unavoidable_shortage_flag: true
```

The unavoidable role has only `36` rows because fewer supported sources were
available under the fixed support-first template and caps. Reset validation
must carry this shortage flag rather than silently rebalancing the materialized
panel.

## Schema Audit

The support-first materialized rows include:

```text
materialized_v2_panel_spec_id
candidate_source_id
source_v1_bounded_panel_spec_id
source_scenario_spec_id
source_role_semantics
v2_task_label
profile_name
profile_group
source_family_id
surface_variant
speed_ref
mu
friction_step_enabled
friction_step_at
dt
min_time_after_friction_step
obstacle_distance
obstacle_half_width
threshold_score
cell_selection_kind
labels_enter_actor_input
v2_ranking_admissible_by_default
reset_validation_required
measured_execution_required
env_config
```

The existing reset preflight expects standard executable-v2 reset fields such
as:

```text
v2_panel_spec_id
profile_config_path
v2_role_surface_id
role_panel_id
v2_primary_metric
v2_admissibility_gate
reset_ready_spec
```

Therefore direct reset preflight is intentionally not admitted from M1863.
Running reset now would mix schema conversion defects with true reset
feasibility. The next step must be a no-reset adapter that converts the
support-first materialized payload into the standard reset-validation payload.

## Adapter Contract

M1864 should implement a no-reset adapter that reads the M1861 materialized JSON
and writes:

```text
summary.json
support_first_reset_executable_v2_panel_specs.json
support_first_reset_executable_v2_panel_specs.csv
support_first_reset_validation_matrix.csv
support_first_reset_missing_field_rows.csv
support_first_reset_duplicate_key_rows.csv
support_first_reset_validation_claim_boundary.csv
```

The JSON payload must use:

```text
executable_v2_panel_specs
```

so a later execution design can call the existing reset preflight, or a
support-first-specific reset preflight if the adapter implementation finds a
cleaner route.

## Required Converted Fields

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
support_first_materialized_v2_panel_spec_id
candidate_source_id
source_role_semantics
surface_variant
cell_selection_kind
env_config
measured_execution_admissible
controller_family_ranking_admissible
environment_reset_scheduled
environment_rollout_scheduled
training_scheduled
```

Recommended deterministic mappings:

```text
v2_panel_spec_id = materialized_v2_panel_spec_id
v2_role_surface_id = source_role_semantics + "::" + surface_variant
role_panel_id = source_role_semantics
allowed_labels_metadata_only = v2_task_label
hidden_dynamics_bucket = "mu_" + mu + "::" + surface_variant
road_boundary_bucket = "circle_r18"
obstacle_timing_bucket = "post_friction_step" or "steady_surface"
obstacle_lateral_bucket = "support_first_width_" + obstacle_half_width
reset_ready_spec = true
diagnostic_only_no_ranking_claim = true
v2_ranking_admissible_by_default = false
measured_execution_admissible = false
controller_family_ranking_admissible = false
environment_reset_scheduled = false
environment_rollout_scheduled = false
training_scheduled = false
```

The adapter should preserve the inline `env_config` and add any reset-preflight
plumbing fields needed for the existing reset tool, such as deterministic
profile config metadata. That plumbing is reset infrastructure only; it must not
change actor inputs, reward, dynamics, or termination semantics.

## Expected Adapter Counts

M1864 implementation should target:

| field | expected |
| --- | ---: |
| `input_materialized_spec_count` | 180 |
| `targeted_reset_executable_spec_count` | 180 |
| `role_count` | 4 |
| `surface_count` | 2 |
| `role_surface_count` | 8 |
| `profile_count` | 8 |
| `reset_ready_spec_count` | 180 |
| `reset_validation_required_count` | 180 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `measured_execution_admissible_count` | 0 |
| `controller_family_ranking_admissible_count` | 0 |
| `missing_required_field_count` | 0 |
| `duplicate_key_count` | 0 |
| `guardrail_violation_count` | 0 |

## Later Reset Execution Design

After the adapter implementation and project artifact conversion pass, a later
execution-design milestone should pre-register a reset-only command with fixed
counts, for example:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_reset_feasibility_preflight \
  --executable-v2-panel-specs runs/<adapter-output>/support_first_reset_executable_v2_panel_specs.json \
  --output-dir runs/<reset-output> \
  --eval-seed-base 186600 \
  --target-spec-count 180 \
  --target-profile-count 8 \
  --target-role-surface-count 8 \
  --next-blocker <reset-result-audit>
```

That command is intentionally not run in M1863. It should also not be run in
M1864 unless a later execution-design milestone admits it.

## Route Decision

Route to:

```text
m1864-executable-v2-support-first-reset-validation-adapter-implementation
```

M1864 should implement the no-reset adapter and focused tests only. It must not
execute project artifact conversion, instantiate `AutoDriftEnv`, call
`env.reset`, execute policy actions, run measured rollout, train, replay, run
PPO, rank controller families, or make paper-level claims.

## Guardrails

- materialization rerun: `false`
- source mining rerun: `false`
- adapter implementation run: `false`
- project artifact conversion run: `false`
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

- support-first reset-validation design;
- adapter implementation route;
- expected reset payload counts and claim boundary.

Unsupported:

- adapter implementation result;
- project artifact adapter execution result;
- reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
