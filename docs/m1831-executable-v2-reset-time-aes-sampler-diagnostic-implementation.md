# M1831 Executable V2 Reset-Time AES Sampler Diagnostic Implementation

- status: completed
- decision: `reset_time_aes_sampler_diagnostic_implementation_pass_route_to_execution_design`
- source: `src/autodrift/executable_v2_reset_time_aes_sampler_diagnostic.py`
- tests: `tests/test_executable_v2_reset_time_aes_sampler_diagnostic.py`
- project artifact diagnostic run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Implementation Summary

M1831 implements the reset-time AES sampler diagnostic helper specified by
M1830. The helper can:

- replay reset-time obstacle sampler attempts from the reset RNG state without
  calling `AutoDriftEnv.reset`;
- reproduce obstacle-label filters, AEB-infeasible filters,
  `max_threshold_score`, and friction-step timing filters;
- report per-attempt labels, threshold scores, timing values, and rejection
  reasons;
- select failed `aes_feasible` reset rows from an executable-v2 reset preflight;
- write diagnostic tables for later project-artifact execution.

The implementation does not run the diagnostic over project artifacts in this
milestone.

## Added Functions

Key public helpers:

```text
reset_sampler_state_from_seed(...)
evaluate_obstacle_candidate(...)
replay_reset_time_obstacle_attempts(...)
summarize_attempts(...)
failed_aes_target_ids(...)
run_reset_time_aes_sampler_diagnostic(...)
claim_boundary_rows()
```

The default future execution output directory is:

```text
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic
```

## Validation

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest tests/test_executable_v2_reset_time_aes_sampler_diagnostic.py -q
```

Result:

```text
4 passed
```

Full test suite:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q
```

Final result:

```text
1742 passed, 4 warnings in 8.46s
```

## Follow-Up

Route to:

```text
m1832-executable-v2-reset-time-aes-sampler-diagnostic-execution-design
```

M1832 should pre-register the exact project-artifact diagnostic command over:

```text
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv
```

M1832 should not run the diagnostic.

## Guardrails

- project artifact diagnostic execution: `false`
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

- reset-time AES sampler diagnostic helper implementation;
- focused tests and full-suite validation;
- execution-design route.

Unsupported:

- project diagnostic result;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
