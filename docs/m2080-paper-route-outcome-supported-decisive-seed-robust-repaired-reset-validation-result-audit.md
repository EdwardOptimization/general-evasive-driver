# M2080 Paper-Route Outcome-Supported Decisive Seed-Robust Repaired Reset Validation Result Audit and Synthesis

- status: completed
- decision: `continue_to_one_bounded_density_aware_repair_design`
- synthesis decision: `continue`
- audited artifact: `runs/m2079_paper_route_outcome_supported_decisive_seed_robust_repaired_reset_validation_preflight/summary.json`
- failure taxonomy: `scenario_sampling_failure`, `seed_fragility`
- reset/rollout/measured execution in M2080: `false`
- policy actions executed in M2080: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

This branch has made real task-validity progress:

```text
M2066 original reset validation: 0/240 success
M2070 no-reset single-seed repair: 240/240 scenario-filter feasible
M2073 repaired reset validation: 164/240 success
M2076 no-reset seed-support repair: 240/240 specs with 5/5 support seeds
M2079 fresh-seed reset validation: 234/240 success
```

The current blocker is no longer broad task invalidity. It is six residual
fresh-seed obstacle sampling failures.

## M2079 Failure Audit

M2079 failed closed with:

```text
reset_attempt_count: 240
reset_success_count: 234
reset_failure_count: 6
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
family_quota_pass: true
split_quota_pass: true
difficulty_axis_coverage_pass: true
```

All six failures share:

```text
error: RuntimeError failed to sample an obstacle scenario matching the configured filters
obstacle_distance_band: late
road_width_band: generous
curvature_band: moderate
initial_speed_band: low
```

Failing source kinds:

```text
curved_road_reactive_evasion: 2
same_current_rear_lateral_authority_older_history: 2
long_delay_steer_lag_evidence: 2
```

The M2076 support rows show that these rows had support, but several support
seeds had very low accepted grid density:

```text
lowest accepted grid cell counts among failed rows: 2, 2, 4, 6, 8, 8, 9
lowest accepted grid cell fraction: 0.00032077
```

Interpretation:

```text
M2076 proved existence of accepted grid cells.
M2079 shows existence is not enough for reset sampler reliability.
The next repair target should be accepted-region density, not another existence-only support scan.
```

## Supported Claims

Supported:

```text
The branch improved reset feasibility from 0/240 to 234/240.
The remaining failures are localized and sparse.
The actor-input contract, metadata, quota, and guardrail boundaries are still intact.
No policy-action or driver-performance claim has been made.
```

## Falsified Claims

Falsified:

```text
Single-seed exact obstacle feasibility is sufficient for reset validity.
5/5 existence-only grid support is sufficient for full fresh-seed reset validity.
The repaired panel is ready for measured execution.
```

Not tested:

```text
controller-family ranking;
finite-window vs GRU;
closed-loop self-identification;
paper-level benchmark claims.
```

## Failure Taxonomy Summary

Current active failure taxonomy:

```text
scenario_sampling_failure
seed_fragility
```

Operational subtype:

```text
support_window_density_failure
```

This is not a contract violation, metric artifact, training instability, or
behavior regression. No controller behavior has been measured in this branch.

## Public Gate Overfit Risk

Risk is medium.

Reasons:

```text
The branch has repeated task-materialization repair on public generated rows.
M2076 support seeds improved reset validity but did not fully generalize to M2079.
The remaining six rows are narrow enough that overfitting is possible.
```

Mitigation:

```text
Allow exactly one bounded density-aware repair design/implementation/reset cycle.
Require the next reset rerun to use a fresh seed base outside both M2076 support seeds and M2079 seed base.
If that reset still fails scenario sampling, stop this local repair branch and pivot or reduce the panel through synthesis.
```

## Next Branch Decision

Decision:

```text
continue
```

Allowed next route:

```text
M2081 density-aware obstacle-filter repair design
```

The repair must target the six M2079 failures and must preserve all 240 specs,
metadata, quota, and claim guards. It may not run reset or measured execution.
It must replace the existence-only support criterion with a density-aware
criterion, for example:

```text
minimum accepted grid cells per support seed;
minimum accepted grid-cell fraction;
bounded threshold-score escalation up to 1.0;
fresh validation seed base reserved for the next reset command.
```

Stop condition:

```text
If density-aware repair cannot specify a bounded criterion, or if the following
fresh reset validation still fails scenario sampling, synthesize and stop or
reduce the panel rather than continuing local repair.
```

## Next

Next milestone:

```text
m2081-paper-route-outcome-supported-decisive-density-aware-obstacle-filter-repair-design
```
