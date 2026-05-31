# M2051 Paper-Route Controlled Routing Smoke Task-Quality Repair Reset Validation Implementation And Run

- status: completed
- decision: `controlled_routing_smoke_task_quality_repair_reset_validation_fail_route_to_result_audit`
- result class: `controlled_routing_smoke_reset_validation_preflight_fail`
- validator: `autodrift.paper_route_controlled_routing_smoke_reset_validation_preflight`
- focused tests: `1 passed`
- summary: `runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/summary.json`
- reset execution in M2051: `true`
- rollout/measured execution in M2051: `false`
- policy actions executed in M2051: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_controlled_routing_smoke_reset_validation_preflight.py
```

Result:

```text
1 passed
```

Frozen reset-only command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_reset_validation_preflight \
  --executable-task-specs runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight \
  --eval-seed-base 205100 \
  --target-spec-count 192 \
  --expected-observation-dim 72 \
  --next-blocker m2052-paper-route-controlled-routing-smoke-task-quality-repair-reset-validation-result-audit
```

Result:

```text
result_class=controlled_routing_smoke_reset_validation_preflight_fail
reset_attempt_count=192
reset_success_count=192
reset_failure_count=0
contract_violation_count=0
metadata_missing_count=0
guardrail_violation_count=0
```

## Reset Evidence

The actual reset path is clean:

```text
input_executable_spec_count: 192
target_executable_spec_count: 192
reset_attempt_count: 192
reset_success_count: 192
reset_failure_count: 0
observation_finite_count: 192
observation_dimension_failure_count: 0
obstacle_initialized_count: 192
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
family_quota_pass: true
source_kind_quota_pass: true
proxy_template_quota_pass: true
guardrail_violation_count: 0
```

No rollout, policy actions, measured execution, training, replay, PPO,
promotion, private holdout, actor-input change, profile tuning, ranking,
paper-level claim, finite-window-vs-GRU conclusion, or level3 self-ID claim
occurred.

## Failure Localization

The fail class is caused by one aggregate quota key mismatch:

```text
generated_proxy_quota_pass: false
```

Expected keys in the summary use capitalized boolean strings from raw spec
values:

```text
generated=false|semantics=smoke_proxy|paper_claim=False: 170
generated=true|semantics=smoke_proxy|paper_claim=False: 22
```

Observed reset-row keys normalize `paper_validity_claim` to lowercase:

```text
generated=false|semantics=smoke_proxy|paper_claim=false: 170
generated=true|semantics=smoke_proxy|paper_claim=false: 22
```

Counts match exactly after case normalization. M2051 still fails closed because
the registered pass gate requires the validator summary to pass as written.

## Supported Claims

Supported:

```text
The frozen reset-only command executed.
All 192 repaired specs reset successfully with finite 72-dim observations.
Metadata, actor-contract, forbidden-key, and guardrail checks are clean.
The only observed fail condition is generated-proxy aggregate key normalization.
```

Unsupported:

```text
formal reset-validity pass for the repaired panel;
rollout validity;
measured execution success;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark result;
level3 self-identification.
```

## Next

M2052 must audit the failure before any repair or rerun. The likely route is a
validator key-normalization repair or audit-accepted normalization rule, not a
scenario/task-quality repair.
