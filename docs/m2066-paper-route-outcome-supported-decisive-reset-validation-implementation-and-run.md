# M2066 Paper-Route Outcome-Supported Decisive Reset Validation Implementation and Run

- status: completed
- decision: `outcome_supported_decisive_reset_validation_fail_route_to_result_audit`
- run artifact: `runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/summary.json`
- failure taxonomy: `scenario_sampling_failure`
- focused tests: `2 passed`
- reset/rollout/measured execution in M2066: reset-only `true`, rollout/measured `false`
- policy actions executed in M2066: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2066 implements a focused reset-only validator:

```text
autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight
```

It preserves the M2063 outcome-supported decisive task metadata and reuses the
low-level executable-v2 reset helper. The validator writes reset rows, failure
rows, contract rows, metadata-missing rows, distribution summaries, a claim
boundary file, and `summary.json`.

One validator normalization was repaired during implementation: registered
split quota checks now treat explicit zero-target splits such as
`private_holdout: 0` as satisfied when no rows are present. This avoids a false
secondary failure while leaving the real reset failures unchanged.

## Run Result

M2066 ran the frozen M2065 reset-only command over the M2063 `240` executable
specs:

```text
result_class: outcome_supported_decisive_reset_validation_preflight_fail
input_executable_spec_count: 240
target_executable_spec_count: 240
reset_attempt_count: 240
reset_success_count: 0
reset_failure_count: 240
observation_finite_count: 0
observation_dimension_failure_count: 0
obstacle_initialized_count: 0
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
```

Distribution and registered quota checks after the zero-quota normalization:

```text
family_quota_pass: true
split_quota_pass: true
difficulty_axis_coverage_pass: true
registered_family_quota_pass: true
registered_split_quota_pass: true
registered_difficulty_axis_coverage_pass: true
```

Failure distribution:

```text
RuntimeError failed to sample an obstacle scenario matching the configured filters: 123
ValueError warmup_gate max_active_steps must be positive: 117
```

## Interpretation

This is not evidence about controller quality, driver capability, paper-level
performance, finite-window-vs-GRU behavior, or self-identification.

The useful result is narrower:

```text
M2066 proves that the focused validator works and preserves metadata/claim
guards, but the M2063 materialized smoke-proxy specs are not reset-valid under
the current executable environment schema.
```

The two reset failure classes point to different repair questions:

```text
warmup_gate max_active_steps must be positive:
  likely materialization schema invalidity for warmup-gated proxy env configs.

failed to sample an obstacle scenario matching the configured filters:
  likely source/filter feasibility mismatch in the generated smoke-proxy specs.
```

## Supported Claims

Supported:

```text
The focused validator can execute the M2063 schema without metadata or claim-boundary loss.
The M2063 panel is not reset-valid as materialized.
No forbidden rollout, policy action, training, replay, PPO, ranking, or paper claim was executed.
```

Unsupported:

```text
reset-validity of the M2063 panel;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Route Decision

Selected:

```text
route_to_reset_validation_result_audit
```

M2067 must audit the failure rows before any repair or rerun. It should decide
whether the next correction is:

```text
materialization schema repair for invalid warmup-gate configs;
source/filter repair for unsampleable obstacle scenarios;
or a combined task-quality materialization repair.
```

Rejected:

```text
direct measured execution:
  rejected because reset success is 0/240.

accepting M2063 as reset-valid:
  rejected because all reset attempts failed.

driver or controller interpretation:
  rejected because no policy action or rollout was executed.

repair and rerun inside M2066:
  rejected because M2065 required fail-closed routing to a result audit.
```

## Next

Next milestone:

```text
m2067-paper-route-outcome-supported-decisive-reset-validation-result-audit
```
