# M2091 Paper-Route Outcome-Supported Decisive Reset-Valid Core Reset Validation Implementation and Run

- status: completed
- decision: `reset_valid_core_reset_validation_fail_route_to_result_audit`
- run artifact: `runs/m2091_paper_route_outcome_supported_decisive_reset_valid_core_reset_validation_preflight/summary.json`
- failure taxonomy: `scenario_sampling_failure`, `seed_fragility`
- focused tests: `2 passed`
- reset/rollout/measured execution in M2091: reset-only `true`, rollout/measured `false`
- policy actions executed in M2091: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Run Result

M2091 ran the frozen M2090 fresh reset-only command over the M2088 reduced
238-row panel:

```text
result_class: outcome_supported_decisive_reset_validation_preflight_fail
input_executable_spec_count: 238
target_executable_spec_count: 238
reset_attempt_count: 238
reset_success_count: 236
reset_failure_count: 2
observation_finite_count: 236
obstacle_initialized_count: 236
observation_dimension_failure_count: 0
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
family_quota_pass: true
split_quota_pass: true
difficulty_axis_coverage_pass: true
dynamics_quota_pass: true
source_kind_quota_pass: true
```

All failures share one reset-time class:

```text
RuntimeError failed to sample an obstacle scenario matching the configured filters: 2
```

## Failure Rows

Failing task IDs:

```text
m2063-osd-osd_v0_0070_t2
m2063-osd-osd_v0_0129_t3
```

Failure slice:

```text
source_split: public_debug
obstacle_distance_band: late
road_width_band: generous
curvature_band: moderate
dynamics_band: mixed_mu
initial_speed_band: low
```

Failure by family and source kind:

```text
T2_same_current_different_older_history / same_current_rear_lateral_authority_older_history: 1
T3_active_diagnostic_warmup / warmup_throttle_release_response: 1
```

All `96` public-gate rows remain reset-success rows in M2091.

## Interpretation

The reduced panel is still not fresh-seed stable:

```text
M2085 full panel reset validation: 238/240
M2091 reduced panel fresh reset validation: 236/238
```

The persistent pattern is that public-debug generated rows fail under fresh
seed bases while public-gate rows keep passing. This is still task/sampler
validity evidence, not driver evidence. No policy action or rollout happened.

## Supported Claims

Supported:

```text
The reduced panel preserves contract, metadata, and guardrails under reset validation.
All public-gate rows reset successfully in M2091.
The remaining failure mode is public-debug scenario sampling fragility.
```

Unsupported:

```text
fresh reset-validity of the 238-row reduced panel;
measured execution readiness for the reduced panel;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Route Decision

Selected:

```text
route_to_reset_valid_core_reset_validation_result_audit
```

M2092 must audit the two residual failures and decide whether to pivot to a
public-gate-only panel or redesign the scenario distribution. It must not route
to another obstacle-filter repair.

Rejected:

```text
direct measured execution on the 238-row panel:
  rejected because reset success is 236/238, not 238/238.

repair and rerun inside M2091:
  rejected because M2091 must fail closed and route to audit.

driver capability interpretation:
  rejected because no policy action or rollout was executed.
```

## Next

Next milestone:

```text
m2092-paper-route-outcome-supported-decisive-reset-valid-core-reset-validation-result-audit
```
