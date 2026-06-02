# M2428 Paper-Route Current-Sim Dual-Axis Source-Linked Repair-Candidate Measured Reindex Implementation

- status: completed
- result_class: `current_sim_dual_axis_source_linked_repair_candidate_measured_reindex_pass`
- manifest: `experiments/manifests/m2428-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_source_linked_repair_candidate_measured_reindex.py`
- focused tests: `2 passed`
- summary: `runs/m2428_paper_route_current_sim_dual_axis_source_linked_repair_candidate_measured_reindex/summary.json`
- source measured panel: `runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_rows.csv`
- source reset panel: `runs/m2426_paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence`
- reset rerun / measured rollout rerun / repair / training / ranking: `false / false / false / false / false`

## Result

M2428 reindexed the existing M2413 measured episodes by the M2426 matched
source-linked repair-candidate memberships. It did not rerun reset or measured
rollout.

```text
source_episode_count: 5250
selected_checkpoint_count: 15
source_reset_target_count: 350
source_measured_reset_target_count: 350
exact_reset_key_coverage: true
reindexed_membership_row_count: 13050
reindexed_reset_target_count: 350
matched_candidate_family_count: 3
expected_matched_candidate_family_count: 3
excluded_candidate_count: 1
c04_included_as_measured: false
aggregate_by_candidate_row_count: 3
aggregate_by_candidate_profile_row_count: 15
aggregate_by_candidate_pack_row_count: 15
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
failure_types_observed: []
```

Membership denominator:

```text
c01_source_linked_geometry_timing_containment: 4350 rows, 290 reset targets
c02_source_linked_hidden_dynamics_response_containment: 4200 rows, 280 reset targets
c03_source_linked_role_conditioned_containment: 4500 rows, 300 reset targets
```

c04 remains excluded:

```text
c04_source_linked_outcome_failure_surface_containment:
  matched_effective_candidate_count: 0
  source_linked_scenario_reference_count: 0
  unique_reset_target_count: 0
  c04_included_as_measured: false
```

## Reindexed Outcome Aggregates

The matched candidate-family slices remain offtrack-dominated:

```text
c01_source_linked_geometry_timing_containment:
  episode_count: 4350
  success_rate: 0.06689655172413793
  collision_rate: 0.16114942528735632
  offtrack_rate: 0.7583908045977011
  dominant_failure_mode: offtrack_dominated_failure

c02_source_linked_hidden_dynamics_response_containment:
  episode_count: 4200
  success_rate: 0.06
  collision_rate: 0.09547619047619048
  offtrack_rate: 0.8269047619047619
  dominant_failure_mode: offtrack_dominated_failure

c03_source_linked_role_conditioned_containment:
  episode_count: 4500
  success_rate: 0.078
  collision_rate: 0.08933333333333333
  offtrack_rate: 0.8162222222222222
  dominant_failure_mode: offtrack_dominated_failure
```

These are diagnostic aggregates, not rankings.

## Interpretation

Supported:

```text
The existing M2413 measured panel can be reindexed cleanly by the M2426 matched
c01/c02/c03 repair-candidate memberships.

The reindexed matched subset remains offtrack-dominated.

c04 is correctly excluded from measured aggregates because it has zero matched
effective candidates in M2426.
```

Blocked:

```text
all-four-family measured result
c04 outcome-failure-surface measured result
scenario repair success
driver improvement
candidate-family ranking
winner selection
paper-level result
finite-window-vs-GRU result
level3 self-identification
current-sim verdict
```

## Next

Follow-up manifest:

```text
experiments/manifests/m2429-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-result-audit.json
```

M2429 should audit whether the reindexed offtrack-dominated result should route
to:

```text
1. branch synthesis / scenario-quality decision;
2. source-coverage repair for c04 outcome_bucket;
3. bounded scenario-quality reassessment;
4. a stop before more artifact-only local search.
```

It should not route directly to training, repair execution, candidate ranking,
or current-sim/paper/self-ID verdict claims.
