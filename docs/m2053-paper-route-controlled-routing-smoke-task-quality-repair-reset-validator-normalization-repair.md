# M2053 Paper-Route Controlled Routing Smoke Task-Quality Repair Reset Validator Normalization Repair

- status: completed
- decision: `controlled_routing_smoke_task_quality_repair_reset_validator_normalization_pass_route_to_result_audit_and_synthesis`
- result class: `controlled_routing_smoke_reset_validation_preflight_pass`
- repaired file: `src/autodrift/paper_route_controlled_routing_smoke_reset_validation_preflight.py`
- focused tests: `2 passed`
- summary: `runs/m2053_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/summary.json`
- reset execution in M2053: `true`
- rollout/measured execution in M2053: `false`
- policy actions executed in M2053: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Repair

M2053 canonicalizes `paper_validity_claim` when building generated-proxy
aggregate keys:

```text
paper_claim = str(paper_validity_claim).strip().lower()
```

This keeps expected generated-proxy counts and observed reset-row counts in the
same key space. It does not change scenario geometry, controller profiles,
actor inputs, rollout logic, policy actions, or measured execution.

Focused regression coverage now includes raw spec values such as
`paper_validity_claim="False"` and verifies that expected and observed
generated-proxy counts compare equal after canonicalization.

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_controlled_routing_smoke_reset_validation_preflight.py
```

Result:

```text
2 passed
```

Repaired reset-only rerun:

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_reset_validation_preflight \
  --executable-task-specs runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m2053_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight \
  --eval-seed-base 205300 \
  --target-spec-count 192 \
  --expected-observation-dim 72 \
  --next-blocker m2054-paper-route-controlled-routing-smoke-task-quality-repair-reset-validator-normalization-result-audit
```

Result:

```text
result_class=controlled_routing_smoke_reset_validation_preflight_pass
reset_attempt_count=192
reset_success_count=192
reset_failure_count=0
contract_violation_count=0
metadata_missing_count=0
guardrail_violation_count=0
```

## Pass Gates

The repaired reset-validation run passes the registered gates:

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
generated_proxy_quota_pass: true
guardrail_violation_count: 0
```

Generated-proxy aggregate keys are now canonical on both sides:

```text
generated=false|semantics=smoke_proxy|paper_claim=false: 170
generated=true|semantics=smoke_proxy|paper_claim=false: 22
```

## Supported Claims

Supported:

```text
The M2051 fail class is repaired as a validator metric artifact.
The M2048 repaired 192-spec panel is reset-valid under the repaired validator.
The repaired reset run preserves metadata and human-view actor contract guards.
```

Unsupported:

```text
rollout validity;
measured execution success;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark result;
level3 self-identification.
```

## Next

M2054 should audit M2053 and synthesize the task-quality repair branch before
moving to measured-execution command design. The branch has now accumulated a
full repair path from offtrack localization to repaired materialization and
reset-validity evidence, so the next decision should not be another narrow
adapter milestone unless the audit finds a real blocker.
