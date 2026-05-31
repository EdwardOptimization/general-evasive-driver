# M2079 Paper-Route Outcome-Supported Decisive Seed-Robust Repaired Reset Validation Implementation and Run

- status: completed
- decision: `seed_robust_repaired_reset_validation_fail_route_to_result_audit`
- run artifact: `runs/m2079_paper_route_outcome_supported_decisive_seed_robust_repaired_reset_validation_preflight/summary.json`
- failure taxonomy: `scenario_sampling_failure`, `seed_fragility`
- focused tests: `2 passed`
- reset/rollout/measured execution in M2079: reset-only `true`, rollout/measured `false`
- policy actions executed in M2079: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Run Result

M2079 ran the frozen M2078 fresh-seed reset-only command over the M2076
seed-robust repaired specs:

```text
result_class: outcome_supported_decisive_reset_validation_preflight_fail
input_executable_spec_count: 240
target_executable_spec_count: 240
reset_attempt_count: 240
reset_success_count: 234
reset_failure_count: 6
observation_finite_count: 234
obstacle_initialized_count: 234
observation_dimension_failure_count: 0
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
family_quota_pass: true
split_quota_pass: true
difficulty_axis_coverage_pass: true
```

All failures share one reset-time class:

```text
RuntimeError failed to sample an obstacle scenario matching the configured filters: 6
```

## Failure Distribution

Failure by family:

```text
T1_reactive_active_safety: 2
T2_same_current_different_older_history: 2
T4_variable_diagnostic_delay: 2
```

Failure by source kind:

```text
curved_road_reactive_evasion: 2
same_current_rear_lateral_authority_older_history: 2
long_delay_steer_lag_evidence: 2
```

All six failures share the same difficulty pattern:

```text
obstacle_distance_band: late
road_width_band: generous
curvature_band: moderate
initial_speed_band: low
dynamics_band: mixed_mu or nominal_mu
```

Failing task IDs:

```text
m2063-osd-osd_v0_0011_t1
m2063-osd-osd_v0_0023_t1
m2063-osd-osd_v0_0058_t2
m2063-osd-osd_v0_0076_t2
m2063-osd-osd_v0_0170_t4
m2063-osd-osd_v0_0200_t4
```

## Interpretation

M2076's no-reset seed-support repair helped substantially:

```text
M2073 reset success before seed-robust repair: 164/240
M2079 reset success after seed-robust repair: 234/240
```

But `5/5` grid support was still not sufficient for full fresh-seed reset
validity. The remaining problem is likely acceptance density inside the repaired
windows, not actor contract, metadata, warmup schema, observation dimension, or
guardrail loss.

This is still not controller evidence. No policy action or rollout happened.

## Supported Claims

Supported:

```text
Seed-robust no-reset repair improved reset success from 164/240 to 234/240.
The remaining blocker is a small fresh-seed obstacle sampling failure set.
The repaired panel still preserves metadata, quotas, contract, and guardrails.
```

Unsupported:

```text
reset-validity of the 240-spec panel;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Route Decision

Selected:

```text
route_to_seed_robust_repaired_reset_validation_result_audit
```

M2080 must audit the six failures before another repair, reset rerun, or any
measured execution design.

Rejected:

```text
direct measured execution:
  rejected because reset success is 234/240, not 240/240.

repair and rerun inside M2079:
  rejected because M2079 must fail closed and route to audit.

driver capability interpretation:
  rejected because no policy action or rollout was executed.
```

## Next

Next milestone:

```text
m2080-paper-route-outcome-supported-decisive-seed-robust-repaired-reset-validation-result-audit
```
