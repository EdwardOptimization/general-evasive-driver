# M2103 Paper-Route Outcome-Supported Decisive Public-Gate Core Measured Execution Repair Design

- status: completed
- decision: `public_gate_core_measured_execution_repair_design_admit_no_rollout_implementation`
- parent audit: `docs/m2102-paper-route-outcome-supported-decisive-public-gate-core-measured-execution-result-audit.md`
- reset/rollout/measured execution in M2103: `false`
- policy actions executed in M2103: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2101 failed the pass gate for two independent reasons:

```text
failure_count: 2 scenario-sampling failures
metadata_missing_count: 480 full metadata completeness failures
```

M2103 freezes a bounded no-rollout repair before any rerun.

## Metadata Completeness Repair

Inputs:

```text
M2098 measured-compatible specs/workload
M2091 reset_rows.csv
```

For each spec and workload row, join by `task_source_id` and fill:

```text
source_role_semantics := spec.task_role_semantics
parent_feasibility_tier_id := tier_not_applicable_outcome_supported_decisive
normalized_surface_variant := outcome_supported_decisive_public_gate_core
sampled_obstacle_label := M2091.reset_sampled_obstacle_label
```

The `sampled_obstacle_label` value is provenance metadata from the M2091
reset-success evidence. It must remain logging metadata only and must not enter
actor input or controller logic.

The repair must preserve:

```text
env_config
workload_id
task_source_id
profile_name
profile_config_path
checkpoint_path
controller profiles
scenario filters
```

## Scenario-Sampling Repair

M2101 failed exactly two workload cells:

```text
m2063-osd-osd_v0_0162_t3::L2_window_50
m2063-osd-osd_v0_0235_t5::L3_online_gru
```

M2091 already has reset-success seeds for both task specs:

```text
m2063-osd-osd_v0_0162_t3 -> 210260
m2063-osd-osd_v0_0235_t5 -> 210333
```

M2104 should add an optional workload column:

```text
eval_seed_override
```

The measured runner should use:

```text
eval_seed = int(workload_row["eval_seed_override"])
```

only when the column is present and non-empty. Otherwise it must keep the
existing behavior:

```text
eval_seed = eval_seed_base + cell_index
```

Only the two M2101 failure workload cells should receive overrides. This keeps
the previous measured command semantics unchanged for the other 478 cells while
using known reset-success seeds for the two scenario-sampling failures.

## M2104 Implementation Route

M2104 should implement:

```text
src/autodrift/paper_route_outcome_supported_decisive_public_gate_core_measured_execution_repair.py
tests/test_paper_route_outcome_supported_decisive_public_gate_core_measured_execution_repair.py
```

It should also update the existing measured runner to support optional
`eval_seed_override` without changing default behavior.

M2104 must not run measured execution. It should only write repaired artifacts
and validate that:

```text
metadata_missing_count would be 0 under the measured runner metadata check
validation_failure_rows would be 0
eval_seed_override_count == 2
env_config_changed_count == 0
duplicate_workload_id_count == 0
guardrail_violation_count == 0
```

## Claim Boundary

M2103/M2104 may claim only:

```text
the incomplete measured execution blockers have a bounded repair route.
```

They cannot claim:

```text
complete measured execution;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2104-paper-route-outcome-supported-decisive-public-gate-core-measured-execution-repair-implementation
```
