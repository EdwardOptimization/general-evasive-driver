# M1967 Executable V2 Task-Quality Calibrated Measured Execution Result Audit

- status: completed
- decision: `task_quality_calibrated_measured_execution_audit_route_to_offtrack_parent_tier_metadata_normalization`
- audited run: `runs/m1966_executable_v2_task_quality_calibrated_measured_execution/summary.json`
- reset/rollout/measured execution in M1967: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Summary

M1966 did not produce measured driver-performance evidence. It failed closed
before any environment rollout because required provenance metadata was blank
for the offtrack-boundary-relief slice.

M1966 summary:

```text
result_class: task_quality_calibrated_measured_execution_incomplete_or_fail
episode_count: 0
target_episode_count: 960
spec_count: 0
target_spec_count: 80
profile_count: 0
target_profile_count: 12
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
guardrail_violation_count: 0
training_started: false
replay_started: false
ppo_used: false
```

The direct validation failure was:

```text
error_type: missing_spec_field
error_message: parent_feasibility_tier_id
validation_failure_rows: 8
```

The `8` validation failures correspond to `8` selected task sources and `96`
planned workload cells after crossing with the `12` controller profiles.

## Localization

The affected executable specs are exactly the selected
offtrack-boundary-relief sources:

```text
tqcm_exec_v0_0056_otsr_v0_0114_offtrack_boundary_relief
tqcm_exec_v0_0057_otsr_v0_0118_offtrack_boundary_relief
tqcm_exec_v0_0058_otsr_v0_0121_offtrack_boundary_relief
tqcm_exec_v0_0059_otsr_v0_0127_offtrack_boundary_relief
tqcm_exec_v0_0060_otsr_v0_0130_offtrack_boundary_relief
tqcm_exec_v0_0061_otsr_v0_0133_offtrack_boundary_relief
tqcm_exec_v0_0062_otsr_v0_0139_offtrack_boundary_relief
tqcm_exec_v0_0063_otsr_v0_0142_offtrack_boundary_relief
```

Source-level audit:

```text
M1952 supported source rows: 130
M1952 supported rows with blank parent_feasibility_tier_id: 11
blank source repair_source_kind: offtrack_boundary_relief
```

Materialization audit:

```text
M1958 executable specs: 80
executable specs with blank parent_feasibility_tier_id: 8
blank spec repair_source_kind: offtrack_boundary_relief
M1958 planned workload rows: 960
planned workload rows with blank parent_feasibility_tier_id: 96
blank workload repair_source_kind: offtrack_boundary_relief
```

The executable spec key exists for those rows, but the value is an empty string.
So the failure is not a missing-column issue; it is a blank provenance value.

## Classification

Within the current harness taxonomy this is closest to
`scenario_sampling_failure`, but the operational diagnosis is narrower:

```text
offtrack-boundary-relief parent-tier metadata normalization gap
```

It is not a driver-performance failure:

```text
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
episode_count: 0
```

It is not a guardrail failure:

```text
guardrail_violation_count: 0
training/replay/PPO/ranking/paper/self-ID flags: false
```

It is not runner validation overreach. The calibrated runner requires
`parent_feasibility_tier_id` because calibrated measured execution promised to
preserve repair-source metadata as first-class episode and aggregate evidence.
A blank value would silently weaken that evidence contract.

## Supported Claims

Supported:

- M1966 correctly failed closed before rollout on blank required provenance;
- the failure localizes to offtrack-boundary-relief selected sources;
- the blank value originates upstream in M1952 supported source rows and is
  propagated by M1958 materialization;
- repair should preserve metadata by assigning an explicit normalized value,
  not by weakening runner validation.

Unsupported:

- measured rollout success;
- controller-family ranking;
- policy performance comparison;
- paper-level benchmark evidence;
- finite-window vs GRU conclusion;
- level3 self-identification.

## Repair Route

Next route:

```text
m1968-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-design
```

M1968 should design a no-rollout metadata normalization repair. The repair
should:

- keep the calibrated runner requirement for non-empty
  `parent_feasibility_tier_id`;
- normalize blank offtrack-boundary-relief parent tiers to an explicit sentinel
  value rather than leaving them empty;
- preserve source role, repair source kind, normalized surface, base geometry,
  and representative cell metadata;
- rerun no-reset materialization and reset validation only after the design is
  explicit;
- block measured execution until the repaired workload has zero blank required
  metadata fields.

No M1967 repair or rerun was performed.
