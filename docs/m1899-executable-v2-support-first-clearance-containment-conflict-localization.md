# M1899 Executable V2 Support-First Clearance-Containment Conflict Localization

- status: completed
- decision: `clearance_containment_conflict_localization_pass_route_to_result_audit`
- summary: `runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/summary.json`
- parent rows: `runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv`
- reset/rollout in M1899: false
- measured execution in M1899: false
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## Implementation

M1899 adds:

```text
src/autodrift/executable_v2_support_first_clearance_containment_conflict_localization.py
tests/test_executable_v2_support_first_clearance_containment_conflict_localization.py
```

Focused tests:

```text
2 passed
```

The tool is no-rollout. It reads completed M1895 CSV/JSON artifacts and writes
diagnostic localization tables. It does not instantiate the environment or run
policy actions.

## Execution

Command:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_support_first_clearance_containment_conflict_localization \
  --episode-rows runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv \
  --summary runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/summary.json \
  --output-dir runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization \
  --target-episode-count 960 \
  --next-blocker m1900-executable-v2-support-first-clearance-containment-conflict-localization-result-audit
```

Result:

```text
result_class: clearance_containment_conflict_localization_pass
episode_count: 960 / 960
source_result_class: executable_v2_support_first_repaired_bounded_smoke_execution_pass
all_selected_metrics_finite: true
all_rows_classified_once: true
required_aggregate_files_written: true
guardrail_violation_count: 0
recommended_next_route: route_to_task_quality_repair_axis_design
```

## Primary Conflict Classes

```text
joint_clearance_containment: 0
clearance_only_offtrack: 784
containment_collision: 169
collision_and_offtrack: 7
other_non_success: 0
```

The previous audit finding is now an artifact-backed localization result:
there are still zero rows satisfying both obstacle clearance and road
containment.

## Near Misses

```text
near_containment_after_clearance: 292
near_clearance_with_containment: 112
late_offtrack_after_clearance: 59
near_miss_row_count: 429
```

This is important because it means the branch has likely repairable boundary
cases. The result should not trigger controller ranking; it should first be
audited to choose a task-quality repair axis.

## Role-Surface Localization

Notable role-surface conflict rates:

```text
unavoidable_mitigation::post_friction_step:
  clearance_only_offtrack_rate: 1.000
  containment_collision_rate: 0.000

unavoidable_mitigation::steady_surface:
  clearance_only_offtrack_rate: 0.150
  containment_collision_rate: 0.800
  collision_and_offtrack_rate: 0.050

stable_aes_only::post_friction_step:
  clearance_only_offtrack_rate: 0.983
  containment_collision_rate: 0.008

stable_aeb::post_friction_step:
  clearance_only_offtrack_rate: 0.967
  containment_collision_rate: 0.033
```

The conflict is therefore not one uniform failure. Post-friction and stable
avoidance surfaces are clearance-dominant but road-containment poor, while
unavoidable steady-surface is containment/collision-heavy.

## Artifacts

```text
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/summary.json
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/conflict_class_rows.csv
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/conflict_class_aggregate.csv
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/near_miss_rows.csv
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/near_miss_aggregate.csv
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/role_surface_conflict_aggregate.csv
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/repair_variant_conflict_aggregate.csv
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/controller_profile_conflict_aggregate.csv
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/role_surface_repair_variant_conflict_aggregate.csv
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/role_surface_profile_conflict_aggregate.csv
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/role_surface_lateral_conflict_aggregate.csv
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/role_surface_timing_conflict_aggregate.csv
runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/hidden_dynamics_conflict_aggregate.csv
```

## Claim Boundary

Supported:

- M1895 clearance/containment conflict has a no-rollout artifact-backed
  localization result;
- the panel remains ranking-blocked because joint clearance/containment count is
  zero;
- near-miss rows exist and justify a result audit before selecting a repair
  axis.

Unsupported:

- controller-family ranking;
- task-quality repair conclusion before M1900 audit;
- driver performance conclusion;
- paper-level benchmark evidence;
- level3 self-identification evidence.

## Decision

Route to:

```text
m1900-executable-v2-support-first-clearance-containment-conflict-localization-result-audit
```

M1900 should audit whether the localized conflict supports a targeted
task-quality repair-axis design or requires branch synthesis before any further
repair. Do not rank controller families from M1899.
