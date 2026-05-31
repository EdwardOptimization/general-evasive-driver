# M1900 Executable V2 Support-First Clearance-Containment Conflict Localization Result Audit

- status: completed
- decision: `clearance_containment_conflict_audit_admit_task_quality_repair_axis_design`
- audited summary: `runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/summary.json`
- reset/rollout in M1900: false
- measured execution in M1900: false
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## Artifact Integrity

M1899 passes as a no-rollout localization artifact:

```text
result_class: clearance_containment_conflict_localization_pass
episode_count: 960 / 960
source_result_class: executable_v2_support_first_repaired_bounded_smoke_execution_pass
all_selected_metrics_finite: true
all_rows_classified_once: true
required_aggregate_files_written: true
guardrail_violation_count: 0
```

M1899 did not run reset, rollout, measured execution, training, replay, PPO,
private holdout, promotion, actor-input changes, controller-family ranking,
paper-level claims, or level3 self-identification claims.

## Conflict Result

Primary classes:

```text
joint_clearance_containment: 0
clearance_only_offtrack: 784
containment_collision: 169
collision_and_offtrack: 7
other_non_success: 0
```

Near-miss flags:

```text
near_containment_after_clearance: 292
near_clearance_with_containment: 112
late_offtrack_after_clearance: 59
near_miss_row_count: 429
```

Controller ranking remains blocked because `joint_clearance_containment` is
zero. However, the conflict is now actionable enough for targeted
task-quality repair-axis design because there are many near-miss rows and the
failure modes separate by role surface.

## Actionable Structure

Clearance-only/offtrack dominance:

```text
unavoidable_mitigation::post_friction_step:
  clearance_only_offtrack_rate: 1.000

stable_aes_only::post_friction_step:
  clearance_only_offtrack_rate: 0.983

stable_aes_only::steady_surface:
  clearance_only_offtrack_rate: 0.983

stable_aeb::post_friction_step:
  clearance_only_offtrack_rate: 0.967

stable_aeb::steady_surface:
  clearance_only_offtrack_rate: 0.950
```

Containment/collision dominance:

```text
unavoidable_mitigation::steady_surface:
  containment_collision_rate: 0.800
  near_clearance_with_containment_rate: 0.592

drift_required_recovery::steady_surface:
  containment_collision_rate: 0.450
  near_clearance_with_containment_rate: 0.225
```

This is not a single scalar success-semantics bug. It is at least two repair
axes:

```text
1. post-clearance containment / recovery axis:
   many rows clear the obstacle but leave the road.

2. contained collision / clearance feasibility axis:
   some steady-surface rows stay contained but collide, especially unavoidable
   steady-surface and drift-required steady-surface.
```

## Repair Variant Audit

The existing bounded smoke variants did not solve the conflict:

```text
original:
  joint_clearance_containment_rate: 0.000
  clearance_only_offtrack_rate: 0.833
  containment_collision_rate: 0.156

road_relaxed_finish_extended:
  joint_clearance_containment_rate: 0.000
  clearance_only_offtrack_rate: 0.786
  containment_collision_rate: 0.214
```

`road_relaxed_finish_extended` slightly reduces clearance-only/offtrack but
increases containment-collision. That is useful diagnostic evidence, not a
repair success. The next panel should not simply repeat the same variants at
larger scale.

## Decision

Do not route to controller comparison.

Do not route directly to another measured execution.

Route to a targeted task-quality repair-axis design:

```text
m1901-executable-v2-support-first-task-quality-repair-axis-design
```

M1901 should define a baseline-preserving no-rollout repair-axis matrix that
separates:

- post-clearance containment/recovery variants;
- contained-collision clearance-feasibility variants;
- unavoidable-mitigation role semantics;
- original baseline retention.

The next design must preserve actor inputs, controller profiles, support-first
metadata, and ranking boundaries. Any later execution must still be audited
before controller-family comparison.

## Claim Boundary

Supported:

- M1899 localization artifacts are valid;
- the conflict is actionable enough for task-quality repair-axis design;
- ranking remains blocked because joint clearance/containment count is zero.

Unsupported:

- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence;
- task-quality repair success.
