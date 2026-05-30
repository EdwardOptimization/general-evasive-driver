# M1859 Executable V2 Support-First Materialization Implementation

- status: completed
- decision: `support_first_materialization_implementation_pass_route_to_execution_design`
- branch: `paper_route_executable_v2_support_first_materialization`
- parent design: `docs/m1858-executable-v2-support-first-materialization-design.md`
- project materialization execution run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Implementation

M1859 adds a no-reset bounded materialization helper:

```text
src/autodrift/executable_v2_support_first_materialization.py
```

and focused tests:

```text
tests/test_executable_v2_support_first_materialization.py
```

The helper:

- filters to supported/admissible sources only;
- enforces `max_sources_per_role`, `max_sources_per_role_surface`, and
  `max_cells_per_source`;
- selects boundary and representative accepted cells per source;
- writes materialized executable-v2 specs and a matrix;
- keeps labels out of actor input;
- marks reset validation required and measured execution not required.

## Verification

Focused:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest tests/test_executable_v2_support_first_materialization.py -q
```

Result:

```text
5 passed in 0.06s
```

Full:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q
```

Result:

```text
1775 passed, 4 warnings in 10.23s
```

## Guardrails

- project materialization execution run: `false`
- source mining rerun: `false`
- source repair payload generated: `false`
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

## Next Route

M1860 should fix the exact project materialization command over M1856 artifacts.
M1861 may then run materialization, but reset validation remains blocked until a
materialization result audit.

## Claim Boundary

Supported:

- bounded materialization helper implementation;
- focused and full tests passed;
- materialization execution-design route.

Unsupported:

- project materialization result;
- reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
