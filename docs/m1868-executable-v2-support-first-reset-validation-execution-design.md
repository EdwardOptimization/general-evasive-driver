# M1868 Executable V2 Support-First Reset Validation Execution Design

- status: completed
- decision: `support_first_reset_validation_execution_design_admit_preflight_run`
- branch: `paper_route_executable_v2_support_first_reset_validation`
- parent audit: `docs/m1867-executable-v2-support-first-reset-validation-adapter-result-audit.md`
- converted payload: `runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json`
- reset run in this milestone: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1868 fixes the exact command and gates for reset-only validation over the
converted M1866 support-first payload. It does not run reset. The next
milestone should execute the 180-row reset preflight and record sampling
success or failure before any measured execution or controller comparison.

## Execution Command

M1869 should run:

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

## Required Targets

M1869 should pass only if:

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

Expected output directory:

```text
runs/m1869_executable_v2_support_first_reset_validation_preflight/
```

Expected artifacts:

```text
summary.json
reset_stress_rows.csv
sampling_failure_rows.csv
label_distribution_by_surface.csv
label_distribution_by_profile.csv
label_distribution_by_hidden_bucket.csv
```

## Guardrails

M1869 may start environment reset. It must not start rollout or execute policy
actions.

Forbidden:

- measured rollout;
- policy action execution;
- training;
- replay;
- PPO;
- promotion;
- private holdout;
- actor input contract changes;
- profile-specific tuning;
- controller-family ranking;
- paper-level claims;
- level3 self-ID claims.

## Route Decision

Route to:

```text
m1869-executable-v2-support-first-reset-validation-preflight
```

M1869 should execute the command above exactly and write the resulting
artifacts. Interpretation of sampling failures or label distributions belongs
to:

```text
m1870-executable-v2-support-first-reset-validation-result-audit
```

## Claim Boundary

Supported:

- exact support-first reset-only preflight command and gates are fixed;
- M1869 reset preflight execution is admitted.

Unsupported:

- reset feasibility result;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
