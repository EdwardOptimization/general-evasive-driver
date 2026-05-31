# M1898 Executable V2 Support-First Clearance-Containment Conflict Localization Design

- status: completed
- decision: `clearance_containment_conflict_localization_design_admit_no_rollout_implementation_execution`
- parent audit: `docs/m1897-executable-v2-support-first-repaired-bounded-smoke-execution-result-audit.md`
- parent rows: `runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv`
- reset/rollout in M1898: false
- measured execution in M1898: false
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## Purpose

M1897 found that the repaired smoke panel is execution-clean but not
ranking-interpretable. The core blocker is not just zero success. It is the
disjoint condition:

```text
obstacle_clearance_pass=True,  road_containment_pass=False: many rows
obstacle_clearance_pass=False, road_containment_pass=True: many rows
obstacle_clearance_pass=True,  road_containment_pass=True: zero rows
```

M1898 designs the next no-rollout localization pass. It must transform this
conflict into actionable slices before any new repair, ranking, PPO, or
paper-level claim.

## Why Existing Localization Is Not Enough

The existing `executable_v2_support_first_outcome_localization` helper is useful
for broad non-success dominance. It aggregates `outcome_bucket` by role,
profile, hidden bucket, timing, lateral bucket, and related support-first axes.

That is insufficient for the current blocker because M1895 already has a
sharper conflict:

```text
clearance without containment
containment without clearance
collision plus off-track
near miss toward satisfying both
```

The new pass should therefore implement a dedicated conflict localizer rather
than only rerunning the old outcome-dominance helper.

## Conflict Classes

The M1899 helper should classify every row into exactly one primary conflict
class:

```text
joint_clearance_containment:
  obstacle_clearance_pass == true
  road_containment_pass == true

clearance_only_offtrack:
  obstacle_clearance_pass == true
  road_containment_pass == false
  collision_failure == false

containment_collision:
  obstacle_clearance_pass == false
  road_containment_pass == true
  collision_failure == true

collision_and_offtrack:
  obstacle_clearance_pass == false
  road_containment_pass == false
  collision_failure == true

other_non_success:
  all remaining rows
```

For M1895, the expected primary counts are:

```text
joint_clearance_containment: 0
clearance_only_offtrack: 784
containment_collision: 169
collision_and_offtrack: 7
```

These values should be checked by the next command, not manually assumed.

## Near-Miss Classes

The helper should also produce non-exclusive near-miss flags:

```text
near_containment_after_clearance:
  obstacle_clearance_pass == true
  road_containment_pass == false
  max_off_track_overshoot <= 0.15

near_clearance_with_containment:
  road_containment_pass == true
  obstacle_clearance_pass == false
  min_clearance_margin >= -0.25

late_offtrack_after_clearance:
  obstacle_clearance_pass == true
  road_containment_pass == false
  time_to_first_off_track_s >= 2.0
```

The thresholds are diagnostic, not pass/fail truth. They are meant to identify
repairable boundary cases where a small road, timing, recovery-window, or
obstacle-placement change might create valid comparison cells.

## Required Output Artifacts

M1899 should write:

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

The aggregate rows should include:

```text
episode_count
joint_clearance_containment_count / rate
clearance_only_offtrack_count / rate
containment_collision_count / rate
collision_and_offtrack_count / rate
other_non_success_count / rate
near_containment_after_clearance_count / rate
near_clearance_with_containment_count / rate
late_offtrack_after_clearance_count / rate
clearance_margin_mean
clearance_margin_p10
max_off_track_overshoot_mean
impact_severity_proxy_mean
diagnostic_only_no_ranking_claim
```

## Slice Axes

M1899 should aggregate by at least these axes:

```text
role_panel_id
v2_role_surface_id
repair_variant_id
repair_variant_kind
geometry_variant_id
success_semantics_variant_id
controller_profile_name
hidden_dynamics_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
sampled_obstacle_label
v2_role_surface_id + repair_variant_id
v2_role_surface_id + controller_profile_name
v2_role_surface_id + obstacle_lateral_bucket
v2_role_surface_id + obstacle_timing_bucket
```

These axes are chosen to answer the next design question:

```text
Is the conflict dominated by geometry/road/finalization, obstacle placement,
role semantics, hidden dynamics, or a controller-profile interaction?
```

## Pass Criteria

M1899 should pass only if:

```text
episode_count == 960
source_result_class == executable_v2_support_first_repaired_bounded_smoke_execution_pass
guardrail_violation_count == 0
all selected source metrics are finite
all rows receive exactly one primary conflict class
required conflict classes are represented or explicitly zero-counted
joint_clearance_containment_count is reported even if zero
near-miss rows and aggregates are written
all required slice aggregate files are written
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

M1899 should fail if it silently drops rows, treats the conflict as controller
ranking, or requires a new environment rollout.

## Recommended Next Route After M1899

M1899 should not automatically admit controller ranking. Its summary should
choose one of:

```text
route_to_task_quality_repair_axis_design:
  conflict is localized enough to design a specific repair axis.

route_to_branch_synthesis:
  conflict remains broad/diffuse after localization.

route_to_controller_comparison_design:
  only if non-zero joint_clearance_containment cells exist across source-diverse
  roles, variants, and controller profiles.
```

For the current M1895 facts, the expected route is likely either targeted
task-quality repair-axis design or branch synthesis, not controller comparison.

## Guardrails

M1899 may implement and run a no-rollout artifact analysis helper. It must not:

- run environment reset;
- run environment rollout;
- run measured execution;
- train;
- run replay or PPO;
- use private holdout;
- promote a checkpoint;
- change actor inputs;
- tune controller profiles;
- rank controller families;
- claim paper-level evidence;
- claim level3 self-identification.

## Decision

Admit:

```text
m1899-executable-v2-support-first-clearance-containment-conflict-localization
```

This should be a combined no-rollout implementation and execution milestone:
add the dedicated localizer, cover it with focused tests, run it on the M1895
episode rows, and produce a conflict localization artifact set. That gives the
next branch real data/panel evidence instead of another design-only step.
