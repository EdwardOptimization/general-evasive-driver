# M2086 Paper-Route Outcome-Supported Decisive Density-Aware Repaired Reset Validation Result Audit and Synthesis

- status: completed
- decision: `pivot_to_reset_valid_core_panel_reduction_design`
- synthesis decision: `pivot`
- audited artifact: `runs/m2085_paper_route_outcome_supported_decisive_density_aware_repaired_reset_validation_preflight/summary.json`
- failure taxonomy: `scenario_sampling_failure`, `seed_fragility`
- reset/rollout/measured execution in M2086: `false`
- policy actions executed in M2086: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

The outcome-supported decisive task-distribution branch made real reset-validity
progress, but did not reach a full 240/240 reset-valid panel:

```text
M2066 original reset validation: 0/240
M2073 repaired reset validation: 164/240
M2079 seed-robust repaired reset validation: 234/240
M2085 density-aware repaired reset validation: 238/240
```

M2085 preserved the important boundaries:

```text
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started/replay_started/ppo_used: false
```

The two remaining failures are both public-debug generated rows:

```text
m2063-osd-osd_v0_0002_t1
m2063-osd-osd_v0_0049_t2
```

The public-gate split remains intact under the M2085 reset run:

```text
public_gate rows: 96
public_gate reset failures: 0
public_debug reset failures: 2
```

## M2085 Failure Audit

M2085 failed closed with:

```text
reset_attempt_count: 240
reset_success_count: 238
reset_failure_count: 2
observation_finite_count: 238
obstacle_initialized_count: 238
observation_dimension_failure_count: 0
family_quota_pass: true
split_quota_pass: true
difficulty_axis_coverage_pass: true
dynamics_quota_pass: true
source_kind_quota_pass: true
```

Both failures share:

```text
error: RuntimeError failed to sample an obstacle scenario matching the configured filters
obstacle_distance_band: late
road_width_band: generous
curvature_band: moderate
dynamics_band: low_mu
initial_speed_band: low
```

Failure source kinds:

```text
low_mu_reactive_evasion: 1
same_current_yaw_authority_older_history: 1
```

Interpretation:

```text
The blocker is still task/sampler validity, not actor input contract, metadata,
observation dimension, rollout behavior, or controller performance.
```

## Supported Claims

Supported:

```text
The branch improved reset feasibility from 0/240 to 238/240.
All 96 public-gate rows reset successfully in M2085.
The remaining failures are two public-debug low-mu late/generous/moderate/low rows.
The actor-input contract, metadata, quota, and guardrail boundaries stayed intact.
No policy-action or driver-performance claim has been made.
```

## Falsified Claims

Falsified:

```text
Single-seed exact obstacle feasibility is sufficient for reset validity.
5/5 existence-only support is sufficient for full fresh-seed reset validity.
5/5 density-aware support with minimum accepted grid cells >= 80 is sufficient for full 240/240 reset validity.
The 240-row generated panel is ready for measured execution.
Continuing local obstacle-filter repair is still the right next step.
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
generated-row reset-sampling fragility after local obstacle-filter repair
```

This is not a contract violation, metric artifact, training instability, or
behavior regression. No controller behavior has been measured in this branch.

## Public Gate Overfit Risk

Risk is high if the project continues local obstacle-filter repair.

Reasons:

```text
The branch has repaired public generated rows multiple times.
M2076 support improved reset validity but did not fully generalize.
M2082 density support improved reset validity but still did not fully generalize.
The residual failures moved to different rows, suggesting the 240-row generated panel is brittle under fresh reset seeds.
```

Mitigation:

```text
Close the local repair loop.
Preserve the M2085 reset-valid evidence.
Pivot to a reset-valid core panel reduction instead of changing more obstacle filters.
Do not run measured execution until the reduced panel is explicitly materialized and audited.
```

## Next Branch Decision

Decision:

```text
pivot
```

Selected next route:

```text
M2087 reset-valid core panel reduction design
```

The design should:

```text
extract a reduced panel from M2085 reset-success rows;
preserve all 96 public-gate rows;
exclude the two reset-failed public-debug rows;
avoid changing obstacle filters;
keep provenance and claim-boundary metadata;
define whether the reduced core is 238 rows or a stricter public-gate-only subset;
block measured execution until the reduced panel is materialized and audited.
```

Rejected routes:

```text
another local obstacle-filter repair:
  rejected because M2084 made M2085 decisive and M2085 still failed scenario sampling.

direct measured execution on 240 rows:
  rejected because reset success is 238/240.

paper-level claim from reset evidence:
  rejected because these are generated smoke-proxy tasks and no rollout has happened.
```

## Next

Next milestone:

```text
m2087-paper-route-outcome-supported-decisive-reset-valid-core-panel-reduction-design
```
