# M2085 Paper-Route Outcome-Supported Decisive Density-Aware Repaired Reset Validation Implementation and Run

- status: completed
- decision: `density_aware_repaired_reset_validation_fail_route_to_synthesis_audit`
- run artifact: `runs/m2085_paper_route_outcome_supported_decisive_density_aware_repaired_reset_validation_preflight/summary.json`
- failure taxonomy: `scenario_sampling_failure`, `seed_fragility`
- focused tests: `2 passed`
- reset/rollout/measured execution in M2085: reset-only `true`, rollout/measured `false`
- policy actions executed in M2085: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Run Result

M2085 ran the frozen M2084 fresh-seed reset-only command over the M2082
density-aware repaired specs:

```text
result_class: outcome_supported_decisive_reset_validation_preflight_fail
input_executable_spec_count: 240
target_executable_spec_count: 240
reset_attempt_count: 240
reset_success_count: 238
reset_failure_count: 2
observation_finite_count: 238
obstacle_initialized_count: 238
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
m2063-osd-osd_v0_0002_t1
m2063-osd-osd_v0_0049_t2
```

Failure slice:

```text
obstacle_distance_band: late
road_width_band: generous
curvature_band: moderate
dynamics_band: low_mu
initial_speed_band: low
```

Failure by family and source kind:

```text
T1_reactive_active_safety / low_mu_reactive_evasion: 1
T2_same_current_different_older_history / same_current_yaw_authority_older_history: 1
```

Both failures are public-debug generated rows. They are not contract,
observation-dimension, metadata, forbidden-key, or guardrail failures.

## Interpretation

The density-aware repair improved the reset-validity branch, but not enough to
pass:

```text
M2066 original reset validation: 0/240
M2073 repaired reset validation: 164/240
M2079 seed-robust repaired reset validation: 234/240
M2085 density-aware repaired reset validation: 238/240
```

This is still meaningful task-validity progress, but M2084 explicitly made this
rerun decisive for local obstacle-filter repair. The residual failures moved to
two low-mu late/generous/moderate/low rows, so another narrow repair would be a
local-search continuation rather than a clean evidence expansion.

No policy action, rollout, measured execution, ranking, paper-level claim, or
self-ID claim happened in M2085.

## Supported Claims

Supported:

```text
Density-aware no-reset repair improved reset success from 234/240 to 238/240.
The remaining blocker is a small fresh-seed obstacle scenario-sampling failure set.
The 240-spec panel still preserves metadata, quotas, contract, and guardrails.
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
route_to_density_aware_repaired_reset_validation_synthesis_audit
```

M2086 must audit and synthesize the failure before any measured execution,
panel reduction, or new distribution work.

Rejected:

```text
direct measured execution:
  rejected because reset success is 238/240, not 240/240.

another local obstacle-filter repair:
  rejected by the M2084 stop rule after the decisive fresh-seed reset rerun.

driver capability interpretation:
  rejected because no policy action or rollout was executed.
```

## Next

Next milestone:

```text
m2086-paper-route-outcome-supported-decisive-density-aware-repaired-reset-validation-result-audit
```
