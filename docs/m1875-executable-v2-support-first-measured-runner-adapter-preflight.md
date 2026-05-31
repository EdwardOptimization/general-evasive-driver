# M1875 Executable V2 Support-First Measured Runner Adapter Preflight

- status: completed
- decision: `support_first_measured_runner_adapter_preflight_pass_route_to_result_audit`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- manifest: `experiments/manifests/m1875-executable-v2-support-first-measured-runner-adapter-preflight.json`
- summary: `runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/summary.json`
- workload matrix: `runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_workload_matrix.csv`
- no environment reset: true
- no policy action: true
- no measured rollout: true
- training/replay/PPO: false

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_support_first_measured_runner_adapter \
  --executable-v2-panel-specs runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json \
  --m1674-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --profile-seed 167400 \
  --output-dir runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight \
  --target-support-first-spec-count 180 \
  --target-controller-profile-count 12 \
  --target-workload-cell-count 2160 \
  --target-role-count 4 \
  --target-role-surface-count 8 \
  --next-blocker m1876-executable-v2-support-first-measured-runner-adapter-result-audit
```

## Result

The adapter preflight passed:

```text
result_class: executable_v2_support_first_measured_runner_adapter_pass
support_first_spec_count: 180
controller_profile_count: 12
workload_cell_count: 2160
role_count: 4
role_surface_count: 8
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
missing_profile_artifact_count: 0
profile_alias_mismatch_count: 0
scenario_as_controller_profile_count: 0
missing_required_field_count: 0
duplicate_key_count: 0
guardrail_violation_count: 0
```

The generated CSV row counts are:

```text
support_first_measured_workload_matrix.csv: 2160 data rows
support_first_measured_executable_specs.csv: 180 data rows
support_first_role_surface_counts.csv: 8 data rows
```

## Role-Surface Counts

The known support-first imbalance is preserved:

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

Controller profile counts are balanced:

```text
each of 12 controller profiles: 180 workload rows
```

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
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Claim Boundary

Supported by M1875:

```text
real support-first no-rollout adapter preflight passed
2160 public diagnostic workload rows were materialized locally
scenario/controller profile separation passed
role-surface imbalance remains explicit
result audit is admissible
```

Not supported by M1875:

```text
environment reset or measured rollout result
controller-family ranking
paper-level evidence
current-response / finite-window / GRU comparison result
level3 self-identification evidence
```

## Decision

Route to M1876 result audit before any measured runner execution design.
