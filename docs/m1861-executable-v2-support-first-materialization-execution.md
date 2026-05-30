# M1861 Executable V2 Support-First Materialization Execution

- status: completed
- decision: `support_first_materialization_execution_pass_route_to_result_audit`
- branch: `paper_route_executable_v2_support_first_materialization`
- result artifact: `runs/m1861_executable_v2_support_first_materialization/summary.json`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Execution

M1861 ran the exact M1860 bounded materialization command over M1856 source
support artifacts.

Result:

```text
input_supported_source_count: 202
selected_source_count: 90
selected_cell_count: 180
materialized_spec_count: 180
materialization_matrix_row_count: 180
duplicate_key_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
guardrail_violation_count: 0
```

The result is below the M1860 caps:

```text
selected_source_count <= 96
materialized_spec_count <= 192
```

## Coverage

Role counts:

```text
drift_required_recovery: 48
stable_aeb: 48
stable_aes_only: 48
unavoidable_mitigation: 36
```

Surface counts:

```text
post_friction_step: 84
steady_surface: 96
```

Other diversity:

```text
speed_count: 5
mu_count: 6
```

The unavoidable role produced fewer rows than the other three roles under the
fixed support/cap rules. This is acceptable for materialization, but M1862
should audit whether reset-validation design needs role-specific quotas or
shortage flags.

## Generated Outputs

```text
runs/m1861_executable_v2_support_first_materialization/summary.json
runs/m1861_executable_v2_support_first_materialization/support_first_materialized_source_selection.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialized_cell_selection.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialized_executable_v2_panel_specs.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialized_executable_v2_panel_specs.json
runs/m1861_executable_v2_support_first_materialization/support_first_materialization_matrix.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialization_blocked_sources.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialization_duplicate_keys.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialization_claim_boundary.csv
```

The JSON payload contains 180 `executable_v2_panel_specs` and is strict JSON.
Reset validation should use the JSON payload, not the CSV display string for
`env_config`.

## Guardrails

- project materialization execution run: `true`
- source mining rerun: `false`
- source repair payload generated: `false`
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

- bounded materialization artifacts exist;
- executable-v2 candidate JSON payload exists;
- result audit route.

Unsupported:

- reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
