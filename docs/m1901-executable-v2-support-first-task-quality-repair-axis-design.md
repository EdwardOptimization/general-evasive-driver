# M1901 Executable V2 Support-First Task-Quality Repair-Axis Design

- status: completed
- decision: `task_quality_repair_axis_design_admit_no_rollout_materialization`
- parent audit: `docs/m1900-executable-v2-support-first-clearance-containment-conflict-localization-result-audit.md`
- parent localization: `runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/summary.json`
- reset/rollout in M1901: false
- measured execution in M1901: false
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## Purpose

M1901 turns the M1899/M1900 clearance-containment conflict into a concrete
repair-axis matrix before any new rollout. The goal is not to make the benchmark
easier or to rank controller families. The goal is to build a baseline-preserving
diagnostic panel that can separate task-quality failures:

```text
post-clearance containment / recovery failure
contained-collision / clearance-feasibility failure
unavoidable mitigation semantics
```

## Parent Facts

M1899/M1900 established:

```text
episode count: 960 / 960
joint clearance/containment rows: 0
clearance-only offtrack rows: 784
containment-collision rows: 169
collision-and-offtrack rows: 7
other non-success rows: 0
near-miss rows: 429
near containment after clearance: 292
near clearance with containment: 112
late offtrack after clearance: 59
guardrail violations: 0
```

Role-surface split:

```text
post-friction and stable surfaces:
  mostly obstacle cleared, then road containment fails.

unavoidable_mitigation::steady_surface:
  mostly road-contained collision, with high near-clearance count.

drift_required_recovery::steady_surface:
  mixed clearance-only offtrack and containment-collision.
```

The existing broad repair variants did not solve the conflict:

```text
original:
  joint clearance/containment rate: 0.000
  clearance-only offtrack rate: 0.833
  containment-collision rate: 0.156

road_relaxed_finish_extended:
  joint clearance/containment rate: 0.000
  clearance-only offtrack rate: 0.786
  containment-collision rate: 0.214
```

Therefore the next panel must be axis-specific. Repeating the same
`road_relaxed_finish_extended` family at larger scale would be local search
without a new diagnostic question.

## Design Principles

Allowed:

- preserve the original baseline variant for every source/profile cell;
- add diagnostic semantics derived from existing rollout metrics;
- materialize new geometry variants for later rollout;
- separate recovery, clearance feasibility, and mitigation semantics axes;
- preserve all support-first scenario metadata and all controller profiles;
- keep actor inputs and controller profile configs unchanged.

Forbidden:

- actor input changes;
- controller profile tuning;
- reward or planner shortcuts;
- hidden parameter, oracle feasibility, TTC, reference, success/collision,
  slip, tire-force, friction-margin, or controller-mode fields in actor input;
- reset, rollout, measured execution, training, replay, PPO, promotion, private
  holdout, controller ranking, paper-level claims, or level3 self-ID claims in
  this design step.

## Repair Axes

### Axis A: Baseline And Semantics Retention

Purpose:

```text
keep the old evidence comparable and make role semantics auditable.
```

Variants:

```text
original_retained:
  no config delta; imports existing M1895/M1880-compatible metrics.

role_semantics_only:
  no geometry delta; adds role-aware diagnostic fields, including
  obstacle_clearance_pass, road_containment_pass, offtrack_after_clearance,
  contained_collision, near_clearance_with_containment, impact_severity_proxy,
  and mitigation-quality fields.
```

This axis is mandatory. Any later repair improvement must be reported beside
the unchanged original baseline, not by deleting the hard rows.

### Axis B: Post-Clearance Containment / Recovery

Purpose:

```text
test whether rows that already clear the obstacle fail because the recovery
window, post-obstacle road corridor, or road-containment semantics are too
strict for a fair evasive-driving diagnostic.
```

Primary target rows:

```text
clearance_only_offtrack rows: 784
near_containment_after_clearance rows: 292
late_offtrack_after_clearance rows: 59
```

Primary target surfaces:

```text
stable_aeb::post_friction_step
stable_aeb::steady_surface
stable_aes_only::post_friction_step
stable_aes_only::steady_surface
drift_required_recovery::post_friction_step
unavoidable_mitigation::post_friction_step
```

Variants:

```text
post_clearance_recovery_window_plus:
  keep road and obstacle geometry fixed; extend the post-obstacle recovery
  horizon/finish window only.

post_obstacle_containment_corridor_plus:
  keep pre-obstacle road and obstacle geometry fixed; relax only the
  post-obstacle road containment corridor.

post_clearance_recovery_corridor_combo:
  combine the recovery-window and post-obstacle-corridor changes to test
  whether the two effects must be present together.
```

This axis must not be interpreted as controller ranking. It asks whether the
task has a fair recovery corridor after a successful emergency maneuver.

### Axis C: Contained-Collision / Clearance Feasibility

Purpose:

```text
test whether road-contained collision rows are near-feasible and whether the
obstacle timing/gap is the blocker rather than the controller profile.
```

Primary target rows:

```text
containment_collision rows: 169
near_clearance_with_containment rows: 112
```

Primary target surfaces:

```text
unavoidable_mitigation::steady_surface
drift_required_recovery::steady_surface
```

Variants:

```text
contained_clearance_gap_plus:
  keep road geometry fixed; increase obstacle clearance gap by a small,
  declared geometry delta.

contained_reaction_distance_plus:
  keep road geometry fixed; increase obstacle approach distance/reaction
  horizon by a small, declared timing delta.
```

These variants do not declare success. They are probes for whether the
collision-heavy rows are just beyond the feasible boundary, which is required
before using them in a paper-grade comparison panel.

### Axis D: Unavoidable-Mitigation Semantics

Purpose:

```text
avoid treating unavoidable mitigation as binary obstacle-pass ranking.
```

Primary target surfaces:

```text
unavoidable_mitigation::post_friction_step
unavoidable_mitigation::steady_surface
```

Variant:

```text
mitigation_scored_semantics:
  no geometry delta; preserve collision/offtrack fields but add continuous
  mitigation metrics such as impact severity, bounded road departure, and
  obstacle clearance margin. Collision-free pass can remain a diagnostic field
  but must not be the only score for this role.
```

This axis is a semantics repair, not a controller-performance result.

## Materialization Matrix

M1902 should materialize the following no-rollout matrix over the same
support-first bounded-smoke source/profile base used by M1895:

```text
source specs: 16
controller profiles: 12
repair-axis variants: 8
expected matrix rows: 1536
```

Required variant IDs:

```text
original_retained
role_semantics_only
post_clearance_recovery_window_plus
post_obstacle_containment_corridor_plus
post_clearance_recovery_corridor_combo
contained_clearance_gap_plus
contained_reaction_distance_plus
mitigation_scored_semantics
```

If a variant is role-specific, M1902 must still emit auditable rows for every
source/profile cell with an explicit `axis_applicability` field, not silently
drop rows.

Required row fields:

```text
task_quality_axis_id
repair_axis_variant_id
axis_applicability
target_conflict_class
target_near_miss_class
target_role_surface_id
repair_variant_kind
execution_row_kind
geometry_delta_json
semantics_delta_json
source_conflict_class
source_near_miss_flags
source_clearance_margin
source_max_off_track_overshoot
source_impact_severity_proxy
source_episode_workload_id
base_task_source_id
controller_profile_name
scenario_profile_name
role_panel_id
v2_role_surface_id
surface_variant
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
sampled_obstacle_label
actor_input_contract_changed
profile_specific_tuning
controller_family_ranking_claim_made
paper_level_claim_made
level3_self_id_claim_made
diagnostic_only_no_ranking_claim
```

## Materialization Pass Gates

M1902 should pass only if:

```text
summary.json exists
task_quality_repair_axis_matrix.csv exists
task_quality_repair_axis_spec.json exists
role_surface_axis_target_map.csv exists
source spec count == 16
controller profile count == 12
repair-axis variant count == 8
expected matrix rows == 1536
original_retained rows == 192
all role surfaces represented
all controller profiles represented
baseline support-first metadata preserved
actor input contract changed == false
profile-specific tuning == false
ranking claims == false
paper-level claims == false
level3 self-ID claims == false
guardrail violation count == 0
reset/rollout/measured execution started == false
training/replay/PPO == false
```

M1902 must fail or route to synthesis if it cannot preserve the original
baseline, if it merges the distinct axes into one scalar tweak, or if it would
require changing actor inputs or controller profiles.

## Next Step

Route to:

```text
m1902-executable-v2-support-first-task-quality-repair-axis-materialization
```

M1902 should implement and run only a no-rollout materialization helper. It
must not run reset, rollout, measured execution, training, replay, PPO, private
holdout, controller ranking, paper-level claims, or level3 self-ID claims.

## Claim Boundary

Supported:

- M1899/M1900 expose at least two distinct task-quality repair axes;
- the next fair step is a baseline-preserving no-rollout repair-axis matrix;
- direct controller ranking remains blocked.

Unsupported:

- task-quality repair success;
- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.
