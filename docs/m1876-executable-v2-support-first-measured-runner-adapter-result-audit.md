# M1876 Executable V2 Support-First Measured Runner Adapter Result Audit

- status: completed
- decision: `support_first_measured_adapter_result_clean_admit_measured_runner_execution_design`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- parent result: `runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/summary.json`
- workload matrix: `runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_workload_matrix.csv`
- no environment reset: true
- no policy action: true
- no measured rollout: true
- training/replay/PPO: false

## Purpose

M1876 audits the M1875 no-rollout adapter preflight before any measured runner
execution design. It checks target counts, profile semantic separation,
role-surface imbalance preservation, and guardrails.

## Evidence Checked

M1875 summary reports:

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

The workload matrix has `2160` data rows. The normalized spec CSV has `180`
data rows. The role-surface count table has `8` data rows.

## Profile Semantics Audit

The workload rows preserve the required separation:

```text
profile_name == controller_profile_name
scenario_profile_name == original support-first profile_name
scenario_as_controller_profile_count == 0
```

This means the adapter did not reuse support-first scenario/source profile
metadata as a controller policy selector.

## Distribution Audit

Controller profile counts are balanced:

```text
12 controller profiles
180 rows per controller profile
```

Role counts:

```text
drift_required_recovery: 48
stable_aeb: 48
stable_aes_only: 48
unavoidable_mitigation: 36
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

The known unavoidable post-friction shortage remains explicit. It does not
block measured runner execution design, but it still blocks aggregate
controller-family ranking and paper-level claims.

## Runner Boundary

M1875 produced clean workload metadata, but this does not admit direct measured
rollout through a generic runner without design. The next measured runner must:

- load `support_first_measured_executable_specs.json`;
- load `support_first_measured_workload_matrix.csv`;
- use `profile_name` only as the controller profile alias;
- preserve `scenario_profile_name`, `v2_role_surface_id`, `surface_variant`,
  and support-first metadata in episode rows;
- aggregate role-wise and role-surface-wise before any profile interpretation.

The existing shared `run_workload_cell()` helper can be reused, but measured
execution still needs a support-first wrapper/runner contract so that the new
metadata and claim boundaries are not lost.

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

## Audit Decision

M1875 is clean enough to admit measured runner execution design:

```text
m1877-executable-v2-support-first-measured-runner-execution-design
```

This does not admit direct measured rollout. M1877 must first define the
support-first measured runner, output artifacts, pass/fail metrics, resumability
rules, and claim boundaries.

## Claim Boundary

Supported by M1876:

```text
support-first adapter preflight result is clean
2160-row diagnostic workload exists locally
scenario/controller profile separation is clean
measured runner execution design is admissible
```

Not supported by M1876:

```text
environment reset or measured rollout result
controller-family ranking
paper-level benchmark evidence
current-response / finite-window / GRU comparison result
level3 self-identification evidence
```
