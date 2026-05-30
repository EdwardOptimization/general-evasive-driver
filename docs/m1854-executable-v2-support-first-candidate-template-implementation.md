# M1854 Executable V2 Support-First Candidate Template Implementation

- status: completed
- decision: `support_first_candidate_template_implementation_pass_route_to_execution_design`
- branch: `paper_route_executable_v2_support_first_source_mining`
- parent design: `docs/m1853-executable-v2-support-first-candidate-template-design.md`
- generated template: `configs/executable_v2_support_first_candidate_templates_v0.json`
- project artifact source mining run: `false`
- materialized executable-v2 rows generated: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Implementation

M1854 adds a deterministic generator:

```text
src/autodrift/executable_v2_support_first_candidate_templates.py
```

focused tests:

```text
tests/test_executable_v2_support_first_candidate_templates.py
```

and the checked-in V0 candidate artifact:

```text
configs/executable_v2_support_first_candidate_templates_v0.json
```

The generator creates the M1853 V0 template exactly:

```text
candidate_row_count: 288
role_count: 4
speed_count: 6
mu_count: 6
surface_variant_count: 2
grid_cell_count_total: 465264
```

The config carries source role, required label, AEB-infeasible requirement,
surface variant, speed, friction, obstacle grid, profile hash, and guardrail
metadata. It does not contain materialized executable-v2 rows.

## Verification

Generated artifact command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.executable_v2_support_first_candidate_templates --output configs/executable_v2_support_first_candidate_templates_v0.json
```

Result:

```text
candidate_row_count=288
grid_cell_count_total=465264
guardrail_violation_count=0
```

Focused:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest tests/test_executable_v2_support_first_candidate_templates.py -q
```

Result:

```text
5 passed in 0.13s
```

Full:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q
```

Result:

```text
1768 passed, 4 warnings in 10.36s
```

## Guardrails

- project artifact source mining run: `false`
- project artifact scan: `false`
- generated candidate template file: `true`
- materialized executable-v2 rows generated: `false`
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

M1855 should fix the exact source mining execution command over the V0
candidate template. That execution should remain a no-reset classifier scan and
should not materialize executable-v2 rows.

## Claim Boundary

Supported:

- deterministic candidate template generator;
- checked-in V0 candidate template artifact;
- focused and full tests passed;
- source mining execution-design route.

Unsupported:

- source mining result;
- materialized executable-v2 rows;
- reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
