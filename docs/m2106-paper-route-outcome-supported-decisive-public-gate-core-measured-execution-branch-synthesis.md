# M2106 Paper-Route Outcome-Supported Decisive Public-Gate Core Measured Execution Branch Synthesis

- status: completed
- decision: `public_gate_core_measured_execution_branch_synthesis_continue_to_repaired_command_design`
- synthesis_decision: `continue`
- reset/rollout/measured execution in M2106: `false`
- policy actions executed in M2106: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2094 extracted a compact public-gate core panel from reset-valid evidence:

```text
public_gate_core_executable_spec_count: 96
planned_sentinel_workload_count: 480
public_gate_included_count: 96
public_debug_excluded_count: 142
core axes: 12 axes x 8 rows each
dynamics counts: actuator_delay 24, low_mu 24, mixed_mu 24, nominal_mu 24
env_config_changed_count: 0
guardrail_violation_count: 0
```

M2101 then ran the first measured execution over this public-gate core route,
but the artifact was incomplete:

```text
episode_count: 478 / 480
failure_count: 2
metadata_missing_count: 480
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

The two failed cells were scenario sampling failures, not policy-performance
results:

```text
m2063-osd-osd_v0_0162_t3::L2_window_50
m2063-osd-osd_v0_0235_t5::L3_online_gru
```

M2104 repaired both active blockers without rollout:

```text
compatible_spec_count: 96
compatible_workload_count: 480
metadata_missing_count: 0
validation_failure_count: 0
eval_seed_override_count: 2
env_config_changed_count: 0
guardrail_violation_count: 0
```

The two seed overrides are exactly the M2091 reset-success seeds for the failed
cells:

```text
m2063-osd-osd_v0_0162_t3::L2_window_50 -> 210260
m2063-osd-osd_v0_0235_t5::L3_online_gru -> 210333
```

M2105 audited the repair as clean and preserved the claim boundary: no reset,
rollout, measured execution, policy action, ranking, paper claim, or self-ID
claim was made by the repair or audit.

## Supported Claims

Supported:

```text
The public-gate core measured-execution branch has a 96-spec / 480-workload
repaired artifact set that is metadata-complete, preserves controller profiles
and env configs, and carries exactly two targeted reset-success seed overrides.
```

Also supported:

```text
The earlier M2101 measured run is useful as an incomplete diagnostic: it proved
runner routing for 478 cells and localized the remaining blockers to metadata
completeness plus two scenario sampling failures.
```

## Falsified Claims

Falsified or rejected:

```text
The M2098-compatible artifacts were already sufficient for complete measured
execution.
```

Also rejected:

```text
The incomplete M2101 outcome distribution is sufficient for controller ranking
or paper-level comparison.
```

The branch also rejected further public-debug filter repair as the immediate
route. The public-gate core panel deliberately excludes public-debug reset
fragility and keeps the evidence scope narrow.

## Failure Taxonomy Summary

Observed failure types in this branch:

```text
scenario_sampling_failure: two M2101 workload cells
lineage_invalid / metadata_completeness_gap: 480 M2101 rows missing strict
metadata fields
local_search_risk: medium-to-high because several milestones repaired a narrow
execution artifact path
```

The active blockers are repaired by M2104/M2105. No current evidence shows an
actor-input contract violation, env_config mutation, profile-specific tuning,
metric-completeness failure, or guardrail violation.

## Public-Gate Overfit Risk

Risk remains meaningful:

```text
public-gate core is a fixed 96-row panel;
workload rows are generated smoke proxies, not paper-valid generated tasks;
there is no private holdout in this branch;
the branch measures execution infrastructure before paper-level comparison.
```

Therefore, repaired measured execution can support infrastructure readiness and
diagnostic controller-family behavior on the public-gate core panel, but it
cannot by itself support paper-level performance, finite-window-vs-GRU, or
level3 self-identification claims.

## Next Branch Decision

Decision:

```text
continue
```

Continue only to repaired measured-execution command design over the M2104
repaired artifacts. Do not add another local metadata/sampling repair before
the rerun route is frozen. Do not rank controllers until a complete repaired
measured execution exists and is separately audited.

Next milestone:

```text
m2107-paper-route-outcome-supported-decisive-public-gate-core-repaired-measured-execution-command-design
```
