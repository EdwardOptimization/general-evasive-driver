# M1979 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Repair Design

- status: completed
- decision: `task_quality_calibrated_repaired_outcome_support_repair_design_admit_template_implementation`
- branch: `paper_route_task_quality_calibrated_repaired_outcome_support_repair`
- parent audit: `docs/m1978-executable-v2-task-quality-calibrated-repaired-measured-outcome-localization-result-audit.md`
- reset/rollout/measured execution in M1979: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Problem

M1975/M1977 prove that the repaired calibrated panel is executable and
localizable, but it is still not comparison-ready:

```text
success_obstacle_pass: 38 / 960
collision_failure: 150 / 960
off_track_noncollision_noncompletion: 772 / 960
comparison_ready_candidate_count: 0
comparison_support_candidate_count: 1
```

The blocker is not runner correctness, metadata completeness, actor input,
training, replay, PPO, or policy promotion. It is scenario/task quality:

```text
scenario_sampling_failure:
  the public task panel still contains large offtrack-only blocks and
  collision-dominated mitigation blocks, so controller ranking would mostly
  measure task saturation rather than driver capability.
```

## Repair Anchors

M1979 uses M1977 only as diagnostic source selection. It does not rank
profiles.

### Offtrack-Only Anchors

These are high-priority repair anchors because they have zero collision and
zero success, so the task is mostly terminating on road-boundary support rather
than obstacle avoidance:

```text
anchor_neighborhood:
  episodes: 384
  success_count: 0
  collision_count: 0
  offtrack_outcome_count: 384

offtrack_boundary_relief:
  episodes: 96
  success_count: 0
  collision_count: 0
  offtrack_outcome_count: 96
```

Repair intent:

```text
reduce road-boundary saturation while preserving obstacle difficulty and the
same calibrated repair provenance.
```

### Positive Support Anchors

The strongest non-L2 support rows come from `success_stabilizer` and
`mitigation_isolation_check`:

```text
success_stabilizer:
  episodes: 288
  success_count: 25
  collision_count: 44
  offtrack_outcome_count: 219

mitigation_isolation_check:
  episodes: 192
  success_count: 13
  collision_count: 106
  offtrack_outcome_count: 73
```

These rows should seed support expansion, but they remain diagnostic. They do
not support controller ranking.

### Collision-Dominated Mitigation Anchor

The only M1977 comparison-support candidate is collision-dominated:

```text
repair_source_kind: mitigation_isolation_check
source_role_semantics: unavoidable_mitigation
parent_feasibility_tier_id: tier_d_handling_limit_drift_required
normalized_surface_variant: steady_surface
sampled_obstacle_label: unavoidable
episode_count: 60
success_count: 5
collision_count: 55
offtrack_outcome_count: 0
collision_rate: 91.67%
profiles_with_success: L1_one_step; L3_online_gru; L3_reset_control_corrected
```

Repair intent:

```text
separate mitigation-quality diagnostics from obstacle-pass comparison support.
```

## Repair Principle

The repair must improve task support without making the task trivial and
without tuning controller profiles.

Allowed repair levers:

```text
offtrack support:
  increase post-obstacle recovery corridor in bounded increments;
  increase effective road-boundary relief only for offtrack-only source kinds;
  increase reaction distance in small bounded increments;
  reduce obstacle half-width slightly within each role/tier envelope;
  soften obstacle placement away from immediate road-boundary saturation;
  keep steady-surface, post-friction-step, and relief-surface provenance.

collision support:
  create mitigation severity bands rather than one saturated unavoidable block;
  use bounded earlier obstacle distance or smaller half-width deltas;
  keep unavoidable/mitigation labels as metadata only;
  preserve impact/mitigation metrics for later audit instead of relabeling
  collisions as obstacle-pass success.

source selection:
  preserve M1975/M1977 as baseline diagnostic artifacts;
  generate new public-debug/public-gate candidates around diagnostic anchors;
  include both success-support rows and no-support rows to avoid cherry-picking;
  preserve repair source kind, parent tier, normalized surface, sampled label,
  and base geometry provenance.
```

Forbidden repair levers:

```text
profile-specific tuning;
actor input changes;
controller-family-specific scenario filters;
ranking from M1977 diagnostic slices;
turning off road-boundary failure;
calling off-track clearance a success;
calling collision mitigation an obstacle-pass success;
private holdout use;
paper-level or level3 self-ID claims.
```

## First Repair Template Wave

M1980 should implement a deterministic no-rollout template generator that
creates a bounded first repair wave.

Target source template count:

```text
192 repair candidate sources
```

Composition:

```text
offtrack_anchor_relief:
  64 rows around anchor-neighborhood offtrack-only sources.

offtrack_boundary_relief_extension:
  32 rows around offtrack-boundary-relief sources with explicit sentinel
  provenance retained.

success_support_expansion:
  48 rows around success-stabilizer success families across stable AEB,
  stable AES-only, drift-required, and unavoidable roles.

collision_mitigation_relief:
  32 rows around mitigation-isolation collision-dominated unavoidable slices.

mitigation_metric_isolation:
  16 rows that keep collision mitigation diagnostics separate from
  obstacle-pass comparison support.
```

Deterministic split metadata:

```text
public_debug: 112
public_gate: 80
paper_holdout_candidate: 0
```

No holdout should be used in this repair wave because the branch is still
repairing public task quality.

## Candidate Fields

Each repair candidate should include:

```text
repair_branch_id
repair_candidate_id
repair_axis
repair_source_kind
parent_candidate_source_id
parent_task_source_id
parent_profile_name
parent_repair_source_kind
parent_selection_quota_name
parent_feasibility_tier_id
parent_source_role_semantics
parent_surface_variant
parent_normalized_surface_variant
parent_sampled_obstacle_label
parent_base_geometry_source
parent_outcome_bucket
parent_termination_reason

target_feasibility_tier_id
target_source_role_semantics
target_surface_variant
target_normalized_surface_variant
target_sampled_obstacle_label
source_split

speed_ref
mu
obstacle_distance_delta
obstacle_half_width_delta
post_obstacle_track_width_delta
reaction_distance_delta
recovery_corridor_profile
collision_severity_relief_delta
mitigation_metric_mode

labels_enter_actor_input=false
v2_ranking_admissible_by_default=false
profile_specific_tuning=false
controller_family_ranking_claim_made=false
paper_level_claim_made=false
level3_self_id_claim_made=false
```

The template generator may use M1977 outcome labels as artifact metadata, but
none of these labels may enter actor observations.

## Pre-Execution Gates

Before any reset or measured execution, the M1980 template artifact should
pass:

```text
candidate_source_count == 192
offtrack_anchor_relief_count == 64
offtrack_boundary_relief_extension_count == 32
success_support_expansion_count == 48
collision_mitigation_relief_count == 32
mitigation_metric_isolation_count == 16
public_debug_count == 112
public_gate_count == 80
paper_holdout_candidate_count == 0
profile_specific_tuning_count == 0
labels_enter_actor_input_count == 0
v2_ranking_admissible_by_default_count == 0
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

Later source-mining/materialization should prove:

```text
sampling_failure_count == 0
comparison_ready_candidate_count > 0 before ranking is admitted
offtrack outcome rate falls below 0.70 in at least one public-gate scenario
collision rate falls below 0.30 in candidate comparison slices
mitigation-only diagnostics remain isolated from obstacle-pass ranking
L2 zero-success remains diagnostic until support-balanced comparison exists
```

If the first repair wave still has zero comparison-ready candidates, the next
step should be a result audit and possibly broader scenario redesign, not
profile tuning.

## Claim Boundary

M1979 supports only:

```text
a pre-registered calibrated repaired outcome-support repair route is defined.
```

It does not support:

- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification;
- high-fidelity validation readiness.

## Next

Next milestone:

```text
m1980-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-template-implementation
```

M1980 should implement the deterministic no-rollout template generator and
focused tests. It must not reset, rollout, run measured execution, rank
controllers, or tune profiles.
