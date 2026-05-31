# M1883 Executable V2 Support-First Success Semantics Task-Quality Repair Design

- status: completed
- decision: `support_first_success_semantics_task_quality_repair_design_admit_materialization`
- parent localization: `runs/m1882_executable_v2_support_first_outcome_localization/summary.json`
- parent execution: `runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv`
- reset/rollout in M1883: false
- training/replay/PPO: false

## Summary

M1883 designs the repair route required by M1882 before any controller-family
ranking. The parent facts are:

```text
M1880 episodes: 2160 / 2160
M1880 execution failures: 0
M1880 guardrail violations: 0
M1882 dominant slices: 526
M1882 outcome dominance class: diffuse_support_first_outcome_dominance
dominant role panels: 4 / 4
dominant role surfaces: 8 / 8
dominant controller profiles: 12 / 12
outcomes:
  collision_failure: 480
  off_track_noncollision_noncompletion: 1680
  success_obstacle_pass: 0
```

This is not a profile-specific control result. It is a task-quality and success
semantics blocker: the workload executes cleanly, but its current binary success
definition and road/finish geometry make every profile fail across the full
support-first role panel.

## Diagnosis

The failure signal is diffuse:

- all role panels appear in dominant non-success slices;
- all role-surface combinations appear in dominant non-success slices;
- all controller profiles appear in dominant non-success slices;
- many non-collision rows have positive obstacle clearance margin but terminate
  off-track before `success_obstacle_pass`;
- unavoidable mitigation rows are collision-heavy by role design, so binary
  obstacle-pass success is not the right primary metric for that role.

Therefore, a controller-family ranking or PPO response to M1880/M1882 would be
misleading. A repair must first separate:

```text
1. success semantics:
   what each role should count as success, failure, mitigation, or diagnostic.

2. road-boundary geometry:
   whether off-track dominance is caused by unrealistically narrow road or
   finish timing rather than controller inability.

3. obstacle task quality:
   whether obstacle position, timing, and label distribution make the intended
   role observable and comparable.
```

## Repair Principles

The repair is allowed to change evaluation semantics and task-quality geometry,
but it must not change the deployable actor contract.

Allowed:

- add diagnostic outcome labels derived from existing rollout metrics;
- preserve original binary success as a baseline metric;
- materialize public diagnostic variants of road width, finish horizon, and
  recovery window;
- preserve all 12 controller profiles without tuning any profile;
- preserve support-first scenario/source metadata;
- define role-specific metric panels for stable avoidance, drift-required
  recovery, and unavoidable mitigation.

Forbidden:

- actor input changes;
- reward shortcuts;
- hidden parameter, oracle feasibility, TTC, reference trajectory, success,
  collision, progress, slip, tire force, friction margin, or controller-mode
  fields in actor input;
- controller-family profile tuning;
- private holdout use;
- controller-family ranking from M1880/M1882;
- paper-level or level3 self-identification claims.

## Semantics Repair

The next materialization should keep the original `success_obstacle_pass` field
but add a role-aware diagnostic outcome panel.

Core diagnostic fields:

```text
obstacle_clearance_pass:
  collision == false and min_clearance_margin > 0

road_containment_pass:
  termination_reason != off_track

obstacle_pass_before_offtrack:
  first_obstacle_pass_step is finite and
  (time_to_first_off_track_s is missing or first_obstacle_pass_time_s <= time_to_first_off_track_s)

offtrack_after_clearance:
  obstacle_clearance_pass and termination_reason == off_track

controlled_recovery_pass:
  recovery_success or controlled_drift_recovery_success

mitigation_quality:
  collision_mitigation_score / impact_severity_proxy / impact_speed_proxy
  retained as continuous metrics, not converted into a binary win.
```

Role-specific interpretation:

```text
stable_aeb:
  primary: no collision, road containment, obstacle pass if obstacle is present
  diagnostic: obstacle clearance without road containment

stable_aes_only:
  primary: no collision, obstacle pass, road containment or bounded recovery
  diagnostic: offtrack-after-clearance

drift_required_recovery:
  primary: no collision, obstacle clearance, controlled recovery
  diagnostic: drift-used but unrecovered, offtrack-after-clearance

unavoidable_mitigation:
  primary: lower impact severity and bounded road departure
  diagnostic: collision-free pass is allowed but not required for the role
```

This keeps the project honest: normal avoidance roles still penalize road
departure, while unavoidable mitigation is not incorrectly treated as a binary
obstacle-pass task.

## Geometry Repair

M1880/M1882 cannot tell whether the dominant off-track result is caused by bad
driving or by task geometry that leaves no fair recovery corridor. The next
materialization should produce baseline-preserving public variants:

```text
original:
  unchanged current geometry and success semantics.

semantics_only:
  unchanged geometry, added role-aware diagnostic outcome fields.

finish_extended:
  unchanged road width, longer post-obstacle finish/recovery window.

road_relaxed:
  wider or relaxed road-boundary condition, unchanged obstacle placement.

road_relaxed_finish_extended:
  combined geometry variant for diagnosing whether off-track dominance is a
  narrow-road plus short-finish artifact.
```

The original variant must remain in every panel. Any later improvement must be
reported against the original, not by deleting hard cases.

## Obstacle Task-Quality Repair

The materialization should also preserve enough metadata to audit whether each
role is being tested as intended:

```text
role_panel_id
v2_role_surface_id
surface_variant
sampled_obstacle_label
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
scenario_profile_name
controller_profile_name
source_scenario_spec_id
```

Task-quality gates before any ranking:

- all role panels remain represented;
- all role surfaces remain represented;
- original baseline variant remains represented for every source;
- every controller profile is evaluated on the same materialized cells;
- no materialized variant uses hidden or oracle fields as actor input;
- semantic labels are metric outputs, not actor observations.

## Next Step

M1884 should implement a no-rollout materialization pass:

```text
m1884-executable-v2-support-first-success-semantics-task-quality-repair-materialization
```

It should consume M1880/M1882 artifacts plus the original support-first workload
metadata and emit a repair matrix with original, semantics-only, and geometry
repair variants. M1884 must not run environment reset, rollout, training,
replay, PPO, private holdout, or controller-family ranking.

The expected M1884 outputs are:

```text
runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/summary.json
runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/repair_variant_matrix.csv
runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/role_semantics_spec.json
```

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- M1880/M1882 require success-semantics and task-quality repair before ranking;
- the repair must be baseline-preserving and role-aware;
- M1884 should materialize the repair matrix without rollout.

Unsupported:

- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence;
- any conclusion that off-track dominance is controller-specific.

## Decision

Route to M1884 no-rollout success-semantics/task-quality repair materialization.
Ranking, training, private holdout use, and paper-level claims remain blocked.
