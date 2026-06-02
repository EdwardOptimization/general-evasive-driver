# M2415 Paper-Route Current-Sim Dual-Axis Source-Linked Offtrack Containment Measured Outcome Localization Implementation

- status: completed
- result_class: `current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization_pass`
- manifest: `experiments/manifests/m2415-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-outcome-localization-implementation.json`
- parent audit: `docs/m2414-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-result-audit.md`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization.py`
- focused tests: `4 passed`
- summary: `runs/m2415_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization/summary.json`
- source measured panel: `runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation`
- rerun/new rollout in M2415: `false`
- repair execution/training/replay/PPO: `false`
- family/profile/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Implementation Result

M2415 materialized artifact-only localization slices from the complete M2413
measured panel.

Summary:

```text
result_class: current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization_pass
source_episode_count: 5250
source_family_membership_row_count: 18300
source_reset_target_count: 350
source_family_id_count: 4
source_profile_count: 5
source_role_family_count: 6
slice_row_count: 2844
episode_slice_row_count: 2734
family_membership_slice_row_count: 110
offtrack_target_slice_count: 272
collision_guardrail_slice_count: 114
r4_mitigation_semantics_slice_count: 49
max_step_noncompletion_slice_count: 325
speed_too_low_slice_count: 124
diagnostic_only_slice_count: 2504
high_priority_offtrack_slice_count: 113
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Route-class counts:

```text
collision_guardrail: 19
diagnostic_only: 2504
offtrack_target: 177
offtrack_target_with_collision_guardrail: 95
r4_mitigation_semantics: 49
```

Slice source-table counts:

```text
episode_rows: 2734
episode_family_membership_rows: 110
```

The two source tables are intentionally kept separate. Primary episode rows
use the real 5250-episode denominator; family-membership rows are overlapping
diagnostics and must not be used as a mutually exclusive ranking denominator.

## Slice Axes

Primary episode axes include:

```text
global
reset_target_key
pack_id
profile_name
role_family
scenario_family_id
sampled_obstacle_label
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
outcome_bucket
reset_target_key+profile_name
reset_target_key+role_family
profile_name+role_family
role_family+hidden_dynamics_bucket
role_family+obstacle_longitudinal_timing_bucket
role_family+obstacle_lateral_offset_bucket
pack_id+profile_name+role_family
```

Family-membership axes include:

```text
family_id
family_id+profile_name
family_id+pack_id
family_id+role_family
family_id+hidden_dynamics_bucket
family_id+sampled_obstacle_label
```

## Top Localized Slices

Top offtrack target slices:

```text
episode_rows/global=all
  episodes: 5250
  offtrack_rate: 0.7424761904761905
  collision_rate: 0.1761904761904762
  route: offtrack_target_with_collision_guardrail

episode_family_membership_rows/family_id=c03_general_offtrack_boundary_containment
  episodes: 5250
  offtrack_rate: 0.7424761904761905
  collision_rate: 0.1761904761904762
  route: offtrack_target_with_collision_guardrail

episode_rows/outcome_bucket=off_track_noncollision_noncompletion
  episodes: 3898
  offtrack_rate: 1.0
  collision_rate: 0.0
  route: offtrack_target

episode_family_membership_rows/family_id=c01_geometry_timing_containment
  episodes: 4350
  offtrack_rate: 0.7583908045977011
  collision_rate: 0.16114942528735632
  route: offtrack_target_with_collision_guardrail

episode_family_membership_rows/family_id=c04_role_conditioned_containment
  episodes: 4500
  offtrack_rate: 0.8162222222222222
  collision_rate: 0.08933333333333333
  route: offtrack_target
```

Top collision guardrail slices:

```text
episode_rows/global=all
  episodes: 5250
  collision_rate: 0.1761904761904762
  offtrack_rate: 0.7424761904761905
  route: offtrack_target_with_collision_guardrail

episode_family_membership_rows/family_id=c03_general_offtrack_boundary_containment
  episodes: 5250
  collision_rate: 0.1761904761904762
  offtrack_rate: 0.7424761904761905
  route: offtrack_target_with_collision_guardrail

episode_family_membership_rows/family_id=c01_geometry_timing_containment
  episodes: 4350
  collision_rate: 0.16114942528735632
  offtrack_rate: 0.7583908045977011
  route: offtrack_target_with_collision_guardrail

episode_rows/obstacle_lateral_offset_bucket=centerline
  episodes: 2700
  collision_rate: 0.16407407407407407
  offtrack_rate: 0.7562962962962962
  route: offtrack_target_with_collision_guardrail

episode_rows/sampled_obstacle_label=drift_required
  episodes: 2025
  collision_rate: 0.1945679012345679
  offtrack_rate: 0.7881481481481482
  route: offtrack_target_with_collision_guardrail
```

The localization also emits separate max-step and speed-too-low slice tables.
These are diagnostics for audit and target consolidation; they are not new
training claims.

## Claim Boundary

Supported:

```text
M2415 generated artifact-only localization slices from M2413 rows and separated
primary episode rows from overlapping family-membership diagnostics.
```

Blocked:

```text
candidate family ranking
support/profile/controller ranking
winner selection
repair execution
scenario redesign executed
training repair success
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

## Route Decision

Decision:

```text
source_linked_measured_outcome_localization_pass_route_to_result_audit
```

Next milestone:

```text
m2416-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-outcome-localization-result-audit
```

M2416 should audit whether M2415 localization is actionable enough for target
consolidation, branch synthesis, stop, or pivot. It must not rerun measured
validation, execute repair, train, rank families/profiles/controllers, select a
winner, or make paper/self-ID/current-sim verdict claims.

## Failure Taxonomy

Observed:

```text
behavior_regression: source outcome remains offtrack-dominated
```

Not observed:

```text
scenario_sampling_failure
lineage_invalid
contract_violation
metric_artifact
objective_overfit
repair execution
training repair success
candidate/profile/controller ranking
winner selection
```
