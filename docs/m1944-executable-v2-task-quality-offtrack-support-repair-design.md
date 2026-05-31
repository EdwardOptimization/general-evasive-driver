# M1944 Executable V2 Task-Quality Offtrack Support Repair Design

- status: completed
- decision: `task_quality_offtrack_support_repair_design_admit_template_implementation`
- branch: `paper_route_task_quality_offtrack_support_repair`
- parent audit: `docs/m1943-executable-v2-task-quality-measured-outcome-localization-result-audit.md`
- reset/rollout/measured execution in M1944: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Problem

M1942/M1943 showed that the redesigned public diagnostic panel is runnable and
has nonzero success support, but it is still not comparison-ready:

```text
success_obstacle_pass: 40 / 960
collision_failure: 105 / 960
off_track_noncollision_noncompletion: 815 / 960
comparison_ready_candidate_count: 0
comparison_support_candidate_count: 2
```

The blocker is not controller logic, actor input, PPO, or runner correctness.
It is scenario/task quality:

```text
scenario_sampling_failure:
  the public task panel mostly asks policies to leave the road after obstacle
  clearance, so profile ranking would measure task saturation rather than
  driver capability.
```

## Positive Support Anchors

M1944 uses M1942 only as diagnostic source selection. It does not rank
profiles.

Primary comparison-support anchors:

```text
tier_c_boundary_near_miss / stable_aeb / post_friction_step / aeb_feasible
  episode_count: 24
  success_count: 5
  collision_count: 1
  offtrack_outcome_count: 18
  nonzero_success_profiles: L1_one_step; L3_online_gru; L3_reset_control_corrected

tier_c_boundary_near_miss / stable_aeb / steady_surface / aeb_feasible
  episode_count: 24
  success_count: 5
  collision_count: 1
  offtrack_outcome_count: 18
  nonzero_success_profiles: L0_current_masked; L1_one_step; L3_online_gru; L3_reset_control_corrected
```

These slices are useful because they have:

- nonzero success;
- low collision rate;
- multiple non-L2 profiles with success;
- persistent off-track dominance that can be targeted by task-quality repair.

Broader success-source distribution from M1942:

```text
tier_a_positive_support_sanity: 1
tier_b_feasible_emergency: 10
tier_c_boundary_near_miss: 14
tier_d_handling_limit_drift_required: 8
tier_e_mitigation_only: 7

stable_aeb: 18
stable_aes_only: 8
drift_required_recovery: 8
unavoidable_mitigation: 6

post_friction_step: 22
steady_surface: 18
```

These are support anchors, not ranking evidence.

## Repair Principle

The repair must make the task distribution less off-track saturated without
making it trivial.

Allowed repair levers:

```text
scenario geometry:
  increase post-obstacle recovery corridor in bounded increments;
  increase reaction distance in bounded increments;
  reduce obstacle half-width slightly within each role/tier envelope;
  soften obstacle lateral placement away from hard road-boundary saturation;
  keep both steady-surface and post-friction-step variants.

source resampling:
  generate new public-debug/public-gate candidates around M1942 support anchors;
  include nearby off-track-dominated rows from the same tier/role/surface/label;
  preserve source diversity instead of repeatedly repairing one source.

outcome semantics:
  require obstacle clearance and road containment;
  do not relabel off-track-after-clearance as success;
  keep mitigation-only rows isolated from success ranking.
```

Forbidden repair levers:

```text
profile-specific tuning;
actor input changes;
controller-family-specific scenario filters;
ranking from M1942 diagnostic slices;
turning off road-boundary failure;
calling off-track clearance a success;
private holdout use;
paper-level or level3 self-ID claims.
```

## First Repair Template Wave

M1945 should implement a deterministic no-rollout template generator that
creates a bounded first repair wave.

Target source template count:

```text
160 repair candidate sources
```

Composition:

```text
anchor_neighborhood:
  64 rows around the two tier C stable-AEB candidate-support slices.

success_stabilizers:
  48 rows sampled from M1942 success-source families across tier B/C/D and both
  surfaces, preserving role diversity.

offtrack_boundary_relief:
  32 rows from high offtrack, low collision slices with bounded geometry relief.

mitigation_isolation_checks:
  16 rows that keep tier E mitigation separate and verify it does not leak into
  success-ranking support.
```

The repair wave should use deterministic split metadata:

```text
public_debug: 60%
public_gate: 40%
paper_holdout_candidate: 0%
```

No holdout should be used in this repair wave because the branch is still
repairing public task quality.

## Candidate Fields

Each repair candidate should include:

```text
repair_branch_id
repair_candidate_id
repair_source_family
repair_source_kind
parent_candidate_source_id
parent_task_source_id
parent_profile_name
parent_feasibility_tier_id
parent_source_role_semantics
parent_surface_variant
parent_sampled_obstacle_label
parent_outcome_bucket
parent_termination_reason

feasibility_tier_id
source_role_semantics
surface_variant
sampled_obstacle_label
source_split

speed_ref
mu
obstacle_distance_delta
obstacle_half_width_delta
post_obstacle_track_width_delta
reaction_distance_delta
recovery_corridor_profile
offtrack_repair_mode

labels_enter_actor_input=false
v2_ranking_admissible_by_default=false
profile_specific_tuning=false
controller_family_ranking_claim_made=false
paper_level_claim_made=false
level3_self_id_claim_made=false
```

The template generator may use M1942 outcome labels as artifact metadata, but
none of these labels may enter actor observations.

## Pre-Execution Gates

Before any reset or measured execution, the M1945 template artifact should pass:

```text
candidate_source_count == 160
anchor_neighborhood_count == 64
success_stabilizer_count == 48
offtrack_boundary_relief_count == 32
mitigation_isolation_check_count == 16
public_debug_count == 96
public_gate_count == 64
paper_holdout_candidate_count == 0
profile_specific_tuning_count == 0
labels_enter_actor_input_count == 0
v2_ranking_admissible_by_default_count == 0
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

Then later source-mining/materialization should prove:

```text
sampling_failure_count == 0
positive support exists outside tier E
candidate-support slices increase beyond M1942's 2
comparison-ready candidate slices become nonzero before ranking is admitted
offtrack outcome rate falls below 0.70 in at least one public-gate scenario
collision rate remains below 0.30 in candidate comparison slices
```

If the first repair wave still has zero comparison-ready candidates, the next
step should be a result audit and possibly a broader scenario redesign, not
profile tuning.

## Claim Boundary

M1944 supports only:

```text
a pre-registered off-track support repair route is defined.
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
m1945-executable-v2-task-quality-offtrack-support-repair-template-implementation
```

M1945 should implement the no-rollout repair template generator, focused
tests, and a config artifact. It must not run reset, rollout, measured
execution, training, replay, PPO, profile tuning, ranking, paper-level claims,
or level3 self-ID tests.
