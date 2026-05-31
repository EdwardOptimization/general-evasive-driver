# M1867 Executable V2 Support-First Reset Validation Adapter Result Audit

- status: completed
- decision: `support_first_reset_adapter_result_clean_admit_reset_validation_design`
- branch: `paper_route_executable_v2_support_first_reset_validation`
- parent result: `runs/m1866_executable_v2_support_first_reset_validation_adapter/summary.json`
- converted payload: `runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1867 audits the M1866 no-reset adapter result before any reset-validation
execution is designed or run. The audit checks whether the converted payload is
schema-clean enough to admit a reset-validation execution-design milestone.

## Evidence Checked

M1866 summary reports:

```text
result_class: executable_v2_support_first_reset_validation_adapter_pass
input_materialized_spec_count: 180
targeted_reset_executable_spec_count: 180
role_count: 4
surface_count: 2
role_surface_count: 8
profile_count: 8
reset_ready_spec_count: 180
reset_validation_required_count: 180
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
measured_execution_admissible_count: 0
controller_family_ranking_admissible_count: 0
missing_required_field_count: 0
duplicate_key_count: 0
guardrail_violation_count: 0
```

The converted JSON payload contains the expected top-level key:

```text
executable_v2_panel_specs
```

with `180` rows, unique `v2_panel_spec_id` values, and no missing required
reset-plumbing fields in the checked subset:

```text
v2_panel_spec_id
profile_config_path
v2_role_surface_id
role_panel_id
v2_primary_metric
v2_admissibility_gate
reset_ready_spec
env_config
```

## Distribution

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

Task label counts:

```text
aeb_feasible: 48
aes_feasible: 48
drift_required: 48
unavoidable: 36
```

The unavoidable shortage is inherited from the support-first materialization
cap and remains explicit. The audit does not rebalance or hide that shortage.

## Audit Decision

The adapter result is clean enough to admit a reset-validation execution-design
milestone. M1867 does not admit direct reset execution; the next milestone must
pre-register the exact reset-only command, output directory, seed base, target
counts, pass criteria, and claim boundaries.

Route to:

```text
m1868-executable-v2-support-first-reset-validation-execution-design
```

## Claim Boundary

Supported by M1867:

```text
clean adapter result audit
converted support-first reset payload is ready for reset-validation design
```

Not supported by M1867:

```text
reset feasibility
measured execution
controller-family ranking
paper-level evidence
level3 self-identification evidence
```

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training/replay/PPO: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`
