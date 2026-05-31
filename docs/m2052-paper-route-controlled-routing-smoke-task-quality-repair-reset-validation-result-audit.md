# M2052 Paper-Route Controlled Routing Smoke Task-Quality Repair Reset Validation Result Audit

- status: completed
- decision: `controlled_routing_smoke_task_quality_repair_reset_audit_route_to_generated_proxy_key_normalization_repair`
- audited summary: `runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/summary.json`
- failure taxonomy: `metric_artifact`
- reset/rollout/measured execution in M2052: `false`
- policy actions executed in M2052: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result Audit

M2051 ran the frozen reset-only command and failed closed:

```text
result_class: controlled_routing_smoke_reset_validation_preflight_fail
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
guardrail_violation_count: 0
```

The following distribution gates passed:

```text
family_quota_pass: true
source_kind_quota_pass: true
proxy_template_quota_pass: true
```

The only failing gate is:

```text
generated_proxy_quota_pass: false
```

## Failure Classification

This is not a scenario, reset, contract, or materialization failure. It is a
metric artifact in the validator's aggregate-key comparison.

Expected keys are built from raw executable spec values:

```text
generated=false|semantics=smoke_proxy|paper_claim=False: 170
generated=true|semantics=smoke_proxy|paper_claim=False: 22
```

Reset-row keys are built from normalized metadata:

```text
generated=false|semantics=smoke_proxy|paper_claim=false: 170
generated=true|semantics=smoke_proxy|paper_claim=false: 22
```

Counts match exactly under case-normalized `paper_claim`. The validator should
compare canonicalized generated-proxy keys on both sides.

## Supported Claims

Supported:

```text
M2051 proves that all 192 repaired specs can be reset without reset failures.
The actor-input contract, metadata presence, forbidden-key, and guardrail checks are clean.
The M2051 result_class failure is caused by generated-proxy aggregate-key normalization.
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

## Route Decision

Selected:

```text
route_to_generated_proxy_key_normalization_repair_and_rerun
```

M2053 should make a narrowly scoped validator repair:

```text
canonicalize `paper_validity_claim` when computing expected generated-proxy counts;
add a regression test with capitalized raw spec values and normalized reset-row keys;
rerun the exact M2051 reset-only command into a new M2053 run directory.
```

Rejected:

```text
materialization repair:
  rejected because M2048 specs are metadata-complete and reset-clean.

scenario/task-quality repair:
  rejected because no reset, contract, or guardrail failure occurred.

accepting M2051 as pass without code repair:
  rejected because the registered validator summary result_class is fail.

measured execution or ranking:
  rejected because formal reset-validity pass has not yet been regenerated.
```

Controller ranking, finite-window-vs-GRU, paper-level comparison, and level3
self-ID claims remain blocked.

## Next

Next milestone:

```text
m2053-paper-route-controlled-routing-smoke-task-quality-repair-reset-validator-normalization-repair
```
