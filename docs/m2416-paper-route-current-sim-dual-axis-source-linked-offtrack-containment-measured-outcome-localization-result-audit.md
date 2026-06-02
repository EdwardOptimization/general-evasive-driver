# M2416 Paper-Route Current-Sim Dual-Axis Source-Linked Offtrack Containment Measured Outcome Localization Result Audit

- status: completed
- decision: `source_linked_measured_outcome_localization_accepted_route_to_target_consolidation`
- manifest: `experiments/manifests/m2416-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-outcome-localization-result-audit.json`
- parent implementation: `docs/m2415-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-outcome-localization-implementation.md`
- parent summary: `runs/m2415_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization/summary.json`
- rerun/localization rerun/repair/training/replay/PPO: `false`
- family/profile/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2416 accepts M2415 as a complete artifact-only localization pass.

Accepted evidence:

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

Observed route classes:

```text
offtrack_target: 177
offtrack_target_with_collision_guardrail: 95
collision_guardrail: 19
r4_mitigation_semantics: 49
diagnostic_only: 2504
```

M2416 rejects two shortcuts:

```text
do not treat raw slice priority as a ranking
do not execute repair directly from 2844 raw slices
```

The localization is actionable enough to continue, but it is too broad for
direct repair. It needs consolidation into compact target and guardrail
categories.

## Actionability Decision

The next actionable categories are:

```text
offtrack targets:
  global/source-linked offtrack dominance
  c03 general offtrack boundary membership
  off_track outcome bucket
  c01 geometry/timing membership with collision guardrail
  c04 role-conditioned membership offtrack
  centerline and drift_required slices

collision guardrails:
  global/source-linked collision mass
  c03 and c01 membership collision guardrails
  centerline collision guardrail
  drift_required collision guardrail

R4 mitigation semantics:
  R4_unavoidable_mitigation
  scenario_family_id R4
  sampled_obstacle_label unavoidable

max-step and speed-too-low diagnostics:
  preserve separate max-step and speed-too-low slice tables
  do not merge them into offtrack repair targets

diagnostic only:
  reset_target/profile/family slices remain non-ranking diagnostics
```

These categories are separable enough to support target consolidation. The
route should not be a repair implementation yet; it should first consolidate
overlapping slices into compact, auditable target tables.

## Failure Taxonomy

Observed:

```text
behavior_regression: source measured outcome remains offtrack-dominated
target_surface_too_broad_for_direct_repair: 2844 raw slices
collision_guardrail_signal: 114 collision guardrail slices
R4_mitigation_semantics_signal: 49 R4 semantics slices
max_step_signal: 325 max-step slices
speed_too_low_signal: 124 speed-too-low slices
```

Not observed:

```text
metric_artifact
lineage_invalid
contract_violation
scenario_sampling_failure at artifact-construction level
ranking or winner selection
```

## Claim Boundary

Supported:

```text
M2415 localization is complete and separates offtrack, collision guardrail, R4
mitigation semantics, max-step, speed-too-low, and diagnostic-only categories.

M2416 routes to artifact-only actionable target consolidation.
```

Blocked:

```text
candidate family ranking
support/profile/controller ranking
winner selection
repair execution
training repair success
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
current-sim verdict
```

## Route Decision

Decision:

```text
source_linked_measured_outcome_localization_accepted_route_to_target_consolidation
```

Next milestone:

```text
m2417-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-actionable-target-consolidation-implementation
```

M2417 should consolidate M2415 slice rows into compact target and guardrail
tables. It must be artifact-only: no rerun, repair execution, training, ranking,
winner selection, or paper/self-ID/current-sim verdict claim.
