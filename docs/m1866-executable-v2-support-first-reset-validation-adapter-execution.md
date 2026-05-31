# M1866 Executable V2 Support-First Reset Validation Adapter Execution

- status: completed
- decision: `support_first_reset_validation_adapter_execution_pass_route_to_result_audit`
- branch: `paper_route_executable_v2_support_first_reset_validation`
- parent design: `docs/m1865-executable-v2-support-first-reset-validation-adapter-execution-design.md`
- result artifact: `runs/m1866_executable_v2_support_first_reset_validation_adapter/summary.json`
- output payload: `runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1866 ran the exact no-reset adapter command registered in M1865. The goal was
only to convert the M1861 support-first materialized specs into a standard
`executable_v2_panel_specs` reset-validation payload. It does not prove reset
feasibility and does not run any controller.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_support_first_reset_validation_adapter \
  --support-first-materialized-specs runs/m1861_executable_v2_support_first_materialization/support_first_materialized_executable_v2_panel_specs.json \
  --output-dir runs/m1866_executable_v2_support_first_reset_validation_adapter \
  --profile-config-path configs/paper_route_corrected_profiles/m1207_l0_current_masked.json \
  --target-materialized-spec-count 180 \
  --target-executable-spec-count 180 \
  --target-profile-count 8 \
  --target-role-count 4 \
  --target-surface-count 2 \
  --target-role-surface-count 8 \
  --next-blocker m1867-executable-v2-support-first-reset-validation-adapter-result-audit
```

## Result

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

## Output Artifacts

```text
runs/m1866_executable_v2_support_first_reset_validation_adapter/summary.json
runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json
runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.csv
runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_validation_matrix.csv
runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_missing_field_rows.csv
runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_duplicate_key_rows.csv
runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_validation_claim_boundary.csv
```

The payload contains `180` `executable_v2_panel_specs` rows. The missing-field
and duplicate-key CSVs contain headers only.

## Claim Boundary

Supported by M1866:

```text
support-first reset-validation adapter execution
clean converted 180-row reset payload
no label leakage
no ranking or measured-execution admission
```

Not supported by M1866:

```text
reset feasibility
measured execution
controller-family ranking
paper-level evidence
level3 self-identification evidence
```

## Route Decision

Route to:

```text
m1867-executable-v2-support-first-reset-validation-adapter-result-audit
```

The audit should verify whether this pass is sufficient to admit reset-only
validation over the converted payload, or whether adapter/schema repair is
needed first.

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
