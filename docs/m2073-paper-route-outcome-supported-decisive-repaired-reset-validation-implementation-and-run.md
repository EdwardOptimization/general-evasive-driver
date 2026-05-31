# M2073 Paper-Route Outcome-Supported Decisive Repaired Reset Validation Implementation and Run

- status: completed
- decision: `outcome_supported_decisive_repaired_reset_validation_fail_route_to_result_audit`
- run artifact: `runs/m2073_paper_route_outcome_supported_decisive_repaired_reset_validation_preflight/summary.json`
- failure taxonomy: `scenario_sampling_failure`, `seed_fragility`
- focused tests: `2 passed`
- reset/rollout/measured execution in M2073: reset-only `true`, rollout/measured `false`
- policy actions executed in M2073: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Run Result

M2073 ran the frozen M2072 reset-only command over the M2070 repaired specs:

```text
result_class: outcome_supported_decisive_reset_validation_preflight_fail
input_executable_spec_count: 240
target_executable_spec_count: 240
reset_attempt_count: 240
reset_success_count: 164
reset_failure_count: 76
observation_finite_count: 164
observation_dimension_failure_count: 0
obstacle_initialized_count: 164
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
```

Distribution gates remain clean:

```text
family_quota_pass: true
split_quota_pass: true
difficulty_axis_coverage_pass: true
```

All failures share one reset-time class:

```text
RuntimeError failed to sample an obstacle scenario matching the configured filters: 76
```

Family-level failure counts:

```text
T1_reactive_active_safety: 17
T2_same_current_different_older_history: 18
T3_active_diagnostic_warmup: 23
T4_variable_diagnostic_delay: 11
T5_terminal_boundary_near_constraint: 7
```

## Interpretation

M2070's repair was useful but seed-fragile. It moved reset success from M2066's
`0/240` to `164/240`, but M2073 used a fresh eval seed base (`207300`) while
the M2070 deterministic repair was calibrated against M2066 reset-failure seeds
(`206600` series).

This suggests the repaired obstacle filters are too seed-specific:

```text
the repaired specs are feasible for the scanned seed state,
but not robust across fresh reset RNG states.
```

This is still not controller evidence. No policy action or rollout happened.

## Supported Claims

Supported:

```text
The warmup-gate schema repair holds under reset validation; there are no warmup max_active_steps failures.
The repair substantially improves reset feasibility, from 0/240 to 164/240.
The remaining blocker is scenario sampling under fresh seeds, not metadata, actor contract, or guardrail loss.
```

Unsupported:

```text
reset-validity of the repaired panel;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification;
paper-valid generated task semantics.
```

## Route Decision

Selected:

```text
route_to_repaired_reset_validation_result_audit
```

M2074 must audit the remaining `76` reset failures before any repair or rerun.
The likely next question is whether the obstacle repair should target seed-robust
feasibility windows rather than exact seed-specific accepted points.

Rejected:

```text
direct measured execution:
  rejected because reset success is only 164/240.

repair and rerun inside M2073:
  rejected because M2073 must fail closed and route to audit.

driver capability interpretation:
  rejected because no policy action or rollout was executed.
```

## Next

Next milestone:

```text
m2074-paper-route-outcome-supported-decisive-repaired-reset-validation-result-audit
```
