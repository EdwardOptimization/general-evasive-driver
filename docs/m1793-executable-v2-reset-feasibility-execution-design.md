# M1793 Executable V2 Reset-Feasibility Execution Design

- status: completed
- decision: `executable_v2_reset_execution_design_admit_full_reset_preflight`
- source: `docs/m1792-executable-v2-reset-feasibility-adapter-implementation.md`
- reset run in this milestone: false
- rollout/training/replay/PPO: false

## Summary

M1793 fixes the exact command and gates for the full executable v2 reset-only
feasibility preflight. It does not run reset. The next milestone should execute
the 312-row preflight with the M1792 adapter.

## Execution Command

M1794 should run:

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

## Required Targets

M1794 should pass only if:

```text
result_class: executable_v2_reset_feasibility_preflight_pass
attempted_spec_count: 312
target_attempted_spec_count: 312
reset_success_count: 312
sampling_failure_count: 0
profile_count: 12
target_profile_count: 12
role_surface_count: 6
target_role_surface_count: 6
reset_ready_spec_count: 312
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
metadata_join_incomplete_count: 0
guardrail_violation_count: 0
```

Expected output directory:

```text
runs/m1794_executable_v2_reset_feasibility_preflight/
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

M1794 may start environment reset. It must not start rollout or execute policy
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

Route to M1794 executable v2 reset-feasibility preflight. M1794 should execute
the command above exactly and write the resulting artifacts. Interpretation of
sampling failures or label distributions belongs to M1795 result audit.

## Claim Boundary

Supported:

- full executable v2 reset-only preflight command and gates are fixed;
- M1794 execution is admitted.

Unsupported:

- reset feasibility result;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.
