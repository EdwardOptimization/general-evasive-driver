# M1913 Executable V2 Support-First Task-Quality Repair-Axis Measured Wrapper Execution Failure Audit

- status: completed
- decision: `measured_wrapper_failure_audit_route_to_geometry_delta_mapping_repair`
- audited execution: `docs/m1912-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution.md`
- summary: `runs/m1912_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution/summary.json`
- failure rows: `runs/m1912_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution/failure_rows.csv`
- rerun in M1913: `false`
- environment reset/rollout/measured execution in M1913: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Failure Summary

M1912 failed the execution gate:

```text
planned rollout rows: 960
measured rollout rows: 768
import/postprocess rows: 576
combined panel rows: 1344
failure rows: 192
guardrail violations: 0
```

All failures are:

```text
error_type: RuntimeError
error_message: failed to sample an obstacle scenario matching the configured filters
task_quality_axis_id: contained_collision_clearance_feasibility
target_conflict_class: containment_collision
```

Failure by variant:

```text
contained_reaction_distance_plus: 108
contained_clearance_gap_plus: 84
```

Failure by role:

```text
stable_aes_only: 72
drift_required_recovery: 48
unavoidable_mitigation: 48
stable_aeb: 24
```

Failure by geometry delta:

```text
{"obstacle_reaction_distance_delta_m":5.0,"road_geometry_fixed":true}: 108
{"obstacle_clearance_gap_delta_m":0.25,"road_geometry_fixed":true}: 84
```

## Diagnosis

The failure is classified as:

```text
scenario_sampling_failure caused by geometry-delta mapping
```

Why this is the right classification:

- all failures are scenario sampling failures, not checkpoint/profile/model
  loading failures;
- no failures are `KeyError` or base-spec lookup failures;
- no guardrail or actor-input contract violation occurred;
- the failure rows are exactly the contained-collision feasibility variants
  with obstacle diagnostic deltas;
- both failing geometry deltas explicitly include `road_geometry_fixed=true`;
- M1911 mapped those obstacle deltas into `env_config.obstacle`, which changes
  the obstacle sampler instead of only changing downstream task-quality
  semantics.

The key mistake is treating these two fields as sampling geometry changes:

```text
obstacle_clearance_gap_delta_m
obstacle_reaction_distance_delta_m
```

when their row also says:

```text
road_geometry_fixed=true
```

For this axis, those deltas should be retained as task-quality/postprocess
metadata, not used to make the scenario sampler stricter or farther away.

## Ruled Out

Source/spec infeasibility is not the leading cause:

- the failing rows have valid base task ids and base measured specs;
- the completed rows include other variants from the same source families;
- the error message is sampling-filter failure after config mutation, not
  missing source rows.

Controller behavior is not interpretable from M1912:

- partial completed rows are not balanced across variants;
- target counts failed;
- ranking remains blocked.

## Next Route

Route to a focused no-rerun repair:

```text
m1914-executable-v2-support-first-task-quality-repair-axis-geometry-delta-mapping-repair
```

Repair rule:

```text
If geometry_delta_json has road_geometry_fixed=true,
do not apply obstacle_clearance_gap_delta_m or
obstacle_reaction_distance_delta_m to env_config.obstacle.
Keep those fields as metadata for later task-quality scoring.
```

The repair should keep the existing max-steps and road-width mappings for the
post-clearance containment/recovery axes, add focused tests, and not rerun
M1912. A later milestone should rerun the exact M1912 command after the repair
passes.
