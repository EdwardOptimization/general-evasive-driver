# M1887 Executable V2 Support-First Repaired Runner Adapter Implementation

- status: completed
- decision: `support_first_repaired_runner_adapter_implementation_pass_admit_preflight_design`
- implementation: `src/autodrift/executable_v2_support_first_repaired_runner_adapter.py`
- focused tests: `tests/test_executable_v2_support_first_repaired_runner_adapter.py`
- reset/rollout in M1887: false
- training/replay/PPO: false

## Summary

M1887 implements the no-rollout repaired runner adapter required by M1886. It
does not run the real M1884 matrix. Focused tests use synthetic fixtures only.

Implemented capabilities:

- bounded-smoke source selection by role surface;
- `config_delta_json` parsing with unknown-key rejection;
- env config patching validated through `build_env_config`;
- separation of rollout geometry rows from imported original/semantics-only
  rows;
- preservation of controller profile identity;
- claim-boundary artifacts that keep repaired execution, ranking, paper claims,
  and level3 self-ID blocked.

Focused verification:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_executable_v2_support_first_repaired_runner_adapter.py
```

Result:

```text
3 passed
```

## Adapter Contract

The helper can emit:

```text
repaired_measured_executable_specs.json
repaired_measured_executable_specs.csv
repaired_measured_workload_matrix.csv
repaired_measured_import_rows.csv
repaired_measured_selection.csv
repaired_adapter_config_failure_rows.csv
repaired_adapter_missing_import_rows.csv
repaired_adapter_duplicate_spec_rows.csv
repaired_adapter_duplicate_workload_rows.csv
repaired_role_surface_counts.csv
repaired_measured_claim_boundary.csv
summary.json
```

The adapter separates:

```text
rollout variants:
  finish_extended
  road_relaxed
  road_relaxed_finish_extended

import variants:
  original
  semantics_only
```

It rejects unknown repair delta keys and validates patched environment configs.
The current patch mapping changes only task/environment geometry parameters; it
does not add hidden, oracle, reference, success, collision, progress, slip, tire
force, friction margin, or controller-mode fields to actor input.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- measured rollout started: `false`
- policy action executed: `false`
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
- real M1884 matrix executed: `false`

## Claim Boundary

Supported:

- repaired adapter infrastructure exists;
- focused tests pass on synthetic fixtures;
- the adapter can separate rollout/import row types and validate config deltas.

Unsupported:

- real M1884 preflight result;
- repaired measured execution result;
- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.

## Decision

Route to M1888 no-rollout real-artifact preflight design. Do not run the real
M1884 repair matrix until the exact preflight command and gates are registered.
