# M1794 Executable V2 Reset-Feasibility Preflight

- status: completed
- decision: `executable_v2_reset_preflight_sampling_failures_route_to_result_audit`
- summary: `runs/m1794_executable_v2_reset_feasibility_preflight/summary.json`
- environment reset started: true
- rollout/training/replay/PPO: false

## Summary

M1794 ran the full 312-row executable v2 reset-only feasibility preflight using
the M1792 adapter and the M1793 fixed command. The run completed, but the panel
is not reset-feasible yet.

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_reset_feasibility_preflight \
  --executable-v2-panel-specs runs/m1790_executable_v2_panel_spec_materialization_preflight/executable_v2_panel_specs.json \
  --output-dir runs/m1794_executable_v2_reset_feasibility_preflight \
  --eval-seed-base 179400 \
  --target-spec-count 312 \
  --target-profile-count 12 \
  --target-role-surface-count 6 \
  --next-blocker m1795-executable-v2-reset-feasibility-result-audit
```

Result:

```text
result_class: executable_v2_reset_feasibility_preflight_fail
attempted_spec_count: 312
target_attempted_spec_count: 312
reset_success_count: 272
sampling_failure_count: 40
profile_count: 12
role_surface_count: 6
reset_ready_spec_count: 312
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
metadata_join_incomplete_count: 0
guardrail_violation_count: 0
```

## Failure Localization

All failures have the same error:

```text
RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

Failure counts by surface:

```text
stable_avoidance_aes: 36
hidden_robust_aes_feasible: 4
```

Failure counts by task label:

```text
aes_feasible: 28
aeb_feasible: 12
```

Failure counts by hidden bucket:

```text
brake_variation: 12
nominal: 12
friction_step: 12
brake_drive_variation: 2
actuator_delay: 1
mass_cg_shift: 1
```

Failure counts by surface and hidden bucket:

```text
stable_avoidance_aes / brake_variation: 12
stable_avoidance_aes / nominal: 12
stable_avoidance_aes / friction_step: 12
hidden_robust_aes_feasible / brake_drive_variation: 2
hidden_robust_aes_feasible / actuator_delay: 1
hidden_robust_aes_feasible / mass_cg_shift: 1
```

The failure is therefore not diffuse across all v2 surfaces. It is concentrated
in stable/AES-feasible sampling filters and a small part of the hidden robust
AES-feasible surface.

## Written Artifacts

```text
runs/m1794_executable_v2_reset_feasibility_preflight/summary.json
runs/m1794_executable_v2_reset_feasibility_preflight/reset_stress_rows.csv
runs/m1794_executable_v2_reset_feasibility_preflight/sampling_failure_rows.csv
runs/m1794_executable_v2_reset_feasibility_preflight/label_distribution_by_surface.csv
runs/m1794_executable_v2_reset_feasibility_preflight/label_distribution_by_profile.csv
runs/m1794_executable_v2_reset_feasibility_preflight/label_distribution_by_hidden_bucket.csv
```

## Guardrails

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
- guardrail violation count: `0`

## Claim Boundary

Supported:

- full executable v2 reset-only preflight ran;
- 272/312 specs reset successfully;
- 40 sampling failures are localized for M1795 audit;
- no label leakage, ranking admission, rollout, policy action, training, or
  promotion occurred.

Unsupported:

- reset feasibility pass;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.

## Decision

Route to M1795 reset-feasibility result audit. M1795 should determine whether
the failures are seed-fragile, inherited M1771 sampling artifacts, or v2
surface/label repair issues before any rerun or repair.
