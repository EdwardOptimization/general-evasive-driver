# M1869 Executable V2 Support-First Reset Validation Preflight

- status: completed
- decision: `support_first_reset_validation_preflight_pass_route_to_result_audit`
- branch: `paper_route_executable_v2_support_first_reset_validation`
- parent design: `docs/m1868-executable-v2-support-first-reset-validation-execution-design.md`
- result artifact: `runs/m1869_executable_v2_support_first_reset_validation_preflight/summary.json`
- environment reset started: `true`
- rollout/training/replay/PPO: `false`

## Purpose

M1869 ran the reset-only feasibility preflight registered in M1868. The
milestone tests whether the converted 180-row support-first reset payload can
sample and reset without rollout, policy actions, label leakage, ranking
admission, or guardrail violations.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_reset_feasibility_preflight \
  --executable-v2-panel-specs runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json \
  --output-dir runs/m1869_executable_v2_support_first_reset_validation_preflight \
  --eval-seed-base 186900 \
  --target-spec-count 180 \
  --target-profile-count 8 \
  --target-role-surface-count 8 \
  --next-blocker m1870-executable-v2-support-first-reset-validation-result-audit
```

## Result

```text
result_class: executable_v2_reset_feasibility_preflight_pass
attempted_spec_count: 180
target_attempted_spec_count: 180
reset_success_count: 180
sampling_failure_count: 0
profile_count: 8
target_profile_count: 8
role_surface_count: 8
target_role_surface_count: 8
reset_ready_spec_count: 180
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
metadata_join_incomplete_count: 0
guardrail_violation_count: 0
```

Role-surface counts:

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

Sampled label counts:

```text
aeb_feasible: 48
aes_feasible: 48
drift_required: 48
unavoidable: 36
```

The unavoidable post-friction-step role-surface still has only `12` rows. This
is the known support-first materialization shortage and not a reset failure.

## Output Artifacts

```text
runs/m1869_executable_v2_support_first_reset_validation_preflight/summary.json
runs/m1869_executable_v2_support_first_reset_validation_preflight/reset_stress_rows.csv
runs/m1869_executable_v2_support_first_reset_validation_preflight/sampling_failure_rows.csv
runs/m1869_executable_v2_support_first_reset_validation_preflight/label_distribution_by_surface.csv
runs/m1869_executable_v2_support_first_reset_validation_preflight/label_distribution_by_profile.csv
runs/m1869_executable_v2_support_first_reset_validation_preflight/label_distribution_by_hidden_bucket.csv
```

`sampling_failure_rows.csv` contains headers only.

## Claim Boundary

Supported by M1869:

```text
reset-only validation passed for the converted 180-row support-first payload
no sampling failures
no label leakage
no ranking admission
no rollout or policy action execution
```

Not supported by M1869:

```text
measured execution
controller-family ranking
paper-level benchmark evidence
level3 self-identification evidence
```

## Route Decision

Route to:

```text
m1870-executable-v2-support-first-reset-validation-result-audit
```

M1870 should audit whether the reset pass is sufficient to admit a measured
execution design, or whether an additional task-quality/source-balance repair
is needed first.

## Guardrails

- environment reset started: `true`
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
