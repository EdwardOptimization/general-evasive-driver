# M1920 Executable V2 Task-Quality Scenario Redesign Source-Mining Design

- status: completed
- decision: `task_quality_scenario_source_mining_design_admit_template_implementation`
- branch: `paper_route_task_quality_scenario_redesign`
- parent plan: `docs/m1919-executable-v2-task-quality-scenario-redesign-plan.md`
- existing helper reviewed: `src/autodrift/executable_v2_support_first_source_mining.py`
- reset/rollout/measured execution in M1920: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M1920 turns the M1919 feasibility ladder into an executable source-mining
schema. The next artifact should not be another fixed-source repair matrix. It
should be a fresh candidate-source template set that can be scanned for
positive support, boundary near-misses, and mitigation-only rows before any
controller comparison.

## Source-Mining Schema

Each candidate source row should include the existing support-first fields plus
new scenario-quality fields.

Existing compatibility fields:

```text
candidate_source_id
source_v1_bounded_panel_spec_id
source_scenario_spec_id
source_role_semantics
source_required_label
source_allowed_labels
profile_name
profile_group
speed_ref
mu
surface_variant
source_family_id
friction_step_enabled
friction_step_at
dt
min_time_after_friction_step
obstacle_distance_min / max / count
obstacle_half_width_min / max / count
min_accepted_cells
labels_enter_actor_input=false
v2_ranking_admissible_by_default=false
```

New scenario-quality fields:

```text
scenario_quality_branch_id
feasibility_tier_id
source_split
target_support_mode
target_boundary_mode
road_corridor_profile
pre_obstacle_track_width
post_obstacle_track_width
obstacle_lateral_profile
reaction_distance_profile
expected_joint_support
expected_near_miss_support
mitigation_only
positive_support_gate_required
paper_holdout_candidate
```

No source-mining label or tier field may enter deployable actor input. These
fields are artifact metadata only.

## First-Wave Template Grid

The first candidate-template wave should be large enough to break the fixed
16-source loop while still being cheap to scan without rollout:

```text
feasibility tiers: 5
roles: 4
surfaces: 2
speed buckets: 4
mu buckets: 4
target candidate rows: 640
```

Recommended buckets:

```text
tiers:
  tier_a_positive_support_sanity
  tier_b_feasible_emergency
  tier_c_boundary_near_miss
  tier_d_handling_limit_drift_required
  tier_e_mitigation_only

roles:
  stable_aeb
  stable_aes_only
  drift_required_recovery
  unavoidable_mitigation

surfaces:
  steady_surface
  post_friction_step

speed buckets:
  12, 18, 24, 30 m/s

mu buckets:
  0.25, 0.40, 0.60, 0.80
```

The exact obstacle distance and width ranges should be tier-specific. Tier A/B
must be easier than M1902/M1915 so the system can verify positive support. Tier
C/D should target the M1917 near-miss boundary. Tier E should remain
mitigation-only and must not be mixed into success ranking.

## Split Policy

Every candidate must declare:

```text
source_split in {public_debug, public_gate, paper_holdout_candidate}
```

First wave default:

```text
public_debug: 60%
public_gate: 30%
paper_holdout_candidate: 10%
```

The holdout candidates are metadata only in the first wave. They must not be
used for repair or tuning. If any holdout candidate is used to fix a bug or
tune thresholds, it must be rotated out before a paper comparison.

## Acceptance Gates

M1920 defines two gate levels.

Template-generation gate:

```text
candidate_row_count == 640
feasibility_tier_count == 5
role_count == 4
surface_count == 2
speed_bucket_count == 4
mu_bucket_count == 4
labels_enter_actor_input_count == 0
ranking_admissible_by_default_count == 0
positive_support_gate_required_count > 0
paper_holdout_candidate_count > 0
guardrail_violation_count == 0
```

Source-mining execution gate, for the later scan milestone:

```text
sampling / grid scan completes without reset, rollout, or policy action
supported_source_count > 0
Tier A joint-support candidates exist
Tier B joint-support candidates exist
Tier C or D near-miss candidates exist
Tier E mitigation-only candidates are isolated
max single tier/role/source-family share is bounded
labels_enter_actor_input_count == 0
v2_ranking_admissible_by_default_count == 0
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If source mining produces zero positive-support candidates in Tier A/B, the
branch should adjust source templates once. If a second wave still has zero
positive support, synthesize rather than opening a local search loop.

## Next

Next milestone:

```text
m1921-executable-v2-task-quality-scenario-redesign-template-implementation
```

M1921 should implement the deterministic candidate-template generator and
focused tests. It should not run source mining, reset, rollout, measured
execution, training, replay, PPO, controller ranking, paper-level claims, or
level3 self-ID claims.
