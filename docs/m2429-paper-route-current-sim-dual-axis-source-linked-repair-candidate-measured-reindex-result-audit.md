# M2429 Paper-Route Current-Sim Dual-Axis Source-Linked Repair-Candidate Measured Reindex Result Audit

- status: completed
- decision: `measured_reindex_offtrack_dominated_route_to_branch_synthesis`
- manifest: `experiments/manifests/m2429-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-result-audit.json`
- parent implementation: `docs/m2428-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-implementation.md`
- parent summary: `runs/m2428_paper_route_current_sim_dual_axis_source_linked_repair_candidate_measured_reindex/summary.json`
- rerun/reset/rollout/repair/training/replay/PPO: `false`
- candidate/support/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2429 accepts M2428 as a complete measured-result reindex artifact. It also
classifies the result as negative for matched-subset task-quality improvement:
all three matched source-linked repair-candidate slices remain
offtrack-dominated.

Accepted artifact evidence:

```text
result_class: current_sim_dual_axis_source_linked_repair_candidate_measured_reindex_pass
source_episode_count: 5250
selected_checkpoint_count: 15
source_reset_target_count: 350
source_measured_reset_target_count: 350
exact_reset_key_coverage: true
reindexed_membership_row_count: 13050
matched_candidate_family_count: 3
expected_matched_candidate_family_count: 3
excluded_candidate_count: 1
c04_included_as_measured: false
aggregate_by_candidate_row_count: 3
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
failure_types_observed: []
```

Measured reindex outcome:

```text
c01_source_linked_geometry_timing_containment:
  success_rate: 0.06689655172413793
  collision_rate: 0.16114942528735632
  offtrack_rate: 0.7583908045977011
  dominant_failure_mode: offtrack_dominated_failure

c02_source_linked_hidden_dynamics_response_containment:
  success_rate: 0.06
  collision_rate: 0.09547619047619048
  offtrack_rate: 0.8269047619047619
  dominant_failure_mode: offtrack_dominated_failure

c03_source_linked_role_conditioned_containment:
  success_rate: 0.078
  collision_rate: 0.08933333333333333
  offtrack_rate: 0.8162222222222222
  dominant_failure_mode: offtrack_dominated_failure
```

## Diagnosis

M2428 successfully avoided a duplicate rollout by reusing M2413. That was the
right move because M2426 and M2413 share the exact 350 reset-target denominator.

But the reindexed evidence does not support continuing directly to training,
repair execution, or candidate-family comparison:

```text
matched subset still offtrack-dominated
c04 outcome-failure-surface candidate has no measured coverage
all aggregates are diagnostic-only
no current-sim verdict is supported
```

This is now a route-decision problem, not another adapter/reindex problem.

## Failure Taxonomy

Observed:

```text
driver_outcome_failure:
  c01/c02/c03 matched slices remain offtrack-dominated.

source_coverage_gap:
  c04 outcome-failure-surface containment remains excluded because M2426 has
  zero matched effective candidates.

local_search_guard:
  another artifact-only reindex/audit would not add driver evidence.
```

Not observed:

```text
lineage_invalid
contract_violation
metric_artifact in M2428
scenario_sampling_failure in M2428
active config overwrite
repair execution
training repair success
candidate/profile/controller ranking
winner selection
```

## Route Decision

Decision:

```text
measured_reindex_offtrack_dominated_route_to_branch_synthesis
```

Next milestone:

```text
m2430-paper-route-current-sim-dual-axis-source-linked-repair-candidate-branch-synthesis
```

M2430 should synthesize M2425-M2429 and decide the next route. The admissible
options are:

```text
1. scenario-quality reassessment:
   if current-sim offtrack semantics are the dominant blocker;

2. c04 source-coverage repair:
   if outcome-failure-surface coverage is required before any paper route;

3. bounded matched-subset measured follow-up:
   only if it adds evidence beyond M2428 and keeps c04 excluded;

4. stop current-sim local repair and pivot toward high-fidelity backend design:
   if this branch has exhausted useful current-sim evidence;

5. stop for user review:
   if no bounded evidence-producing route is supported.
```

M2430 must not treat M2428 as a repaired driver result or candidate-family
ranking.

## Claim Boundary

Supported:

```text
M2428 is accepted as a complete non-ranking measured-result reindex.

The matched source-linked repair-candidate subset remains offtrack-dominated.

The next admissible step is branch synthesis/route decision, not another
ordinary local artifact step.
```

Blocked:

```text
driver improvement
scenario repair success
all-four-family measured result
c04 outcome-failure-surface measured result
candidate family ranking
support/controller ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```
