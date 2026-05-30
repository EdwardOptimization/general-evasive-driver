# M1862 Executable V2 Support-First Materialization Result Audit

- status: completed
- decision: `materialization_result_clean_admit_reset_validation_design`
- branch: `paper_route_executable_v2_support_first_materialization`
- parent result: `runs/m1861_executable_v2_support_first_materialization/summary.json`
- materialization rerun: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Audit Summary

M1861 materialization is within the M1860 bounds:

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

The materialized JSON payload is strict JSON and contains 180
`executable_v2_panel_specs`.

## Coverage Audit

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

Diversity:

```text
speed_count: 5
mu_count: 6
```

The unavoidable role is smaller than the other roles because fewer supported
sources were available under the fixed support-first template and caps. This is
not a materialization failure. M1863 should carry this as a shortage flag during
reset-validation design instead of silently rebalancing by changing the
materialization rules.

## Decision

The materialization result is clean enough to design reset validation.

Next:

```text
m1863-executable-v2-support-first-reset-validation-design
```

M1863 should design reset-only validation over the 180 materialized specs. It
should not run reset yet. It should explicitly check:

- all 180 specs are joinable and reset-validation eligible;
- role and surface counts are preserved;
- unavoidable shortage is recorded;
- reset validation command has fixed expected counts;
- no measured rollout or controller ranking occurs.

## Guardrails

- materialization rerun: `false`
- source mining rerun: `false`
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

- bounded materialization result audit;
- reset-validation design route.

Unsupported:

- reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
