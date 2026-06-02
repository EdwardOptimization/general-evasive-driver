# M2400 Paper-Route Current-Sim Dual-Axis Effective Candidate Measured Outcome Localization Result Audit

- status: completed
- decision: `effective_candidate_measured_outcome_localization_accepted_route_to_actionable_target_consolidation`
- manifest: `experiments/manifests/m2400-paper-route-current-sim-dual-axis-effective-candidate-measured-outcome-localization-result-audit.json`
- parent implementation: `docs/m2399-paper-route-current-sim-dual-axis-effective-candidate-measured-outcome-localization-implementation.md`
- parent summary: `runs/m2399_paper_route_current_sim_dual_axis_effective_candidate_measured_outcome_localization/summary.json`
- rerun/new rollout in M2400: `false`
- repair execution/training/replay/PPO: `false`
- support-policy/controller-family/effective-candidate ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2400 accepts M2399 as a complete artifact-only localization pass.

Accepted evidence:

```text
result_class: current_sim_dual_axis_effective_candidate_measured_outcome_localization_pass
source_episode_count: 30735
target_episode_count: 30735
source_candidate_count: 54
source_profile_count: 5
source_role_family_count: 6
slice_row_count: 1313
offtrack_target_slice_count: 1132
collision_guardrail_slice_count: 364
r4_mitigation_semantics_slice_count: 57
diagnostic_only_slice_count: 96
high_priority_offtrack_slice_count: 658
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Observed route classes:

```text
offtrack_target: 796
offtrack_target_with_collision_guardrail: 336
collision_guardrail: 28
r4_mitigation_semantics: 57
diagnostic_only: 96
```

M2400 rejects two shortcuts:

```text
do not treat raw slice priority as a ranking
do not execute repair directly from 1313 raw slices
```

The localization is actionable enough to continue, but it is too broad for
direct repair. It needs consolidation into bounded target and guardrail
categories.

## Actionability Decision

The next actionable categories are:

```text
offtrack targets:
  global offtrack dominance
  centerline offtrack
  early_far offtrack
  drift_required offtrack plus collision
  guarded_offtrack_containment_repair offtrack plus collision

collision guardrails:
  drift_required
  guarded_offtrack_containment_repair
  late_close
  right_offset
  guarded R2 handling-limit slices

R4 mitigation semantics:
  R4_unavoidable_mitigation is collision-dominated
  unavoidable obstacle label is collision-dominated
  guarded R4 slices are especially collision-heavy

diagnostic only:
  candidate/profile aggregates remain non-ranking diagnostics
```

The categories are separable enough to support target consolidation. The route
should not be a repair implementation yet; it should first consolidate
overlapping slices into a compact, auditable target table.

## Failure Taxonomy

Observed:

```text
driver_outcome_failure: offtrack_dominated_failure
target_surface_too_broad_for_direct_repair: 1313 raw slices
collision_guardrail_signal: 364 collision guardrail slices
R4_mitigation_semantics_signal: 57 R4 semantics slices
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
M2399 localization is complete and separates offtrack, collision guardrail, R4
mitigation semantics, and diagnostic-only categories.

M2400 routes to artifact-only actionable target consolidation.
```

Blocked:

```text
effective-candidate ranking
controller-family ranking
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
effective_candidate_measured_outcome_localization_accepted_route_to_actionable_target_consolidation
```

Next milestone:

```text
m2401-paper-route-current-sim-dual-axis-effective-candidate-actionable-target-consolidation-implementation
```

M2401 should consolidate M2399 slice rows into compact target and guardrail
tables. It must be artifact-only: no rerun, repair execution, training, ranking,
winner selection, or paper/self-ID/current-sim verdict claim.
