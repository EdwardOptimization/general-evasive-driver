# M2120 Paper-Route Outcome-Supported Decisive Comparison-Support Reset Validation Command Design

- status: completed
- decision: `comparison_support_reset_validation_command_design_admit_implementation_and_run`
- parent artifact: `runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/executable_task_specs.json`
- reset/rollout/measured execution in M2120: `false`
- policy actions executed in M2120: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Constraint

M2119 found that the existing controlled routing-smoke reset validator is not
the exact command to run directly because it hard-codes:

```text
materialization_semantics == smoke_proxy
```

The M2118 panel correctly uses:

```text
materialization_semantics == comparison_support_smoke_proxy
```

M2121 should therefore implement a comparison-support-specific reset validator
that reuses the same low-level reset helper but accepts the M2118 semantics and
preserves all candidate-support metadata.

## Frozen Command

M2121 must implement and run exactly:

```bash
PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight \
  --executable-task-specs runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight \
  --eval-seed-base 212100 \
  --target-spec-count 240 \
  --expected-observation-dim 72 \
  --next-blocker m2122-paper-route-outcome-supported-decisive-comparison-support-reset-validation-result-audit
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight.py
```

## Planned Artifacts

M2121 must write:

```text
runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight/summary.json
runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight/reset_rows.csv
runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight/reset_failure_rows.csv
runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight/contract_rows.csv
runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight/reset_distribution_by_intent.csv
runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight/reset_distribution_by_source_kind.csv
runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight/reset_distribution_by_proxy_template.csv
runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight/reset_distribution_by_generated_proxy.csv
runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight/metadata_missing_rows.csv
runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight/claim_boundary.csv
```

## Pass Gates

M2121 passes only if:

```text
result_class == comparison_support_reset_validation_preflight_pass
input_executable_spec_count == 240
target_executable_spec_count == 240
reset_attempt_count == 240
reset_success_count == 240
reset_failure_count == 0
observation_dimension_failure_count == 0
observation_finite_count == 240
obstacle_initialized_count == 240
contract_violation_count == 0
metadata_missing_count == 0
forbidden_key_violation_count == 0
intent_quota_pass == true
source_kind_quota_pass == true
proxy_template_quota_pass == true
generated_proxy_quota_pass == true
guardrail_violation_count == 0
```

Reset validation may claim only scenario reset admissibility if audited later.
It remains non-comparison evidence.

## Claim Boundary

Supported after a clean M2121 run:

```text
comparison-support materialized scenario specs reset successfully with finite
72-dimensional observations and initialized obstacles.
```

Unsupported:

```text
measured execution;
policy behavior;
comparison-ready support;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2121-paper-route-outcome-supported-decisive-comparison-support-reset-validation-implementation-and-run
```
